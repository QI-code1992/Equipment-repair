from datetime import UTC, datetime, timedelta
import hashlib
import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.identity.models import (
    LoginSession,
    Permission,
    Role,
    RoleCode,
    User,
    role_permissions,
    user_roles,
)
from app.modules.identity.security import verify_password
from app.modules.audit.service import write_audit_event
from app.modules.identity.security import hash_password


DUMMY_PASSWORD_HASH = hash_password("invalid-user-password")


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_login_session(db: Session, username: str, password: str) -> str | None:
    user = db.scalar(select(User).where(User.username == username))
    password_valid = verify_password(
        password,
        DUMMY_PASSWORD_HASH if user is None else user.password_hash,
    )
    if user is None or not user.enabled or not password_valid:
        write_audit_event(
            db,
            actor_user_id=None if user is None else user.id,
            action="login",
            resource_type="user",
            resource_id=None if user is None else user.id,
            result="failed",
            metadata={"username": username},
        )
        db.commit()
        return None

    token = secrets.token_urlsafe(32)
    db.add(
        LoginSession(
            user_id=user.id,
            token_hash=token_digest(token),
            expires_at=datetime.now(UTC) + timedelta(hours=8),
        )
    )
    write_audit_event(
        db,
        actor_user_id=user.id,
        action="login",
        resource_type="user",
        resource_id=user.id,
        result="success",
        metadata={"username": username},
    )
    db.commit()
    return token


def login_session_for_token(db: Session, token: str) -> LoginSession | None:
    return db.scalar(select(LoginSession).where(LoginSession.token_hash == token_digest(token)))


def active_user_for_session(db: Session, login_session: LoginSession) -> User | None:
    if login_session.revoked_at is not None:
        return None

    expires_at = login_session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at <= datetime.now(UTC):
        return None

    user = db.get(User, login_session.user_id)
    if user is None or not user.enabled:
        return None
    return user


def user_for_token(db: Session, token: str) -> User | None:
    login_session = login_session_for_token(db, token)
    if login_session is None:
        return None
    return active_user_for_session(db, login_session)


def permission_codes_for_user(db: Session, user_id: str) -> set[str]:
    statement = (
        select(Permission.code)
        .join(role_permissions, Permission.id == role_permissions.c.permission_id)
        .join(user_roles, role_permissions.c.role_id == user_roles.c.role_id)
        .join(Role, Role.id == user_roles.c.role_id)
        .where(
            user_roles.c.user_id == user_id,
            Role.code.in_([code.value for code in RoleCode]),
        )
    )
    return set(db.scalars(statement))
