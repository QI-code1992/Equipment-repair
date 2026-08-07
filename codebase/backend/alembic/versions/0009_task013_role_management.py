"""TASK-013 role management lifecycle."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision = "0009_task013_role_management"
down_revision: str | Sequence[str] | None = "0008_task013_notif_meta"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("roles", sa.Column("description", sa.String(length=500), nullable=False, server_default=""))
    op.add_column("roles", sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("roles", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("roles", sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("'1970-01-01 00:00:00'")))
    op.add_column("roles", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("'1970-01-01 00:00:00'")))


def downgrade() -> None:
    op.drop_column("roles", "updated_at")
    op.drop_column("roles", "created_at")
    op.drop_column("roles", "deleted_at")
    op.drop_column("roles", "enabled")
    op.drop_column("roles", "description")
