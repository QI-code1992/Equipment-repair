"""Complete the TASK-002 identity, organization, and equipment contract.

Downgrade is destructive: status detail, organization catalog metadata, fixed-role
codes, and all other data stored only in 0002 columns are discarded.  It restores
the 0001 schema but never drops any table created by revision 0001.

Revision ID: 0002
Revises: 0001
"""

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import NAMESPACE_URL, uuid5

from alembic import op
import sqlalchemy as sa


revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ROLE_CODES = ("SYSTEM_ADMIN", "EQUIPMENT_ADMIN", "REPAIR_WORKER", "LINE_OPERATOR")
ORGANIZATION_TYPES = ("ROOT", "FACTORY", "WORKSHOP", "LINE")
EQUIPMENT_STATUSES = ("NORMAL", "FAULT", "REPAIRING", "DISABLED")
ROOT_ORGANIZATION_ID = str(uuid5(NAMESPACE_URL, "equipment-task-002-root-organization"))


def _fixed_role_id(code: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"equipment-task-002-role:{code}"))


def _legacy_role_code(role_id: str) -> str:
    return f"LEGACY_{role_id.replace('-', '_')}"


def _legacy_organization_code(organization_id: str) -> str:
    return f"ORG_{organization_id}"


def upgrade() -> None:
    op.add_column("roles", sa.Column("code", sa.String(100), nullable=True))
    op.add_column("roles", sa.Column("built_in", sa.Boolean(), nullable=True))

    organization_type = sa.Enum(*ORGANIZATION_TYPES, name="organization_type", native_enum=False)
    op.add_column("organizations", sa.Column("type", organization_type, nullable=True))
    op.add_column("organizations", sa.Column("code", sa.String(100), nullable=True))
    op.add_column("organizations", sa.Column("sort_order", sa.Integer(), nullable=True))
    op.add_column("organizations", sa.Column("enabled", sa.Boolean(), nullable=True))
    op.add_column("organizations", sa.Column("remark", sa.Text(), nullable=True))
    op.add_column(
        "organizations", sa.Column("created_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "organizations", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True)
    )

    equipment_status = sa.Enum(*EQUIPMENT_STATUSES, name="equipment_status", native_enum=False)
    op.add_column("equipment", sa.Column("model", sa.String(100), nullable=True))
    op.add_column("equipment", sa.Column("type", sa.String(100), nullable=True))
    op.add_column("equipment", sa.Column("manufacturer", sa.String(200), nullable=True))
    op.add_column("equipment", sa.Column("manufactured_at", sa.Date(), nullable=True))
    op.add_column("equipment", sa.Column("commissioned_at", sa.Date(), nullable=True))
    op.add_column("equipment", sa.Column("operating_hours", sa.Numeric(12, 2), nullable=True))
    op.add_column("equipment", sa.Column("status", equipment_status, nullable=True))
    op.add_column("equipment", sa.Column("owner_user_id", sa.String(36), nullable=True))
    op.add_column("equipment", sa.Column("image_refs", sa.JSON(), nullable=True))
    op.add_column("equipment", sa.Column("created_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("equipment", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))

    bind = op.get_bind()
    now = datetime.now(UTC)
    roles = sa.table(
        "roles",
        sa.column("id", sa.String(36)),
        sa.column("name", sa.String(100)),
        sa.column("code", sa.String(100)),
        sa.column("built_in", sa.Boolean()),
    )
    role_rows = list(bind.execute(sa.select(roles.c.id, roles.c.name)).mappings())
    present_codes: set[str] = set()
    for row in role_rows:
        if row["name"] == "system-administrator":
            code = "SYSTEM_ADMIN"
        elif row["name"] in ROLE_CODES:
            code = row["name"]
        else:
            code = _legacy_role_code(row["id"])
        present_codes.add(code)
        bind.execute(
            roles.update().where(roles.c.id == row["id"]).values(
                code=code, built_in=code in ROLE_CODES
            )
        )
    for code in ROLE_CODES:
        if code not in present_codes:
            bind.execute(
                roles.insert().values(
                    id=_fixed_role_id(code), code=code, name=code, built_in=True
                )
            )

    organizations = sa.table(
        "organizations",
        sa.column("id", sa.String(36)),
        sa.column("name", sa.String(200)),
        sa.column("parent_id", sa.String(36)),
        sa.column("type", sa.String(20)),
        sa.column("code", sa.String(100)),
        sa.column("sort_order", sa.Integer()),
        sa.column("enabled", sa.Boolean()),
        sa.column("remark", sa.Text()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    organization_rows = list(
        bind.execute(
            sa.select(organizations.c.id, organizations.c.name, organizations.c.parent_id)
        ).mappings()
    )
    parents = {row["id"]: row["parent_id"] for row in organization_rows}

    def depth(organization_id: str) -> int:
        current_id: str | None = organization_id
        visited: set[str] = set()
        result = 0
        while current_id is not None:
            if current_id in visited:
                raise RuntimeError("organization hierarchy contains a cycle")
            visited.add(current_id)
            result += 1
            current_id = parents.get(current_id)
        if result > 3:
            raise RuntimeError("organization hierarchy depth greater than 3 is not supported")
        return result

    inferred_types = {1: "FACTORY", 2: "WORKSHOP", 3: "LINE"}
    ordered_organizations = sorted(organization_rows, key=lambda item: item["id"])
    organization_depths = {row["id"]: depth(row["id"]) for row in ordered_organizations}
    bind.execute(
        organizations.insert().values(
            id=ROOT_ORGANIZATION_ID,
            type="ROOT",
            code="ROOT",
            name="ROOT",
            parent_id=None,
            sort_order=0,
            enabled=True,
            remark=None,
            created_at=now,
            updated_at=now,
        )
    )
    for index, row in enumerate(ordered_organizations):
        values: dict[str, object] = {
            "type": inferred_types[organization_depths[row["id"]]],
            "code": _legacy_organization_code(row["id"]),
            "sort_order": index,
            "enabled": True,
            "created_at": now,
            "updated_at": now,
        }
        if row["parent_id"] is None:
            values["parent_id"] = ROOT_ORGANIZATION_ID
        bind.execute(
            organizations.update().where(organizations.c.id == row["id"]).values(**values)
        )

    equipment = sa.table(
        "equipment",
        sa.column("enabled", sa.Boolean()),
        sa.column("operating_hours", sa.Numeric(12, 2)),
        sa.column("status", sa.String(20)),
        sa.column("image_refs", sa.JSON()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    bind.execute(
        equipment.update().values(
            operating_hours=0,
            status=sa.case((equipment.c.enabled.is_(False), "DISABLED"), else_="NORMAL"),
            image_refs=[],
            created_at=now,
            updated_at=now,
        )
    )

    with op.batch_alter_table("roles") as batch_op:
        batch_op.alter_column("code", existing_type=sa.String(100), nullable=False)
        batch_op.alter_column("built_in", existing_type=sa.Boolean(), nullable=False)
        batch_op.create_unique_constraint("uq_roles_code", ["code"])
    with op.batch_alter_table("organizations") as batch_op:
        batch_op.alter_column("type", existing_type=organization_type, nullable=False)
        batch_op.alter_column("code", existing_type=sa.String(100), nullable=False)
        batch_op.alter_column("sort_order", existing_type=sa.Integer(), nullable=False)
        batch_op.alter_column("enabled", existing_type=sa.Boolean(), nullable=False)
        batch_op.alter_column("created_at", existing_type=sa.DateTime(timezone=True), nullable=False)
        batch_op.alter_column("updated_at", existing_type=sa.DateTime(timezone=True), nullable=False)
        batch_op.create_unique_constraint("uq_organizations_code", ["code"])
        batch_op.create_unique_constraint(
            "uq_organizations_parent_name", ["parent_id", "name"]
        )
    with op.batch_alter_table("equipment") as batch_op:
        batch_op.create_foreign_key(
            "fk_equipment_owner_user_id_users", "users", ["owner_user_id"], ["id"]
        )
        batch_op.alter_column(
            "operating_hours", existing_type=sa.Numeric(12, 2), nullable=False
        )
        batch_op.alter_column("status", existing_type=equipment_status, nullable=False)
        batch_op.alter_column("image_refs", existing_type=sa.JSON(), nullable=False)
        batch_op.alter_column("created_at", existing_type=sa.DateTime(timezone=True), nullable=False)
        batch_op.alter_column("updated_at", existing_type=sa.DateTime(timezone=True), nullable=False)
        batch_op.create_check_constraint(
            "ck_equipment_operating_hours_nonnegative", "operating_hours >= 0"
        )
        batch_op.drop_column("enabled")


def downgrade() -> None:
    equipment_status = sa.Enum(*EQUIPMENT_STATUSES, name="equipment_status", native_enum=False)
    organization_type = sa.Enum(*ORGANIZATION_TYPES, name="organization_type", native_enum=False)

    with op.batch_alter_table("equipment") as batch_op:
        batch_op.add_column(sa.Column("enabled", sa.Boolean(), nullable=True))
    equipment = sa.table(
        "equipment",
        sa.column("enabled", sa.Boolean()),
        sa.column("status", sa.String(20)),
    )
    op.get_bind().execute(
        equipment.update().values(enabled=equipment.c.status != "DISABLED")
    )
    with op.batch_alter_table("equipment") as batch_op:
        batch_op.alter_column("enabled", existing_type=sa.Boolean(), nullable=False)
        batch_op.drop_constraint("ck_equipment_operating_hours_nonnegative", type_="check")
        for column_name in (
            "updated_at",
            "created_at",
            "image_refs",
            "owner_user_id",
            "status",
            "operating_hours",
            "commissioned_at",
            "manufactured_at",
            "manufacturer",
            "type",
            "model",
        ):
            batch_op.drop_column(column_name)
    equipment_status.drop(op.get_bind(), checkfirst=True)

    organizations = sa.table(
        "organizations",
        sa.column("id", sa.String(36)),
        sa.column("parent_id", sa.String(36)),
    )
    bind = op.get_bind()
    bind.execute(
        organizations.update()
        .where(organizations.c.parent_id == ROOT_ORGANIZATION_ID)
        .values(parent_id=None)
    )
    bind.execute(organizations.delete().where(organizations.c.id == ROOT_ORGANIZATION_ID))
    with op.batch_alter_table("organizations") as batch_op:
        batch_op.drop_constraint("uq_organizations_parent_name", type_="unique")
        batch_op.drop_constraint("uq_organizations_code", type_="unique")
        for column_name in (
            "updated_at",
            "created_at",
            "remark",
            "enabled",
            "sort_order",
            "code",
            "type",
        ):
            batch_op.drop_column(column_name)
    organization_type.drop(bind, checkfirst=True)

    with op.batch_alter_table("roles") as batch_op:
        batch_op.drop_constraint("uq_roles_code", type_="unique")
        batch_op.drop_column("built_in")
        batch_op.drop_column("code")
