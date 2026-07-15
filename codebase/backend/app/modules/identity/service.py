from datetime import UTC, datetime, timedelta
import hashlib
import secrets

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.modules.identity.models import (
    LoginSession,
    Permission,
    User,
    role_permissions,
    user_roles,
)
from app.modules.identity.security import verify_password


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_login_session(db: Session, username: str, password: str) -> str | None:
    user = db.scalar(select(User).where(User.username == username))
    if user is None or not user.enabled or not verify_password(password, user.password_hash):
        return None

    token = secrets.token_urlsafe(32)
    db.add(
        LoginSession(
            user_id=user.id,
            token_hash=token_digest(token),
            expires_at=datetime.now(UTC) + timedelta(hours=8),
        )
    )
    db.commit()
    return token


def user_for_token(db: Session, token: str) -> User | None:
    login_session = db.scalar(
        select(LoginSession).where(LoginSession.token_hash == token_digest(token))
    )
    if login_session is None or login_session.revoked_at is not None:
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


def revoke_token(db: Session, token: str) -> None:
    db.execute(
        update(LoginSession)
        .where(LoginSession.token_hash == token_digest(token))
        .values(revoked_at=datetime.now(UTC))
    )
    db.commit()


def permission_codes_for_user(db: Session, user_id: str) -> set[str]:
    statement = (
        select(Permission.code)
        .join(role_permissions, Permission.id == role_permissions.c.permission_id)
        .join(user_roles, role_permissions.c.role_id == user_roles.c.role_id)
        .where(user_roles.c.user_id == user_id)
    )
    return set(db.scalars(statement))
