from dataclasses import FrozenInstanceError

import pytest

from app.modules.agent_config.domain import AgentConfig, AgentId, DeepThinkingLevel


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
