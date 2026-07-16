from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.idempotency import find_idempotent_response, save_idempotent_response
from app.modules.audit.service import write_audit_event
from app.modules.equipment.models import Organization
from app.modules.identity.dependencies import require_permission
from app.modules.identity.models import User


router = APIRouter(prefix="/api/organizations", tags=["organizations"])
ORGANIZATION_TREE_LOCK_ID = 824003


class OrganizationCreate(BaseModel):
    name: str
    parent_id: str | None = None


class OrganizationUpdate(BaseModel):
    name: str
    parent_id: str | None


def acquire_organization_tree_lock(db: Session) -> None:
    if db.get_bind().dialect.name == "postgresql":
        db.execute(
            text("SELECT pg_advisory_xact_lock(:lock_id)"),
            {"lock_id": ORGANIZATION_TREE_LOCK_ID},
        )


def validate_parent(
    db: Session, parent_id: str | None, *, descendant_id: str | None = None
) -> None:
    current_id = parent_id
    visited: set[str] = set()
    while current_id is not None:
        if current_id == descendant_id or current_id in visited:
            raise HTTPException(
                status_code=422, detail={"code": "ORGANIZATION_PARENT_INVALID"}
            )
        visited.add(current_id)
        parent = db.get(Organization, current_id)
        if parent is None:
            raise HTTPException(
                status_code=404, detail={"code": "ORGANIZATION_PARENT_NOT_FOUND"}
            )
        current_id = parent.parent_id


@router.get("")
def list_organizations(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("organization:read")),
) -> list[dict[str, object]]:
    del user
    organizations = db.scalars(select(Organization).order_by(Organization.name)).all()
    return [{"id": item.id, "name": item.name, "parent_id": item.parent_id} for item in organizations]


@router.post("", status_code=201, response_model=None, name="organization.create")
def create_organization(
    payload: OrganizationCreate,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("organization:write")),
) -> dict[str, object] | JSONResponse:
    request_body = payload.model_dump(mode="json")
    replay = find_idempotent_response(
        db,
        user_id=user.id,
        method="POST",
        path="/api/organizations",
        key=idempotency_key,
        request_body=request_body,
    )
    if replay is not None:
        status, body = replay
        return JSONResponse(status_code=status, content=body)
    acquire_organization_tree_lock(db)
    validate_parent(db, payload.parent_id)

    organization = Organization(**payload.model_dump())
    db.add(organization)
    db.flush()
    event = write_audit_event(
        db,
        actor_user_id=user.id,
        action="organization.create",
        resource_type="organization",
        resource_id=organization.id,
        result="success",
        metadata=request_body,
    )
    body: dict[str, object] = {
        "id": organization.id,
        "name": organization.name,
        "parent_id": organization.parent_id,
        "audit_event_id": event.id,
    }
    save_idempotent_response(
        db,
        user_id=user.id,
        method="POST",
        path="/api/organizations",
        key=idempotency_key,
        request_body=request_body,
        status=201,
        body=body,
    )
    db.commit()
    return body


@router.patch(
    "/{organization_id}", response_model=None, name="organization.update"
)
def update_organization(
    organization_id: str,
    payload: OrganizationUpdate,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("organization:write")),
) -> dict[str, object] | JSONResponse:
    path = f"/api/organizations/{organization_id}"
    request_body = payload.model_dump(mode="json")
    replay = find_idempotent_response(
        db,
        user_id=user.id,
        method="PATCH",
        path=path,
        key=idempotency_key,
        request_body=request_body,
    )
    if replay is not None:
        status, body = replay
        return JSONResponse(status_code=status, content=body)
    acquire_organization_tree_lock(db)
    organization = db.get(Organization, organization_id)
    if organization is None:
        raise HTTPException(status_code=404, detail={"code": "ORGANIZATION_NOT_FOUND"})
    validate_parent(db, payload.parent_id, descendant_id=organization.id)

    organization.name = payload.name
    organization.parent_id = payload.parent_id
    event = write_audit_event(
        db,
        actor_user_id=user.id,
        action="organization.update",
        resource_type="organization",
        resource_id=organization.id,
        result="success",
        metadata=request_body,
    )
    body: dict[str, object] = {
        "id": organization.id,
        "name": organization.name,
        "parent_id": organization.parent_id,
        "audit_event_id": event.id,
    }
    save_idempotent_response(
        db,
        user_id=user.id,
        method="PATCH",
        path=path,
        key=idempotency_key,
        request_body=request_body,
        status=200,
        body=body,
    )
    db.commit()
    return body
