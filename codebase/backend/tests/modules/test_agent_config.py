from dataclasses import FrozenInstanceError, replace

import pytest

from app.modules.agent_config.domain import (
    AgentConfig,
    AgentConfigSnapshot,
    AgentId,
    DeepThinkingLevel,
)
from app.modules.agent_config.service import AgentConfigError, AgentConfigService


def test_initialize_only_creates_requested_agent(repository, model_catalog) -> None:
    service = AgentConfigService(repository, model_catalog)

    created = service.initialize("fault_reporting")

    assert created.agent_id is AgentId.FAULT_REPORTING
    assert set(repository.configs) == {AgentId.FAULT_REPORTING}


def enabled_config(
    agent_id: AgentId, model_binding_id: str = "reasoning-pro"
) -> AgentConfig:
    return replace(
        AgentConfig.default_for(agent_id),
        enabled=True,
        model_binding_id=model_binding_id,
    )


def test_repeated_initialize_preserves_existing_config(repository, model_catalog) -> None:
    existing = enabled_config(AgentId.METRIC_QUERY)
    repository.save(existing)
    service = AgentConfigService(repository, model_catalog)

    assert service.initialize("metric_query") is existing


def test_save_changes_only_target_agent(repository, model_catalog) -> None:
    original_reporting = enabled_config(AgentId.FAULT_REPORTING)
    original_query = enabled_config(AgentId.METRIC_QUERY)
    repository.save(original_reporting)
    repository.save(original_query)
    service = AgentConfigService(repository, model_catalog)

    changed = replace(original_reporting, context_turns=8)
    service.save("fault_reporting", changed)

    assert repository.get(AgentId.FAULT_REPORTING) == changed
    assert repository.get(AgentId.METRIC_QUERY) is original_query


def test_non_reasoning_model_rejects_deep_thinking(repository, model_catalog) -> None:
    candidate = replace(
        enabled_config(AgentId.FAULT_DIAGNOSIS, "chat-basic"),
        deep_thinking_enabled=True,
    )
    service = AgentConfigService(repository, model_catalog)

    with pytest.raises(AgentConfigError) as caught:
        service.save("fault_diagnosis", candidate)

    assert caught.value.code == "MODEL_REASONING_UNSUPPORTED"
    assert caught.value.issues[0].field == "deep_thinking_enabled"


def test_reasoning_model_builds_immutable_secret_free_snapshot(
    repository, model_catalog
) -> None:
    candidate = replace(
        enabled_config(AgentId.FAULT_DIAGNOSIS),
        deep_thinking_enabled=True,
        deep_thinking_level=DeepThinkingLevel.HIGH,
    )
    repository.save(candidate)
    service = AgentConfigService(repository, model_catalog)

    snapshot = service.build_snapshot("fault_diagnosis")

    assert isinstance(snapshot, AgentConfigSnapshot)
    assert snapshot.deep_thinking_level is DeepThinkingLevel.HIGH
    assert "secret" not in repr(snapshot).lower()
    with pytest.raises(FrozenInstanceError):
        snapshot.context_turns = 1  # type: ignore[misc]


def test_enabled_config_without_model_cannot_build_snapshot(
    repository, model_catalog
) -> None:
    repository.save(
        replace(AgentConfig.default_for(AgentId.OPERATION_GUIDANCE), enabled=True)
    )
    service = AgentConfigService(repository, model_catalog)

    with pytest.raises(AgentConfigError) as caught:
        service.build_snapshot("operation_guidance")

    assert caught.value.code == "AGENT_CONFIG_INVALID"
    assert caught.value.issues[0].field == "model_binding_id"


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("context_turns", 11),
        ("retrieval_limit", 0),
        ("similarity_threshold", 1.1),
        ("max_reply_tokens", 511),
    ],
)
def test_out_of_range_parameter_is_rejected(
    field: str, invalid_value: int | float, repository, model_catalog
) -> None:
    candidate = replace(enabled_config(AgentId.FAULT_REPORTING), **{field: invalid_value})
    service = AgentConfigService(repository, model_catalog)

    with pytest.raises(AgentConfigError) as caught:
        service.save("fault_reporting", candidate)

    assert caught.value.code == "AGENT_CONFIG_INVALID"
    assert caught.value.issues[0].field == field


@pytest.mark.parametrize(
    "raw_agent_id",
    ["fault_reporting", "metric_query", "operation_guidance", "fault_diagnosis"],
)
def test_all_supported_agent_ids_are_stable(raw_agent_id: str) -> None:
    assert AgentId(raw_agent_id).value == raw_agent_id


def test_unknown_agent_id_is_rejected() -> None:
    with pytest.raises(ValueError):
        AgentId("shared_default")


def test_default_config_is_safe_and_agent_specific() -> None:
    config = AgentConfig.default_for(AgentId.FAULT_REPORTING)

    assert config.agent_id is AgentId.FAULT_REPORTING
    assert config.enabled is False
    assert config.model_binding_id is None
    assert config.knowledge_dataset_ids == ()
    assert config.deep_thinking_enabled is False
    assert config.deep_thinking_level is DeepThinkingLevel.MEDIUM
    assert config.context_turns == 3
    assert config.retrieval_limit == 6
    assert config.similarity_threshold == 0.62
    assert config.max_reply_tokens == 4096


def test_config_is_immutable() -> None:
    config = AgentConfig.default_for(AgentId.METRIC_QUERY)

    with pytest.raises(FrozenInstanceError):
        config.enabled = True  # type: ignore[misc]
