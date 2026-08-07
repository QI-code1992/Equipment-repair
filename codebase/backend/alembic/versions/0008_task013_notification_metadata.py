"""Add notification related object metadata.

Revision ID: 0008_task013_notification_metadata
Revises: 0007_task013_notifications
"""

from alembic import op
import sqlalchemy as sa


revision = "0008_task013_notification_metadata"
down_revision = "0007_task013_notifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("notifications", sa.Column("related_object_id", sa.String(100)))
    op.create_index(
        "ix_notifications_type_related_object",
        "notifications",
        ["type", "related_object_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_notifications_type_related_object", table_name="notifications")
    op.drop_column("notifications", "related_object_id")
