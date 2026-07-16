from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.idempotency import find_idempotent_response, save_idempotent_response
from app.modules.audit.service import write_audit_event
from app.modules.equipment import organization_service
from app.modules.equipment.models import Organization
from app.modules.equipment.organization_service import (
    ORGANIZATION_TREE_LOCK_ID,
    acquire_organization_tree_lock,
)
from app.modules.equipment.schemas import OrganizationCreate, OrganizationUpdate
from app.modules.identity.dependencies import require_permission
from app.modules.identity.models import User


router = APIRouter(prefix="/api/organizations", tags=["organizations"])


def organization_body(organization: Organization) -> dict[str, object]:
    return {
        "id": organization.id,
        "type": organization.type.value,
        "code": organization.code,
        "name": organization.name,
        "parent_id": organization.parent_id,
        "sort_order": organization.sort_order,
        "enabled": organization.enabled,
        "remark": organization.remark or "",
    }


def _replay(
    db: Session, actor: User, method: str, path: str, key: str, body: object
) -> JSONResponse | None:
    response = find_idempotent_response(
        db,
        user_id=actor.id,
        method=method,
        path=path,
        key=key,
        request_body=body,
    )
    if response is None:
        return None
    return JSONResponse(status_code=response[0], content=response[1])


def _complete_write(
    db: Session,
    actor: User,
    organization: Organization,
    *,
    action: str,
    method: str,
    path: str,
    key: str | None,
    request_body: object,
    status: int,
) -> dict[str, object]:
    event = write_audit_event(
        db,
        actor_user_id=actor.id,
        action=action,
        resource_type="organization",
        resource_id=organization.id,
        result="success",
        metadata=request_body,
    )
    body = {**organization_body(organization), "audit_event_id": event.id}
    if key is not None:
        save_idempotent_response(
            db,
            user_id=actor.id,
            method=method,
            path=path,
            key=key,
            request_body=request_body,
            status=status,
            body=body,
        )
    db.commit()
    return body


@router.get("")
def list_organizations(
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("organization:read")),
) -> list[dict[str, object]]:
    del actor
    return [organization_body(item) for item in organization_service.organizations(db)]


@router.post("", status_code=201, response_model=None, name="organization.create")
def create_organization(
    payload: OrganizationCreate,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("organization:write")),
) -> dict[str, object] | JSONResponse:
    acquire_organization_tree_lock(db)
    request_body = payload.model_dump(mode="json")
    replay = _replay(db, actor, "POST", "/api/organizations", idempotency_key, request_body)
    if replay is not None:
        return replay
    created = organization_service.create_organization(db, payload)
    return _complete_write(
        db, actor, created, action="organization.create", method="POST",
        path="/api/organizations", key=idempotency_key, request_body=request_body,
        status=201,
    )


@router.patch("/{organization_id}", response_model=None, name="organization.update")
def update_organization(
    organization_id: str,
    payload: OrganizationUpdate,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("organization:write")),
) -> dict[str, object] | JSONResponse:
    acquire_organization_tree_lock(db)
    path = f"/api/organizations/{organization_id}"
    request_body = payload.model_dump(mode="json")
    replay = _replay(db, actor, "PATCH", path, idempotency_key, request_body)
    if replay is not None:
        return replay
    updated = organization_service.update_organization(db, organization_id, payload)
    return _complete_write(
        db, actor, updated, action="organization.update", method="PATCH", path=path,
        key=idempotency_key, request_body=request_body, status=200,
    )


@router.delete("/{organization_id}", name="organization.delete")
def delete_organization(
    organization_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("organization:write")),
) -> dict[str, object]:
    acquire_organization_tree_lock(db)
    deleted = organization_service.delete_organization(db, organization_id)
    return _complete_write(
        db, actor, deleted, action="organization.delete", method="DELETE",
        path=f"/api/organizations/{organization_id}", key=None, request_body={},
        status=200,
    )
