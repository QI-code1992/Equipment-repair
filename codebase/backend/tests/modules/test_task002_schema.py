from sqlalchemy import UniqueConstraint

from app.core.database import Base, create_database_engine, session_factory
from app.modules.equipment.models import Equipment, EquipmentStatus, Organization, OrganizationType
from app.modules.identity.bootstrap import (
    DEFAULT_ROLE_PERMISSIONS,
    FIXED_ROLE_CODES,
    PERMISSION_CODES,
    bootstrap_admin,
    ensure_identity_catalog,
)
from app.modules.identity.models import Permission, Role, RoleCode


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
    for column_name in ("model", "type", "manufacturer", "organization_id"):
        assert Equipment.__table__.c[column_name].nullable is False


def test_equipment_has_no_enabled_compatibility_attribute() -> None:
    assert not hasattr(Equipment, "enabled")


def test_role_code_has_no_automatic_default() -> None:
    assert Role.__table__.c.code.default is None


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


def test_identity_catalog_has_exact_permissions_and_role_defaults() -> None:
    expected_permissions = {
        "identity:read", "identity:write", "equipment:read", "equipment:write",
        "organization:read", "organization:write", "workbench:view",
        "workbench:export", "bi:view", "bi:export", "factory:view",
        "factory:manage", "equipment:view", "equipment:create", "equipment:edit",
        "equipment:delete", "fault:view", "fault:create", "fault:repair",
        "fault:close", "maintenance:view", "maintenance:detail", "maintenance:export",
        "system:role", "system:user", "user_management.view_all", "system:org",
        "system:audit", "intelligence:view", "intelligence:model",
        "intelligence:agent", "intelligence:knowledge", "intelligence:audit",
    }
    expected_role_permissions = {
        RoleCode.EQUIPMENT_ADMIN: {
            "identity:read", "equipment:read", "equipment:write", "organization:read",
            "workbench:view", "bi:view", "factory:view", "equipment:view",
            "equipment:create", "equipment:edit", "fault:view", "fault:create",
            "maintenance:view", "maintenance:detail",
        },
        RoleCode.REPAIR_WORKER: {
            "equipment:read", "workbench:view", "equipment:view", "fault:view",
            "fault:repair", "fault:close", "maintenance:view", "maintenance:detail",
        },
        RoleCode.LINE_OPERATOR: {
            "equipment:read", "workbench:view", "equipment:view", "fault:view",
            "fault:create",
        },
    }
    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = session_factory(engine)
    with factory() as db:
        roles = ensure_identity_catalog(db)
        db.commit()
        roles_again = ensure_identity_catalog(db)

        assert roles_again == roles
        assert len(PERMISSION_CODES) == len(expected_permissions)
        assert set(PERMISSION_CODES) == expected_permissions
        assert {
            role_code: set(permission_codes)
            for role_code, permission_codes in DEFAULT_ROLE_PERMISSIONS.items()
        } == expected_role_permissions
        assert {permission.code for permission in db.query(Permission).all()} == expected_permissions
        assert {
            permission.code for permission in roles[RoleCode.SYSTEM_ADMIN].permissions
        } == expected_permissions
        for role_code, expected_codes in expected_role_permissions.items():
            assert {permission.code for permission in roles[role_code].permissions} == set(
                expected_codes
            )
        assert all(role.built_in for role in roles.values())
