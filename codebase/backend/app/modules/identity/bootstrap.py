import os

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.database import create_database_engine, session_factory
from app.modules.audit.service import write_audit_event
from app.modules.identity.models import Permission, Role, RoleCode, User
from app.modules.identity.security import hash_password


API_PERMISSION_CODES = (
    "identity:read",
    "identity:write",
    "equipment:read",
    "equipment:write",
    "organization:read",
    "organization:write",
)
MENU_ACTION_PERMISSION_CODES = (
    "workbench:view",
    "workbench:export",
    "bi:view",
    "bi:export",
    "factory:view",
    "factory:manage",
    "equipment:view",
    "equipment:create",
    "equipment:edit",
    "equipment:delete",
    "fault:view",
    "fault:create",
    "fault:repair",
    "fault:close",
    "maintenance:view",
    "maintenance:detail",
    "maintenance:export",
    "system:role",
    "system:user",
    "user_management.view_all",
    "system:org",
    "system:audit",
    "intelligence:view",
    "intelligence:model",
    "intelligence:agent",
    "intelligence:knowledge",
    "intelligence:audit",
)
PERMISSION_CODES = API_PERMISSION_CODES + MENU_ACTION_PERMISSION_CODES
FIXED_ROLE_CODES = tuple(RoleCode)

DEFAULT_ROLE_PERMISSIONS = {
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
        "equipment:read", "workbench:view", "equipment:view", "fault:view", "fault:create",
    },
}


class BootstrapAlreadyInitialized(RuntimeError):
    pass


def ensure_identity_catalog(db: Session) -> dict[RoleCode, Role]:
    permissions = {
        code: db.scalar(select(Permission).where(Permission.code == code)) or Permission(code=code)
        for code in PERMISSION_CODES
    }
    roles: dict[RoleCode, Role] = {}
    for code in FIXED_ROLE_CODES:
        role = db.scalar(select(Role).where(Role.code == code.value))
        if role is None:
            role = Role(code=code.value, name=code.value, built_in=True)
            db.add(role)
        roles[code] = role
    roles[RoleCode.SYSTEM_ADMIN].permissions = list(permissions.values())
    for code, defaults in DEFAULT_ROLE_PERMISSIONS.items():
        if not roles[code].permissions:
            roles[code].permissions = [permissions[item] for item in sorted(defaults)]
    db.flush()
    return roles


def bootstrap_admin(db: Session, username: str, password: str) -> User:
    if not username.strip() or not password.strip():
        raise ValueError("bootstrap credentials must not be blank")
    if db.get_bind().dialect.name == "postgresql":
        db.execute(text("SELECT pg_advisory_xact_lock(824002)"))
    if db.scalar(select(func.count()).select_from(User)):
        raise BootstrapAlreadyInitialized("users already exist")
    role = ensure_identity_catalog(db)[RoleCode.SYSTEM_ADMIN]
    user = User(username=username, password_hash=hash_password(password), roles=[role])
    db.add(user)
    db.flush()
    write_audit_event(
        db,
        actor_user_id=None,
        action="user.bootstrap",
        resource_type="user",
        resource_id=user.id,
        result="success",
        metadata={"username": username},
    )
    db.commit()
    return user


def main() -> None:
    database_url = os.environ["POSTGRES_DSN"]
    username = os.environ["BOOTSTRAP_ADMIN_USERNAME"]
    password = os.environ["BOOTSTRAP_ADMIN_PASSWORD"]
    factory = session_factory(create_database_engine(database_url))
    with factory() as db:
        bootstrap_admin(db, username, password)


if __name__ == "__main__":
    main()
