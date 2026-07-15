from dataclasses import replace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.agent_config.api import create_agent_config_router
from app.modules.agent_config.domain import AgentConfig, AgentId
from app.modules.agent_config.service import AgentConfigService


def make_client(repository, model_catalog) -> TestClient:
    service = AgentConfigService(repository, model_catalog)
    app = FastAPI()
    app.include_router(create_agent_config_router(service))
    return TestClient(app)


def initialize_all(repository) -> None:
    for agent_id in AgentId:
        repository.save(AgentConfig.default_for(agent_id))


def test_list_returns_four_configs_in_stable_order(repository, model_catalog) -> None:
    initialize_all(repository)
    response = make_client(repository, model_catalog).get("/api/agent-configs")

    assert response.status_code == 200
    assert [item["agent_id"] for item in response.json()] == [
        item.value for item in AgentId
    ]


def test_get_unknown_agent_does_not_fall_back(repository, model_catalog) -> None:
    repository.save(AgentConfig.default_for(AgentId.FAULT_REPORTING))
    response = make_client(repository, model_catalog).get(
        "/api/agent-configs/shared_default"
    )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "UNKNOWN_AGENT_ID"


def test_put_rejects_unsupported_reasoning_with_stable_error(
    repository, model_catalog
) -> None:
    payload = {
        "agent_id": "fault_diagnosis",
        "enabled": True,
        "model_binding_id": "chat-basic",
        "knowledge_dataset_ids": [],
        "streaming_enabled": True,
        "suggestions_enabled": True,
        "sources_enabled": True,
        "context_turns": 3,
        "retrieval_limit": 6,
        "similarity_threshold": 0.62,
        "deep_thinking_enabled": True,
        "deep_thinking_level": "medium",
        "max_reply_tokens": 4096,
    }

    response = make_client(repository, model_catalog).put(
        "/api/agent-configs/fault_diagnosis", json=payload
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "MODEL_REASONING_UNSUPPORTED"
    assert response.json()["detail"]["fields"][0]["field"] == "deep_thinking_enabled"


def test_get_exposes_capability_without_provider_secret(
    repository, model_catalog
) -> None:
    config = replace(
        AgentConfig.default_for(AgentId.METRIC_QUERY),
        enabled=True,
        model_binding_id="reasoning-pro",
    )
    repository.save(config)

    response = make_client(repository, model_catalog).get(
        "/api/agent-configs/metric_query"
    )

    assert response.status_code == 200
    assert response.json()["model_capability"] == {
        "binding_id": "reasoning-pro",
        "display_name": "推理模型",
        "supports_reasoning": True,
    }
    assert "never-return-this-api-key" not in response.text
    assert "api_key" not in response.text.lower()
    assert "access_token" not in response.text.lower()
    assert "provider_secret" not in response.text.lower()
