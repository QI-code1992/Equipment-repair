from sqlalchemy import select

from app.modules.agent_config.models import AgentConfigModel, ModelBinding, ModelProvider
from app.modules.agent_runtime.models import AgentConfirmation, AgentRun, AgentThread
from app.modules.audit.models import AuditEvent, IdempotencyRecord
from app.modules.agent_runtime.tool_audit import ALLOWED_TOOLS, record_tool_call
from app.modules.agent_runtime.langgraph_runtime import normalize_checkpoint_url, run_checkpoint
from tests.modules.support import create_user_token


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def enabled_config(client, agent_id: str = "fault_reporting") -> None:
    with client.app.state.session_factory() as db:
        provider = ModelProvider(name=f"provider-{agent_id}", secret_ref="vault://secret")
        db.add(provider)
        db.flush()
        binding = ModelBinding(
            provider_id=provider.id,
            name=f"binding-{agent_id}",
            model_name="chat-model",
            supports_reasoning=True,
        )
        db.add(binding)
        db.flush()
        db.add(
            AgentConfigModel(
                agent_id=agent_id,
                enabled=True,
                model_binding_id=binding.id,
                knowledge_dataset_ids=[],
                streaming_enabled=True,
                suggestions_enabled=True,
                sources_enabled=True,
                context_turns=3,
                retrieval_limit=6,
                similarity_threshold=0.62,
                deep_thinking_enabled=True,
                deep_thinking_level="high",
                max_reply_tokens=4096,
            )
        )
        db.commit()


def test_thread_message_persists_snapshot_and_sse_hides_input(client) -> None:
    _, token = create_user_token(
        client,
        username="runtime-owner",
        role_code="REPAIR_WORKER",
        permission_codes=["intelligence:agent"],
    )
    enabled_config(client)
    created = client.post(
        "/api/agent/threads",
        headers={**auth(token), "Idempotency-Key": "thread-1"},
        json={"agent_id": "fault_reporting", "business_context": {"fault_id": "f-1"}},
    )
    assert created.status_code == 201
    thread_id = created.json()["thread_id"]
    run_response = client.post(
        f"/api/agent/threads/{thread_id}/messages",
        headers={**auth(token), "Idempotency-Key": "runtime-1"},
        json={"text": "password=never-echo-this"},
    )
    assert run_response.status_code == 202
    run_id = run_response.json()["run_id"]
    with client.app.state.session_factory() as db:
        run = db.get(AgentRun, run_id)
        assert run is not None
        assert run.config_snapshot_json["deep_thinking_level"] == "high"
        assert "secret" not in str(run.config_snapshot_json).lower()
        assert "password" not in str(run.state_json).lower()
    events = client.get(f"/api/agent/runs/{run_id}/events", headers=auth(token))
    assert events.status_code == 200
    assert "event: run_started" in events.text
    assert "never-echo-this" not in events.text
    assert "reasoning_status" in events.text


def test_atomic_thread_start_does_not_leave_a_thread_when_config_is_invalid(client) -> None:
    _, token = create_user_token(
        client, username="runtime-atomic-invalid", role_code="REPAIR_WORKER", permission_codes=["intelligence:agent"]
    )
    response = client.post(
        "/api/agent/threads/start",
        headers={**auth(token), "Idempotency-Key": "atomic-invalid"},
        json={"agent_id": "fault_reporting", "business_context": {}, "text": "describe the fault"},
    )
    assert response.status_code == 503
    with client.app.state.session_factory() as db:
        assert db.scalars(select(AgentThread)).all() == []


def test_atomic_thread_start_replays_one_thread_and_one_run(client) -> None:
    owner_id, token = create_user_token(
        client, username="runtime-atomic-replay", role_code="REPAIR_WORKER", permission_codes=["intelligence:agent"]
    )
    enabled_config(client)
    headers = {**auth(token), "Idempotency-Key": "atomic-replay"}
    payload = {"agent_id": "fault_reporting", "business_context": {"equipment_id": "eq-1"}, "text": "describe the fault"}
    first = client.post("/api/agent/threads/start", headers=headers, json=payload)
    replay = client.post("/api/agent/threads/start", headers=headers, json=payload)
    conflict = client.post("/api/agent/threads/start", headers=headers, json={**payload, "text": "different"})
    assert first.status_code == replay.status_code == 202
    assert first.json() == replay.json()
    assert conflict.status_code == 409
    with client.app.state.session_factory() as db:
        assert len(db.scalars(select(AgentThread)).all()) == 1
        assert len(db.scalars(select(AgentRun)).all()) == 1
        assert len(db.scalars(select(AuditEvent).where(AuditEvent.action == "agent.thread.create")).all()) == 1
        assert db.scalar(select(IdempotencyRecord).where(IdempotencyRecord.user_id == owner_id)) is not None


def test_thread_history_lists_only_current_users_threads(client) -> None:
    _, token = create_user_token(
        client,
        username="runtime-history-owner",
        role_code="REPAIR_WORKER",
        permission_codes=["intelligence:agent"],
    )
    _, other_token = create_user_token(
        client,
        username="runtime-history-other",
        role_code="REPAIR_WORKER",
        permission_codes=["intelligence:agent"],
    )
    for current_token, key in ((token, "history-1"), (other_token, "history-2")):
        response = client.post(
            "/api/agent/threads",
            headers={**auth(current_token), "Idempotency-Key": key},
            json={"agent_id": "fault_reporting", "business_context": {}},
        )
        assert response.status_code == 201

    history = client.get("/api/agent/threads", headers=auth(token))

    assert history.status_code == 200
    assert history.json()["count"] == 1
    assert set(history.json()["items"][0]) == {"thread_id", "agent_id", "status", "created_at", "updated_at"}


def test_thread_isolation_and_checkpoint_resume(client) -> None:
    _, owner_token = create_user_token(
        client,
        username="runtime-owner-2",
        role_code="REPAIR_WORKER",
        permission_codes=["intelligence:agent"],
    )
    _, other_token = create_user_token(
        client,
        username="runtime-other",
        role_code="REPAIR_WORKER",
        permission_codes=["intelligence:agent"],
    )
    enabled_config(client, "metric_query")
    thread = client.post(
        "/api/agent/threads",
        headers={**auth(owner_token), "Idempotency-Key": "thread-2"},
        json={"agent_id": "metric_query"},
    ).json()
    denied = client.get(f"/api/agent/threads/{thread['thread_id']}", headers=auth(other_token))
    assert denied.status_code == 403
    run = client.post(
        f"/api/agent/threads/{thread['thread_id']}/messages",
        headers={**auth(owner_token), "Idempotency-Key": "runtime-2"},
        json={"text": "query"},
    ).json()
    resumed = client.post(
        f"/api/agent/threads/{thread['thread_id']}/resume",
        headers={**auth(owner_token), "Idempotency-Key": "resume-1"},
        json={"confirmation": {"approved": True}},
    )
    assert resumed.status_code == 202
    replay = client.post(
        f"/api/agent/threads/{thread['thread_id']}/resume",
        headers={**auth(owner_token), "Idempotency-Key": "resume-1"},
        json={"confirmation": {"approved": True}},
    )
    conflict = client.post(
        f"/api/agent/threads/{thread['thread_id']}/resume",
        headers={**auth(owner_token), "Idempotency-Key": "resume-1"},
        json={"confirmation": {"approved": False}},
    )
    assert replay.status_code == 202 and replay.json() == resumed.json()
    assert conflict.status_code == 409
    with client.app.state.session_factory() as db:
        stored = db.get(AgentThread, thread["thread_id"])
        assert stored is not None and stored.checkpoint_ref == run["run_id"]
        assert db.scalar(select(AgentRun).where(AgentRun.id == run["run_id"])).status == "RESUMED"
        assert len(db.scalars(select(AgentConfirmation).where(AgentConfirmation.run_id == run["run_id"])).all()) == 1
        assert len(db.scalars(select(AuditEvent).where(AuditEvent.action == "agent.run.resume")).all()) == 1


def test_message_idempotency_replays_and_rejects_conflict(client) -> None:
    owner_id, token = create_user_token(
        client, username="runtime-idempotent", role_code="REPAIR_WORKER", permission_codes=["intelligence:agent"]
    )
    enabled_config(client)
    thread = client.post("/api/agent/threads", headers={**auth(token), "Idempotency-Key": "thread-3"}, json={"agent_id": "fault_reporting"}).json()
    headers = {**auth(token), "Idempotency-Key": "runtime-replay"}
    first = client.post(f"/api/agent/threads/{thread['thread_id']}/messages", headers=headers, json={"text": "one"})
    replay = client.post(f"/api/agent/threads/{thread['thread_id']}/messages", headers=headers, json={"text": "one"})
    conflict = client.post(f"/api/agent/threads/{thread['thread_id']}/messages", headers=headers, json={"text": "two"})
    assert first.status_code == replay.status_code == 202
    assert first.json() == replay.json()
    assert conflict.status_code == 409
    with client.app.state.session_factory() as db:
        assert len(db.scalars(select(AgentRun).where(AgentRun.thread_id == thread["thread_id"])).all()) == 1
        assert len(db.scalars(select(AuditEvent).where(AuditEvent.action == "agent.run.create")).all()) == 1
        assert db.scalar(select(IdempotencyRecord).where(IdempotencyRecord.user_id == owner_id)) is not None


def test_tool_audit_is_allowlisted_and_redacted(client) -> None:
    _, token = create_user_token(
        client, username="runtime-tool", role_code="REPAIR_WORKER", permission_codes=["intelligence:agent"]
    )
    enabled_config(client)
    thread = client.post("/api/agent/threads", headers={**auth(token), "Idempotency-Key": "thread-4"}, json={"agent_id": "fault_reporting"}).json()
    run = client.post(
        f"/api/agent/threads/{thread['thread_id']}/messages",
        headers={**auth(token), "Idempotency-Key": "runtime-tool-run"}, json={"text": "one"},
    ).json()
    with client.app.state.session_factory() as db:
        stored_run = db.get(AgentRun, run["run_id"])
        assert stored_run is not None
        stored_thread = db.get(AgentThread, thread["thread_id"])
        assert stored_thread is not None
        call = record_tool_call(
            db, run=stored_run, actor_user_id=stored_thread.creator_user_id,
            tool_name="query_metric_batch", input_data={"nested": {"token": "secret"}},
            result_summary={"count": 1},
        )
        db.commit()
        assert call.input_json == {"nested": {"token": "[REDACTED]"}}


def test_guidance_and_diagnosis_tools_are_allowlisted() -> None:
    assert {"get_operation_guidance", "run_fault_diagnosis"} <= ALLOWED_TOOLS


def test_resume_reads_checkpoint_history_before_merging_input() -> None:
    initial = run_checkpoint(
        run_id="checkpoint-history",
        initial_state={"step": "historical", "events": [{"event": "historical", "data": {"value": 7}}]},
        database_url="sqlite+pysqlite:///:memory:",
    )
    resumed = run_checkpoint(
        run_id="checkpoint-history",
        initial_state={"confirmation": {"approved": True}},
        database_url="sqlite+pysqlite:///:memory:",
        resumed=True,
    )
    assert any(item["event"] == "historical" for item in resumed["events"])
    assert resumed["confirmation"] == {"approved": True}
    assert resumed["step"] == "waiting_for_model"
    assert initial["step"] == "waiting_for_model"


def test_postgres_checkpoint_url_uses_libpq_format() -> None:
    assert normalize_checkpoint_url(
        "postgresql+psycopg://user:pass@postgres:5432/db"
    ) == "postgresql://user:pass@postgres:5432/db"
