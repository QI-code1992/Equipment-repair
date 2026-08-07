"""TASK-013 backfill built-in role labels and timestamps."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision = "0010_task013_role_labels"
down_revision: str | Sequence[str] | None = "0009_task013_role_management"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    roles = sa.table("roles", sa.column("code", sa.String), sa.column("name", sa.String), sa.column("updated_at", sa.DateTime))
    op.execute(sa.update(roles).where(roles.c.code == "SYSTEM_ADMIN").values(name="系统管理员"))
    op.execute(sa.update(roles).where(roles.c.code == "EQUIPMENT_ADMIN").values(name="设备管理员"))
    op.execute(sa.update(roles).where(roles.c.code == "REPAIR_WORKER").values(name="维修工"))
    op.execute(sa.update(roles).where(roles.c.code == "LINE_OPERATOR").values(name="产线作业员"))
    op.execute(sa.text("UPDATE roles SET updated_at = CURRENT_TIMESTAMP WHERE updated_at <= '1970-01-01 00:00:00'"))


def downgrade() -> None:
    roles = sa.table("roles", sa.column("code", sa.String), sa.column("name", sa.String))
    op.execute(sa.update(roles).where(roles.c.code == "SYSTEM_ADMIN").values(name="SYSTEM_ADMIN"))
    op.execute(sa.update(roles).where(roles.c.code == "EQUIPMENT_ADMIN").values(name="EQUIPMENT_ADMIN"))
    op.execute(sa.update(roles).where(roles.c.code == "REPAIR_WORKER").values(name="REPAIR_WORKER"))
    op.execute(sa.update(roles).where(roles.c.code == "LINE_OPERATOR").values(name="LINE_OPERATOR"))
