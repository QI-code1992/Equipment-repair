"""add agent configuration schema

Revision ID: 0003
Revises: 0002
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "model_providers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("secret_ref", sa.String(500), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_table(
        "model_bindings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "provider_id",
            sa.String(36),
            sa.ForeignKey("model_providers.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("model_name", sa.String(200), nullable=False),
        sa.Column("supports_reasoning", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("provider_id", "name", name="uq_model_bindings_provider_name"),
    )
    op.create_table(
        "agent_configs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("agent_id", sa.String(36), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column(
            "model_binding_id",
            sa.String(36),
            sa.ForeignKey("model_bindings.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("knowledge_dataset_ids", sa.JSON(), nullable=False),
        sa.Column("streaming_enabled", sa.Boolean(), nullable=False),
        sa.Column("suggestions_enabled", sa.Boolean(), nullable=False),
        sa.Column("sources_enabled", sa.Boolean(), nullable=False),
        sa.Column("context_turns", sa.Integer(), nullable=False),
        sa.Column("retrieval_limit", sa.Integer(), nullable=False),
        sa.Column("similarity_threshold", sa.Float(), nullable=False),
        sa.Column("deep_thinking_enabled", sa.Boolean(), nullable=False),
        sa.Column("deep_thinking_level", sa.String(20), nullable=False),
        sa.Column("max_reply_tokens", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.UniqueConstraint("agent_id", name="uq_agent_configs_agent_id"),
    )


def downgrade() -> None:
    op.drop_table("agent_configs")
    op.drop_table("model_bindings")
    op.drop_table("model_providers")
