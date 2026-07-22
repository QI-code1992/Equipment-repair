from sqlalchemy import select

from app.modules.agent_config.models import AgentConfigModel, ModelBinding, ModelProvider
from app.modules.agent_runtime.models import AgentRun, AgentThread
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
        headers=auth(token),
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
        headers=auth(owner_token),
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
        headers=auth(owner_token),
        json={"confirmation": {"approved": True}},
    )
    assert resumed.status_code == 202
    with client.app.state.session_factory() as db:
        stored = db.get(AgentThread, thread["thread_id"])
        assert stored is not None and stored.checkpoint_ref == run["run_id"]
        assert db.scalar(select(AgentRun).where(AgentRun.id == run["run_id"])).status == "RESUMED"
