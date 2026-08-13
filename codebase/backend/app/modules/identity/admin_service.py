from fastapi import HTTPException
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.identity.models import LoginSession, Permission, Role, RoleCode, User, user_roles, utc_now
from app.modules.identity.security import hash_password
from app.modules.identity.schemas import UserCreate, UserUpdate
from app.modules.identity.service import permission_codes_for_user


IDENTITY_ADMIN_LOCK_ID = 824004


def acquire_identity_admin_lock(db: Session) -> None:
    if db.get_bind().dialect.name == "postgresql":
        db.execute(
            text("SELECT pg_advisory_xact_lock(:lock_id)"),
            {"lock_id": IDENTITY_ADMIN_LOCK_ID},
        )


def fixed_roles(db: Session) -> list[Role]:
    return list(db.scalars(select(Role).order_by(Role.built_in.desc(), Role.code)).unique())


def users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.username)).unique())


def user_detail(db: Session, user_id: str) -> User:
    user = db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise HTTPException(status_code=404, detail={"code": "USER_NOT_FOUND"})
    return user


def can_view_all_users(db: Session, actor: User) -> bool:
    return "user_management.view_all" in permission_codes_for_user(db, actor.id)


def visible_users(db: Session, actor: User, organization_id: str | None = None) -> list[User]:
    if organization_id is not None:
        from app.modules.equipment.models import Organization
        if db.get(Organization, organization_id) is None:
            raise HTTPException(status_code=404, detail={"code": "ORGANIZATION_NOT_FOUND"})
    if can_view_all_users(db, actor):
        return list(db.scalars(select(User).where(User.organization_id == organization_id).order_by(User.username)).unique()) if organization_id is not None else users(db)
    return [actor]


def visible_user_detail(db: Session, actor: User, user_id: str) -> User:
    if actor.id == user_id or can_view_all_users(db, actor):
        return user_detail(db, user_id)
    raise HTTPException(status_code=403, detail={"code": "PERMISSION_DENIED"})


def roles_for_ids(db: Session, role_ids: list[str]) -> list[Role]:
    roles = list(
        db.scalars(
            select(Role).where(
                Role.id.in_(role_ids), Role.enabled.is_(True),
            )
        ).unique()
    )
    if {role.id for role in roles} != set(role_ids):
        raise HTTPException(status_code=422, detail={"code": "ROLE_NOT_FOUND"})
    return roles


def permissions_for_codes(db: Session, codes: list[str]) -> list[Permission]:
    permissions = list(db.scalars(select(Permission).where(Permission.code.in_(codes))))
    if {permission.code for permission in permissions} != set(codes):
        raise HTTPException(status_code=422, detail={"code": "PERMISSION_NOT_FOUND"})
    return permissions


def role_detail(db: Session, role_id: str) -> Role:
    role = db.get(Role, role_id)
    if role is None:
        raise HTTPException(status_code=404, detail={"code": "ROLE_NOT_FOUND"})
    return role


def create_role(db: Session, payload: object) -> Role:
    acquire_identity_admin_lock(db)
    if db.scalar(select(Role).where((Role.code == payload.code) | (Role.name == payload.name))):
        raise HTTPException(status_code=409, detail={"code": "ROLE_EXISTS"})
    role = Role(code=payload.code, name=payload.name, description=payload.description, enabled=payload.enabled, built_in=False, permissions=permissions_for_codes(db, payload.permission_codes))
    db.add(role)
    db.flush()
    return role


def update_role(db: Session, role_id: str, payload: object) -> Role:
    acquire_identity_admin_lock(db)
    role = role_detail(db, role_id)
    if role.built_in:
        raise HTTPException(status_code=409, detail={"code": "BUILT_IN_ROLE_IMMUTABLE"})
    if not payload.enabled and db.scalar(select(func.count()).select_from(user_roles).where(user_roles.c.role_id == role.id)):
        raise HTTPException(status_code=409, detail={"code": "ROLE_HAS_USERS"})
    role.name, role.description, role.enabled = payload.name, payload.description, payload.enabled
    role.permissions = permissions_for_codes(db, payload.permission_codes)
    db.flush()
    return role


def delete_role(db: Session, role_id: str) -> Role:
    acquire_identity_admin_lock(db)
    role = role_detail(db, role_id)
    if role.built_in:
        raise HTTPException(status_code=409, detail={"code": "BUILT_IN_ROLE_IMMUTABLE"})
    if db.scalar(select(func.count()).select_from(user_roles).where(user_roles.c.role_id == role.id)):
        raise HTTPException(status_code=409, detail={"code": "ROLE_HAS_USERS"})
    db.delete(role)
    db.flush()
    return role


def create_user(db: Session, payload: UserCreate) -> User:
    if payload.organization_id is not None:
        from app.modules.equipment.models import Organization
        if db.get(Organization, payload.organization_id) is None:
            raise HTTPException(status_code=404, detail={"code": "ORGANIZATION_NOT_FOUND"})
    if db.scalar(select(User).where(User.username == payload.username)) is not None:
        raise HTTPException(status_code=409, detail={"code": "USERNAME_EXISTS"})
    created = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        roles=roles_for_ids(db, payload.role_ids),
        display_name=payload.display_name, gender=payload.gender, email=payload.email,
        phone=payload.phone, remark=payload.remark, organization_id=payload.organization_id,
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
    acquire_identity_admin_lock(db)
    target = user_detail(db, user_id)
    if payload.organization_id is not None:
        from app.modules.equipment.models import Organization
        if db.get(Organization, payload.organization_id) is None:
            raise HTTPException(status_code=404, detail={"code": "ORGANIZATION_NOT_FOUND"})
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
    target.display_name, target.gender, target.email = payload.display_name, payload.gender, payload.email
    target.phone, target.remark, target.organization_id = payload.phone, payload.remark, payload.organization_id
    db.flush()
    return target


def update_role_permissions(
    db: Session, role_id: str, permission_codes: list[str]
) -> Role:
    role = db.scalar(select(Role).where(Role.id == role_id))
    if role is None:
        raise HTTPException(status_code=404, detail={"code": "ROLE_NOT_FOUND"})
    if role.code == RoleCode.SYSTEM_ADMIN.value:
        raise HTTPException(
            status_code=409, detail={"code": "SYSTEM_ADMIN_PERMISSIONS_FIXED"}
        )
    role.permissions = permissions_for_codes(db, permission_codes)
    db.flush()
    return role


def reset_password(db: Session, user_id: str, password: str) -> User:
    target = user_detail(db, user_id)
    target.password_hash = hash_password(password)
    for session in db.scalars(select(LoginSession).where(LoginSession.user_id == target.id, LoginSession.revoked_at.is_(None))):
        session.revoked_at = utc_now()
    db.flush()
    return target
