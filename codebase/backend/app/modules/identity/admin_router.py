from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.idempotency import find_idempotent_response, save_idempotent_response
from app.modules.audit.service import write_audit_event
from app.modules.identity.dependencies import require_permission
from app.modules.identity.models import Permission, Role, User
from app.modules.identity.security import hash_password


router = APIRouter(prefix="/api", tags=["identity-admin"])


class RoleCreate(BaseModel):
    name: str
    permission_codes: list[str]


class UserCreate(BaseModel):
    username: str
    password: str
    role_ids: list[str]


@router.post("/roles", status_code=201, response_model=None)
def create_role(
    payload: RoleCreate,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("identity:write")),
) -> dict[str, object] | JSONResponse:
    replay = find_idempotent_response(
        db, user_id=user.id, method="POST", path="/api/roles", key=idempotency_key
    )
    if replay is not None:
        status, body = replay
        return JSONResponse(status_code=status, content=body)
    if db.scalar(select(Role).where(Role.name == payload.name)) is not None:
        raise HTTPException(status_code=409, detail={"code": "ROLE_NAME_EXISTS"})

    permissions = list(db.scalars(select(Permission).where(Permission.code.in_(payload.permission_codes))))
    found_codes = {permission.code for permission in permissions}
    if found_codes != set(payload.permission_codes):
        raise HTTPException(status_code=422, detail={"code": "PERMISSION_NOT_FOUND"})

    role = Role(name=payload.name, permissions=permissions)
    db.add(role)
    db.flush()
    event = write_audit_event(
        db,
        actor_user_id=user.id,
        action="role.create",
        resource_type="role",
        resource_id=role.id,
        result="success",
        metadata=payload.model_dump(),
    )
    body: dict[str, object] = {
        "id": role.id,
        "name": role.name,
        "permission_codes": sorted(found_codes),
        "audit_event_id": event.id,
    }
    save_idempotent_response(
        db,
        user_id=user.id,
        method="POST",
        path="/api/roles",
        key=idempotency_key,
        status=201,
        body=body,
    )
    db.commit()
    return body


@router.post("/users", status_code=201, response_model=None)
def create_user(
    payload: UserCreate,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("identity:write")),
) -> dict[str, object] | JSONResponse:
    replay = find_idempotent_response(
        db, user_id=user.id, method="POST", path="/api/users", key=idempotency_key
    )
    if replay is not None:
        status, body = replay
        return JSONResponse(status_code=status, content=body)
    if db.scalar(select(User).where(User.username == payload.username)) is not None:
        raise HTTPException(status_code=409, detail={"code": "USERNAME_EXISTS"})

    roles = list(db.scalars(select(Role).where(Role.id.in_(payload.role_ids))))
    if {role.id for role in roles} != set(payload.role_ids):
        raise HTTPException(status_code=422, detail={"code": "ROLE_NOT_FOUND"})

    created_user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        roles=roles,
    )
    db.add(created_user)
    db.flush()
    event = write_audit_event(
        db,
        actor_user_id=user.id,
        action="user.create",
        resource_type="user",
        resource_id=created_user.id,
        result="success",
        metadata=payload.model_dump(),
    )
    body: dict[str, object] = {
        "id": created_user.id,
        "username": created_user.username,
        "enabled": created_user.enabled,
        "role_ids": sorted(role.id for role in roles),
        "audit_event_id": event.id,
    }
    save_idempotent_response(
        db,
        user_id=user.id,
        method="POST",
        path="/api/users",
        key=idempotency_key,
        status=201,
        body=body,
    )
    db.commit()
    return body
