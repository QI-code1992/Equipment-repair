from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.idempotency import find_idempotent_response, save_idempotent_response
from app.modules.audit.service import write_audit_event
from app.modules.equipment.models import Organization
from app.modules.identity.dependencies import require_permission
from app.modules.identity.models import User


router = APIRouter(prefix="/api/organizations", tags=["organizations"])


class OrganizationCreate(BaseModel):
    name: str
    parent_id: str | None = None


@router.get("")
def list_organizations(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("organization:read")),
) -> list[dict[str, object]]:
    del user
    organizations = db.scalars(select(Organization).order_by(Organization.name)).all()
    return [{"id": item.id, "name": item.name, "parent_id": item.parent_id} for item in organizations]


@router.post("", status_code=201, response_model=None)
def create_organization(
    payload: OrganizationCreate,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("organization:write")),
) -> dict[str, object] | JSONResponse:
    replay = find_idempotent_response(
        db,
        user_id=user.id,
        method="POST",
        path="/api/organizations",
        key=idempotency_key,
    )
    if replay is not None:
        status, body = replay
        return JSONResponse(status_code=status, content=body)
    if payload.parent_id is not None and db.get(Organization, payload.parent_id) is None:
        raise HTTPException(status_code=404, detail={"code": "ORGANIZATION_PARENT_NOT_FOUND"})

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
        metadata=payload.model_dump(),
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
        status=201,
        body=body,
    )
    db.commit()
    return body
