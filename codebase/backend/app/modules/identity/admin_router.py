from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.idempotency import find_idempotent_response, save_idempotent_response
from app.modules.audit.service import write_audit_event
from app.modules.identity import admin_service
from app.modules.identity.dependencies import require_permission
from app.modules.identity.models import Permission, Role, User
from app.modules.identity.schemas import RolePermissionsUpdate, UserCreate, UserUpdate


router = APIRouter(prefix="/api", tags=["identity-admin"])


def role_body(role: Role) -> dict[str, object]:
    return {
        "id": role.id,
        "code": role.code,
        "name": role.name,
        "permission_codes": sorted(permission.code for permission in role.permissions),
    }


def user_body(user: User) -> dict[str, object]:
    return {
        "id": user.id,
        "username": user.username,
        "enabled": user.enabled,
        "role_ids": sorted(role.id for role in user.roles),
    }


@router.get("/permissions")
def list_permissions(
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("identity:read")),
) -> list[dict[str, str]]:
    del actor
    permissions = db.scalars(select(Permission).order_by(Permission.code)).all()
    return [{"code": permission.code} for permission in permissions]


@router.get("/roles")
def list_roles(
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("identity:read")),
) -> list[dict[str, object]]:
    del actor
    return [role_body(role) for role in admin_service.fixed_roles(db)]


@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("identity:read")),
) -> list[dict[str, object]]:
    del actor
    return [user_body(user) for user in admin_service.users(db)]


@router.get("/users/{user_id}")
def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("identity:read")),
) -> dict[str, object]:
    del actor
    return user_body(admin_service.user_detail(db, user_id))


@router.post("/users", status_code=201, response_model=None, name="user.create")
def create_user(
    payload: UserCreate,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("identity:write")),
) -> dict[str, object] | JSONResponse:
    request_body = payload.model_dump(mode="json")
    replay = find_idempotent_response(
        db, user_id=actor.id, method="POST", path="/api/users",
        key=idempotency_key, request_body=request_body,
    )
    if replay is not None:
        return JSONResponse(status_code=replay[0], content=replay[1])
    created = admin_service.create_user(db, payload)
    event = write_audit_event(
        db, actor_user_id=actor.id, action="user.create", resource_type="user",
        resource_id=created.id, result="success", metadata={"username": created.username},
    )
    body = {**user_body(created), "audit_event_id": event.id}
    save_idempotent_response(
        db, user_id=actor.id, method="POST", path="/api/users",
        key=idempotency_key, request_body=request_body, status=201, body=body,
    )
    db.commit()
    return body


@router.patch("/users/{user_id}", response_model=None, name="user.update")
def update_user(
    user_id: str,
    payload: UserUpdate,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("identity:write")),
) -> dict[str, object] | JSONResponse:
    request_body = payload.model_dump(mode="json")
    path = f"/api/users/{user_id}"
    replay = find_idempotent_response(
        db, user_id=actor.id, method="PATCH", path=path,
        key=idempotency_key, request_body=request_body,
    )
    if replay is not None:
        return JSONResponse(status_code=replay[0], content=replay[1])
    updated = admin_service.update_user(db, actor, user_id, payload)
    event = write_audit_event(
        db, actor_user_id=actor.id, action="user.update", resource_type="user",
        resource_id=updated.id, result="success", metadata=request_body,
    )
    body = {**user_body(updated), "audit_event_id": event.id}
    save_idempotent_response(
        db, user_id=actor.id, method="PATCH", path=path,
        key=idempotency_key, request_body=request_body, status=200, body=body,
    )
    db.commit()
    return body


@router.patch(
    "/roles/{role_id}/permissions", response_model=None, name="role.permissions.update"
)
def update_role_permissions(
    role_id: str,
    payload: RolePermissionsUpdate,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("identity:write")),
) -> dict[str, object] | JSONResponse:
    request_body = payload.model_dump(mode="json")
    path = f"/api/roles/{role_id}/permissions"
    replay = find_idempotent_response(
        db, user_id=actor.id, method="PATCH", path=path,
        key=idempotency_key, request_body=request_body,
    )
    if replay is not None:
        return JSONResponse(status_code=replay[0], content=replay[1])
    role = admin_service.update_role_permissions(db, role_id, payload.permission_codes)
    event = write_audit_event(
        db, actor_user_id=actor.id, action="role.permissions.update",
        resource_type="role", resource_id=role.id, result="success",
        metadata=request_body,
    )
    body = {**role_body(role), "audit_event_id": event.id}
    save_idempotent_response(
        db, user_id=actor.id, method="PATCH", path=path,
        key=idempotency_key, request_body=request_body, status=200, body=body,
    )
    db.commit()
    return body
