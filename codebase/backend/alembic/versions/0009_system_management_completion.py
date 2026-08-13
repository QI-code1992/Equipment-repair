"""Add system management role and user profile fields.

Revision ID: 0009_system_management_completion
Revises: 0008_task013_notification_metadata
"""

from alembic import op
import sqlalchemy as sa


revision = "0009_system_management_completion"
down_revision = "0008_task013_notification_metadata"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("roles", sa.Column("description", sa.Text()))
    op.add_column("roles", sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("roles", sa.Column("created_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("roles", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("display_name", sa.String(100)))
    op.add_column("users", sa.Column("gender", sa.String(20)))
    op.add_column("users", sa.Column("email", sa.String(254)))
    op.add_column("users", sa.Column("phone", sa.String(30)))
    op.add_column("users", sa.Column("remark", sa.Text()))
    op.add_column("users", sa.Column("organization_id", sa.String(36)))
    op.create_index("ix_users_organization_id", "users", ["organization_id"])


def downgrade() -> None:
    op.drop_index("ix_users_organization_id", table_name="users")
    for column in ("organization_id", "remark", "phone", "email", "gender", "display_name"):
        op.drop_column("users", column)
    for column in ("updated_at", "created_at", "enabled", "description"):
        op.drop_column("roles", column)
