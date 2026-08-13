"""Add system management role and user profile fields.

Revision ID: 0010_system_mgmt
Revises: 0009_task013_role_management
"""

from alembic import op
import sqlalchemy as sa


revision = "0010_system_mgmt"
down_revision = "0009_task013_role_management"
branch_labels = None
depends_on = None


def upgrade() -> None:
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
