from sqlalchemy import UniqueConstraint

from app.core.database import Base, create_database_engine, session_factory
from app.modules.equipment.models import Equipment, EquipmentStatus, Organization, OrganizationType
from app.modules.identity.bootstrap import FIXED_ROLE_CODES, bootstrap_admin
from app.modules.identity.models import Role, RoleCode


def test_task002_models_expose_full_contract() -> None:
    assert set(Equipment.__table__.c.keys()) >= {
        "id", "code", "name", "model", "type", "manufacturer",
        "manufactured_at", "commissioned_at", "operating_hours", "status",
        "organization_id", "owner_user_id", "image_refs", "created_at", "updated_at",
    }
    assert "enabled" not in Equipment.__table__.c
    assert set(Organization.__table__.c.keys()) >= {
        "id", "type", "code", "name", "parent_id", "sort_order",
        "enabled", "remark", "created_at", "updated_at",
    }
    assert set(FIXED_ROLE_CODES) == set(RoleCode)
    assert EquipmentStatus.DISABLED.value == "DISABLED"
    assert OrganizationType.LINE.value == "LINE"


def test_organization_has_global_code_and_sibling_name_constraints() -> None:
    names = {
        constraint.name
        for constraint in Organization.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    assert {"uq_organizations_code", "uq_organizations_parent_name"} <= names


def test_bootstrap_reuses_seeded_system_admin_catalog() -> None:
    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = session_factory(engine)
    with factory() as db:
        seeded_role = Role(
            code=RoleCode.SYSTEM_ADMIN.value,
            name=RoleCode.SYSTEM_ADMIN.value,
            built_in=True,
        )
        db.add(seeded_role)
        db.commit()

        user = bootstrap_admin(db, "first-admin", "bootstrap-password")

        assert user.roles == [seeded_role]
