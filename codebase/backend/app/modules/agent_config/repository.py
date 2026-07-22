from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .domain import AgentConfig, AgentId, DeepThinkingLevel, ModelCapability
from .models import AgentConfigModel, ModelBinding, ModelProvider


def to_domain(row: AgentConfigModel) -> AgentConfig:
    return AgentConfig(
        agent_id=AgentId(row.agent_id),
        enabled=row.enabled,
        model_binding_id=row.model_binding_id,
        knowledge_dataset_ids=tuple(row.knowledge_dataset_ids),
        streaming_enabled=row.streaming_enabled,
        suggestions_enabled=row.suggestions_enabled,
        sources_enabled=row.sources_enabled,
        context_turns=row.context_turns,
        retrieval_limit=row.retrieval_limit,
        similarity_threshold=row.similarity_threshold,
        deep_thinking_enabled=row.deep_thinking_enabled,
        deep_thinking_level=DeepThinkingLevel(row.deep_thinking_level),
        max_reply_tokens=row.max_reply_tokens,
    )


def to_model(config: AgentConfig) -> AgentConfigModel:
    return AgentConfigModel(
        agent_id=config.agent_id.value,
        enabled=config.enabled,
        model_binding_id=config.model_binding_id,
        knowledge_dataset_ids=list(config.knowledge_dataset_ids),
        streaming_enabled=config.streaming_enabled,
        suggestions_enabled=config.suggestions_enabled,
        sources_enabled=config.sources_enabled,
        context_turns=config.context_turns,
        retrieval_limit=config.retrieval_limit,
        similarity_threshold=config.similarity_threshold,
        deep_thinking_enabled=config.deep_thinking_enabled,
        deep_thinking_level=config.deep_thinking_level.value,
        max_reply_tokens=config.max_reply_tokens,
    )


class SqlAgentConfigRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, agent_id: AgentId) -> AgentConfig | None:
        row = self._session.scalar(
            select(AgentConfigModel).where(AgentConfigModel.agent_id == agent_id.value)
        )
        return None if row is None else to_domain(row)

    def list_all(self) -> list[AgentConfig]:
        rows = self._session.scalars(select(AgentConfigModel)).all()
        return [to_domain(row) for row in rows]

    def insert_if_absent(self, config: AgentConfig) -> AgentConfig:
        existing = self.get(config.agent_id)
        if existing is not None:
            return existing
        try:
            with self._session.begin_nested():
                self._session.add(to_model(config))
                self._session.flush()
        except IntegrityError:
            existing = self.get(config.agent_id)
            if existing is not None:
                return existing
            raise
        return config

    def save(self, config: AgentConfig) -> AgentConfig:
        row = self._session.scalar(
            select(AgentConfigModel).where(
                AgentConfigModel.agent_id == config.agent_id.value
            )
        )
        if row is None:
            self._session.add(to_model(config))
        else:
            row.enabled = config.enabled
            row.model_binding_id = config.model_binding_id
            row.knowledge_dataset_ids = list(config.knowledge_dataset_ids)
            row.streaming_enabled = config.streaming_enabled
            row.suggestions_enabled = config.suggestions_enabled
            row.sources_enabled = config.sources_enabled
            row.context_turns = config.context_turns
            row.retrieval_limit = config.retrieval_limit
            row.similarity_threshold = config.similarity_threshold
            row.deep_thinking_enabled = config.deep_thinking_enabled
            row.deep_thinking_level = config.deep_thinking_level.value
            row.max_reply_tokens = config.max_reply_tokens
        self._session.flush()
        return config


class SqlModelCatalog:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, binding_id: str) -> ModelCapability | None:
        binding = self._session.scalar(
            select(ModelBinding)
            .join(ModelProvider, ModelBinding.provider_id == ModelProvider.id)
            .where(
                ModelBinding.id == binding_id,
                ModelBinding.enabled.is_(True),
                ModelProvider.enabled.is_(True),
            )
        )
        if binding is None:
            return None
        return ModelCapability(
            binding_id=binding.id,
            display_name=binding.name,
            supports_reasoning=binding.supports_reasoning,
        )
