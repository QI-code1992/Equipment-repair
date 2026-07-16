from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.identity.models import Permission, Role, RoleCode, User, user_roles
from app.modules.identity.security import hash_password
from app.modules.identity.schemas import UserCreate, UserUpdate


def fixed_roles(db: Session) -> list[Role]:
    return list(
        db.scalars(
            select(Role)
            .where(Role.code.in_([code.value for code in RoleCode]))
            .order_by(Role.code)
        ).unique()
    )


def users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.username)).unique())


def user_detail(db: Session, user_id: str) -> User:
    user = db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise HTTPException(status_code=404, detail={"code": "USER_NOT_FOUND"})
    return user


def roles_for_ids(db: Session, role_ids: list[str]) -> list[Role]:
    roles = list(
        db.scalars(
            select(Role).where(
                Role.id.in_(role_ids),
                Role.code.in_([code.value for code in RoleCode]),
            )
        ).unique()
    )
    if {role.id for role in roles} != set(role_ids):
        raise HTTPException(status_code=422, detail={"code": "ROLE_NOT_FOUND"})
    return roles


def create_user(db: Session, payload: UserCreate) -> User:
    if db.scalar(select(User).where(User.username == payload.username)) is not None:
        raise HTTPException(status_code=409, detail={"code": "USERNAME_EXISTS"})
    created = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        roles=roles_for_ids(db, payload.role_ids),
    )
    db.add(created)
    try:
        db.flush()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail={"code": "USERNAME_EXISTS"}) from error
    return created


def enabled_system_admin_count(db: Session) -> int:
    return int(
        db.scalar(
            select(func.count(func.distinct(User.id)))
            .select_from(User)
            .join(user_roles, user_roles.c.user_id == User.id)
            .join(Role, Role.id == user_roles.c.role_id)
            .where(User.enabled.is_(True), Role.code == RoleCode.SYSTEM_ADMIN.value)
        )
        or 0
    )


def update_user(
    db: Session, actor: User, user_id: str, payload: UserUpdate
) -> User:
    target = user_detail(db, user_id)
    roles = roles_for_ids(db, payload.role_ids)
    keeps_system_admin = any(role.code == RoleCode.SYSTEM_ADMIN.value for role in roles)
    is_enabled_system_admin = target.enabled and any(
        role.code == RoleCode.SYSTEM_ADMIN.value for role in target.roles
    )
    if target.id == actor.id and not payload.enabled:
        raise HTTPException(
            status_code=409, detail={"code": "USER_SELF_DISABLE_FORBIDDEN"}
        )
    if is_enabled_system_admin and (not payload.enabled or not keeps_system_admin):
        if enabled_system_admin_count(db) <= 1:
            raise HTTPException(
                status_code=409, detail={"code": "LAST_SYSTEM_ADMIN_REQUIRED"}
            )
    target.enabled = payload.enabled
    target.roles = roles
    db.flush()
    return target


def update_role_permissions(
    db: Session, role_id: str, permission_codes: list[str]
) -> Role:
    role = db.scalar(select(Role).where(Role.id == role_id))
    if role is None or role.code not in {code.value for code in RoleCode}:
        raise HTTPException(status_code=404, detail={"code": "ROLE_NOT_FOUND"})
    if role.code == RoleCode.SYSTEM_ADMIN.value:
        raise HTTPException(
            status_code=409, detail={"code": "SYSTEM_ADMIN_PERMISSIONS_FIXED"}
        )
    permissions = list(
        db.scalars(select(Permission).where(Permission.code.in_(permission_codes)))
    )
    if {permission.code for permission in permissions} != set(permission_codes):
        raise HTTPException(status_code=422, detail={"code": "PERMISSION_NOT_FOUND"})
    role.permissions = permissions
    db.flush()
    return role
