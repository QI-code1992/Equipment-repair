"""Create TASK-013 notification tables.

Revision ID: 0007_task013_notifications
Revises: 0006_task005
"""

from alembic import op
import sqlalchemy as sa


revision = "0007_task013_notifications"
down_revision = "0006_task005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("level", sa.String(20), nullable=False),
        sa.Column("action_url", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_notifications_created_at", "notifications", ["created_at"])
    op.create_table(
        "notification_reads",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "notification_id",
            sa.String(36),
            sa.ForeignKey("notifications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "notification_id", "user_id", name="uq_notification_read_user_notification"
        ),
    )
    op.create_index(
        "ix_notification_reads_user_notification",
        "notification_reads",
        ["user_id", "notification_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_notification_reads_user_notification", table_name="notification_reads")
    op.drop_table("notification_reads")
    op.drop_index("ix_notifications_created_at", table_name="notifications")
    op.drop_table("notifications")
