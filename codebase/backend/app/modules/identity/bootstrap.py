import os

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.database import create_database_engine, session_factory
from app.modules.audit.service import write_audit_event
from app.modules.identity.models import Permission, Role, User
from app.modules.identity.security import hash_password


ADMIN_PERMISSION_CODES = (
    "identity:read",
    "identity:write",
    "equipment:read",
    "equipment:write",
    "organization:read",
    "organization:write",
)


class BootstrapAlreadyInitialized(RuntimeError):
    pass


def bootstrap_admin(db: Session, username: str, password: str) -> User:
    if not username.strip() or not password.strip():
        raise ValueError("bootstrap credentials must not be blank")
    if db.get_bind().dialect.name == "postgresql":
        db.execute(text("SELECT pg_advisory_xact_lock(824002)"))
    if db.scalar(select(func.count()).select_from(User)):
        raise BootstrapAlreadyInitialized("users already exist")
    permissions = [Permission(code=code) for code in ADMIN_PERMISSION_CODES]
    role = Role(name="system-administrator", permissions=permissions)
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
