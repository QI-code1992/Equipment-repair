from dataclasses import dataclass
from typing import Protocol

from .domain import AgentConfig, AgentConfigSnapshot, AgentId, ModelCapability


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    field: str
    message: str


class AgentConfigError(Exception):
    def __init__(self, code: str, message: str, *issues: ValidationIssue) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.issues = issues


class AgentConfigRepository(Protocol):
    def get(self, agent_id: AgentId) -> AgentConfig | None: ...
    def list_all(self) -> list[AgentConfig]: ...
    def insert_if_absent(self, config: AgentConfig) -> AgentConfig: ...
    def save(self, config: AgentConfig) -> AgentConfig: ...


class ModelCatalog(Protocol):
    def get(self, binding_id: str) -> ModelCapability | None: ...


def parse_agent_id(raw_agent_id: str | AgentId) -> AgentId:
    try:
        return AgentId(raw_agent_id)
    except ValueError as error:
        raise AgentConfigError(
            "UNKNOWN_AGENT_ID",
            "未知 Agent 标识。",
            ValidationIssue("agent_id", "仅允许四个已登记的 agent_id。"),
        ) from error


class AgentConfigService:
    def __init__(self, repository: AgentConfigRepository, model_catalog: ModelCatalog) -> None:
        self._repository = repository
        self._model_catalog = model_catalog

    def initialize(self, agent_id: str | AgentId) -> AgentConfig:
        parsed = parse_agent_id(agent_id)
        return self._repository.insert_if_absent(AgentConfig.default_for(parsed))

    def get(self, agent_id: str | AgentId) -> AgentConfig:
        parsed = parse_agent_id(agent_id)
        config = self._repository.get(parsed)
        if config is None:
            raise AgentConfigError(
                "AGENT_CONFIG_NOT_FOUND",
                "Agent 配置尚未初始化。",
                ValidationIssue("agent_id", "目标 Agent 没有当前有效配置。"),
            )
        return config

    def list_all(self) -> list[AgentConfig]:
        configs = {config.agent_id: config for config in self._repository.list_all()}
        return [configs[agent_id] for agent_id in AgentId if agent_id in configs]

    def save(self, agent_id: str | AgentId, candidate: AgentConfig) -> AgentConfig:
        parsed = parse_agent_id(agent_id)
        if candidate.agent_id is not parsed:
            raise AgentConfigError(
                "AGENT_CONFIG_INVALID",
                "路径与配置身份不一致。",
                ValidationIssue("agent_id", "请求体 agent_id 必须与路径一致。"),
            )
        self._validate(candidate, require_enabled=False)
        return self._repository.save(candidate)

    def build_snapshot(self, agent_id: str | AgentId) -> AgentConfigSnapshot:
        config = self.get(agent_id)
        self._validate(config, require_enabled=True)
        assert config.model_binding_id is not None
        return AgentConfigSnapshot(
            agent_id=config.agent_id,
            enabled=config.enabled,
            model_binding_id=config.model_binding_id,
            knowledge_dataset_ids=tuple(config.knowledge_dataset_ids),
            streaming_enabled=config.streaming_enabled,
            suggestions_enabled=config.suggestions_enabled,
            sources_enabled=config.sources_enabled,
            context_turns=config.context_turns,
            retrieval_limit=config.retrieval_limit,
            similarity_threshold=config.similarity_threshold,
            deep_thinking_enabled=config.deep_thinking_enabled,
            deep_thinking_level=config.deep_thinking_level,
            max_reply_tokens=config.max_reply_tokens,
        )

    def model_capability(self, binding_id: str | None) -> ModelCapability | None:
        return None if binding_id is None else self._model_catalog.get(binding_id)

    def _validate(self, config: AgentConfig, *, require_enabled: bool) -> None:
        if require_enabled and not config.enabled:
            raise AgentConfigError("AGENT_DISABLED", "Agent 未启用。")

        ranges = (
            ("context_turns", 0 <= config.context_turns <= 10, "必须在 0 到 10 之间。"),
            ("retrieval_limit", 1 <= config.retrieval_limit <= 20, "必须在 1 到 20 之间。"),
            (
                "similarity_threshold",
                0.0 <= config.similarity_threshold <= 1.0,
                "必须在 0.0 到 1.0 之间。",
            ),
            (
                "max_reply_tokens",
                512 <= config.max_reply_tokens <= 8192,
                "必须在 512 到 8192 之间。",
            ),
        )
        for field, valid, message in ranges:
            if not valid:
                raise AgentConfigError(
                    "AGENT_CONFIG_INVALID",
                    "Agent 配置参数无效。",
                    ValidationIssue(field, message),
                )

        model_required = config.enabled or config.deep_thinking_enabled
        if model_required and not config.model_binding_id:
            raise AgentConfigError(
                "AGENT_CONFIG_INVALID",
                "Agent 配置缺少模型绑定。",
                ValidationIssue(
                    "model_binding_id", "启用或深度思考配置必须绑定模型。"
                ),
            )
        capability = self.model_capability(config.model_binding_id)
        if config.model_binding_id and capability is None:
            raise AgentConfigError(
                "AGENT_CONFIG_INVALID",
                "模型绑定不存在。",
                ValidationIssue("model_binding_id", "请选择模型目录中的有效绑定。"),
            )
        if config.deep_thinking_enabled and capability and not capability.supports_reasoning:
            raise AgentConfigError(
                "MODEL_REASONING_UNSUPPORTED",
                "当前模型不支持深度思考。",
                ValidationIssue(
                    "deep_thinking_enabled", "请关闭深度思考或更换推理模型。"
                ),
            )
