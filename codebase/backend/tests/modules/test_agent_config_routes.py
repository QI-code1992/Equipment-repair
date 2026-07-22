from fastapi.testclient import TestClient
from sqlalchemy import select

from app.modules.agent_config.models import AgentConfigModel
from app.modules.audit.models import AuditEvent, IdempotencyRecord
from tests.modules.support import create_user_token


def headers(token: str, key: str | None = None) -> dict[str, str]:
    result = {"Authorization": f"Bearer {token}"}
    if key is not None:
        result["Idempotency-Key"] = key
    return result


def agent_body(agent_id: str, *, model_binding_id: str | None = None) -> dict[str, object]:
    return {
        "agent_id": agent_id,
        "enabled": model_binding_id is not None,
        "model_binding_id": model_binding_id,
        "knowledge_dataset_ids": ["knowledge-a"],
        "streaming_enabled": True,
        "suggestions_enabled": True,
        "sources_enabled": True,
        "context_turns": 3,
        "retrieval_limit": 6,
        "similarity_threshold": 0.62,
        "deep_thinking_enabled": False,
        "deep_thinking_level": "medium",
        "max_reply_tokens": 4096,
    }


def test_formal_agent_configuration_routes_require_authentication(
    client: TestClient,
) -> None:
    assert client.get("/api/model-providers").status_code == 401
    assert client.get("/api/model-bindings").status_code == 401
    assert client.get("/api/agent-configs/fault_reporting").status_code == 401


def test_model_provider_write_hides_secret_from_response_audit_and_replay(
    client: TestClient,
) -> None:
    actor_id, token = create_user_token(
        client,
        username="model-admin",
        role_code="EQUIPMENT_ADMIN",
        permission_codes=["intelligence:model"],
    )
    payload = {
        "name": "OpenAI compatible",
        "secret_ref": "vault://models/production",
        "enabled": True,
    }
    request_headers = headers(token, "provider-create-1")

    created = client.post("/api/model-providers", headers=request_headers, json=payload)
    replay = client.post("/api/model-providers", headers=request_headers, json=payload)

    assert created.status_code == replay.status_code == 201
    assert created.json() == replay.json()
    assert "secret_ref" not in created.json()
    assert payload["secret_ref"] not in str(created.json())
    with client.app.state.session_factory() as db:
        events = db.scalars(
            select(AuditEvent).where(AuditEvent.action == "model_provider.create")
        ).all()
        record = db.scalar(
            select(IdempotencyRecord).where(
                IdempotencyRecord.user_id == actor_id,
                IdempotencyRecord.idempotency_key == "provider-create-1",
            )
        )
    assert len(events) == 1
    assert payload["secret_ref"] not in str(events[0].metadata_json)
    assert record is not None
    assert payload["secret_ref"] not in str(record.response_body)


def test_model_and_agent_permissions_are_separate(client: TestClient) -> None:
    _, model_token = create_user_token(
        client,
        username="models-only",
        role_code="EQUIPMENT_ADMIN",
        permission_codes=["intelligence:model"],
    )
    _, agent_token = create_user_token(
        client,
        username="agents-only",
        role_code="REPAIR_WORKER",
        permission_codes=["intelligence:agent"],
    )

    model_denied = client.put(
        "/api/agent-configs/fault_reporting",
        headers=headers(model_token, "agent-denied"),
        json=agent_body("fault_reporting"),
    )
    agent_denied = client.post(
        "/api/model-providers",
        headers=headers(agent_token, "provider-denied"),
        json={"name": "forbidden", "secret_ref": "vault://forbidden", "enabled": True},
    )
    model_read_denied = client.get(
        "/api/agent-configs", headers=headers(model_token)
    )
    agent_read_denied = client.get(
        "/api/model-providers", headers=headers(agent_token)
    )

    assert model_denied.status_code == agent_denied.status_code == 403
    assert model_read_denied.status_code == agent_read_denied.status_code == 403
    assert model_denied.json()["detail"]["code"] == "PERMISSION_DENIED"
    assert agent_denied.json()["detail"]["code"] == "PERMISSION_DENIED"


def test_agent_get_initializes_only_requested_agent_and_put_persists(
    client: TestClient,
) -> None:
    _, token = create_user_token(
        client,
        username="agent-admin",
        role_code="REPAIR_WORKER",
        permission_codes=["intelligence:agent"],
    )

    fetched = client.get(
        "/api/agent-configs/fault_reporting", headers=headers(token)
    )
    saved = client.put(
        "/api/agent-configs/fault_reporting",
        headers=headers(token, "agent-save-1"),
        json=agent_body("fault_reporting"),
    )
    listed = client.get("/api/agent-configs", headers=headers(token))

    assert fetched.status_code == saved.status_code == listed.status_code == 200
    assert fetched.json()["agent_id"] == "fault_reporting"
    assert saved.json()["knowledge_dataset_ids"] == ["knowledge-a"]
    assert "audit_event_id" in saved.json()
    assert [item["agent_id"] for item in listed.json()] == ["fault_reporting"]
    with client.app.state.session_factory() as db:
        assert db.scalars(select(AgentConfigModel.agent_id)).all() == ["fault_reporting"]


def test_agent_config_rejects_path_and_body_identity_mismatch(client: TestClient) -> None:
    _, token = create_user_token(
        client,
        username="agent-mismatch",
        role_code="LINE_OPERATOR",
        permission_codes=["intelligence:agent"],
    )

    response = client.put(
        "/api/agent-configs/fault_reporting",
        headers=headers(token, "agent-mismatch-1"),
        json=agent_body("metric_query"),
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "AGENT_CONFIG_INVALID"
    assert response.json()["detail"]["fields"]["agent_id"] == "invalid"


def test_model_catalog_crud_reads_are_protected_and_secret_free(
    client: TestClient,
) -> None:
    _, token = create_user_token(
        client,
        username="catalog-admin",
        role_code="EQUIPMENT_ADMIN",
        permission_codes=["intelligence:model"],
    )
    provider = client.post(
        "/api/model-providers",
        headers=headers(token, "catalog-provider"),
        json={"name": "catalog-provider", "secret_ref": "vault://catalog", "enabled": True},
    )
    provider_id = provider.json()["id"]
    provider_update = client.put(
        f"/api/model-providers/{provider_id}",
        headers=headers(token, "catalog-provider-update"),
        json={"name": "catalog-provider-v2", "secret_ref": "vault://catalog-v2", "enabled": True},
    )
    binding = client.post(
        "/api/model-bindings",
        headers=headers(token, "catalog-binding"),
        json={
            "provider_id": provider_id,
            "name": "catalog-binding",
            "model_name": "gpt-test",
            "supports_reasoning": True,
            "enabled": True,
        },
    )
    updated = client.put(
        f"/api/model-bindings/{binding.json()['id']}",
        headers=headers(token, "catalog-binding-update"),
        json={
            "provider_id": provider_id,
            "name": "catalog-binding",
            "model_name": "gpt-test-v2",
            "supports_reasoning": True,
            "enabled": True,
        },
    )
    providers = client.get("/api/model-providers", headers=headers(token))
    bindings = client.get("/api/model-bindings", headers=headers(token))

    assert provider.status_code == binding.status_code == 201
    assert provider_update.status_code == 200
    assert "secret_ref" not in provider_update.json()
    assert updated.status_code == providers.status_code == bindings.status_code == 200
    assert all("secret_ref" not in item for item in providers.json())
    assert bindings.json()[0]["model_name"] == "gpt-test-v2"
