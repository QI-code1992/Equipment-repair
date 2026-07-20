from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    false,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def new_id() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


class ModelProvider(Base):
    __tablename__ = "model_providers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    secret_ref: Mapped[str] = mapped_column(String(500), nullable=False)
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )


class ModelBinding(Base):
    __tablename__ = "model_bindings"
    __table_args__ = (
        UniqueConstraint("provider_id", "name", name="uq_model_bindings_provider_name"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    provider_id: Mapped[str] = mapped_column(
        ForeignKey("model_providers.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_name: Mapped[str] = mapped_column(String(200), nullable=False)
    supports_reasoning: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )


class AgentConfigModel(Base):
    __tablename__ = "agent_configs"
    __table_args__ = (UniqueConstraint("agent_id", name="uq_agent_configs_agent_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    agent_id: Mapped[str] = mapped_column(String(36), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)
    model_binding_id: Mapped[str | None] = mapped_column(
        ForeignKey("model_bindings.id", ondelete="RESTRICT")
    )
    knowledge_dataset_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    streaming_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)
    suggestions_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)
    sources_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)
    context_turns: Mapped[int] = mapped_column(Integer, nullable=False)
    retrieval_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    similarity_threshold: Mapped[float] = mapped_column(Float, nullable=False)
    deep_thinking_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)
    deep_thinking_level: Mapped[str] = mapped_column(String(20), nullable=False)
    max_reply_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )
    updated_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
