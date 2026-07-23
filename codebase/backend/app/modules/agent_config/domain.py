from dataclasses import dataclass
from enum import StrEnum


class AgentId(StrEnum):
    FAULT_REPORTING = "fault_reporting"
    METRIC_QUERY = "metric_query"
    OPERATION_GUIDANCE = "operation_guidance"
    FAULT_DIAGNOSIS = "fault_diagnosis"


class DeepThinkingLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class ModelCapability:
    binding_id: str
    display_name: str
    supports_reasoning: bool


@dataclass(frozen=True, slots=True)
class AgentConfig:
    agent_id: AgentId
    enabled: bool
    model_binding_id: str | None
    knowledge_dataset_ids: tuple[str, ...]
    streaming_enabled: bool
    suggestions_enabled: bool
    sources_enabled: bool
    context_turns: int
    retrieval_limit: int
    similarity_threshold: float
    deep_thinking_enabled: bool
    deep_thinking_level: DeepThinkingLevel
    max_reply_tokens: int

    @classmethod
    def default_for(cls, agent_id: AgentId) -> "AgentConfig":
        return cls(
            agent_id=agent_id,
            enabled=False,
            model_binding_id=None,
            knowledge_dataset_ids=(),
            streaming_enabled=True,
            suggestions_enabled=True,
            sources_enabled=True,
            context_turns=3,
            retrieval_limit=6,
            similarity_threshold=0.62,
            deep_thinking_enabled=False,
            deep_thinking_level=DeepThinkingLevel.MEDIUM,
            max_reply_tokens=4096,
        )


@dataclass(frozen=True, slots=True)
class AgentConfigSnapshot:
    agent_id: AgentId
    enabled: bool
    model_binding_id: str
    knowledge_dataset_ids: tuple[str, ...]
    streaming_enabled: bool
    suggestions_enabled: bool
    sources_enabled: bool
    context_turns: int
    retrieval_limit: int
    similarity_threshold: float
    deep_thinking_enabled: bool
    deep_thinking_level: DeepThinkingLevel
    max_reply_tokens: int
