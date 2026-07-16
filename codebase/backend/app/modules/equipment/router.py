from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.idempotency import find_idempotent_response, save_idempotent_response
from app.modules.audit.service import write_audit_event
from app.modules.equipment.models import Equipment, EquipmentStatus, Organization
from app.modules.identity.dependencies import require_permission
from app.modules.identity.models import User


router = APIRouter(prefix="/api/equipment", tags=["equipment"])


class EquipmentCreate(BaseModel):
    code: str
    name: str
    organization_id: str | None = None


class EquipmentUpdate(BaseModel):
    name: str
    organization_id: str | None
    status: EquipmentStatus


@router.get("")
def list_equipment(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("equipment:read")),
) -> list[dict[str, object]]:
    del user
    equipment = db.scalars(select(Equipment).order_by(Equipment.code)).all()
    return [
        {
            "id": item.id,
            "code": item.code,
            "name": item.name,
            "organization_id": item.organization_id,
            "status": item.status.value,
        }
        for item in equipment
    ]


@router.post("", status_code=201, response_model=None)
def create_equipment(
    payload: EquipmentCreate,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("equipment:write")),
) -> dict[str, object] | JSONResponse:
    request_body = payload.model_dump(mode="json")
    replay = find_idempotent_response(
        db,
        user_id=user.id,
        method="POST",
        path="/api/equipment",
        key=idempotency_key,
        request_body=request_body,
    )
    if replay is not None:
        status, body = replay
        return JSONResponse(status_code=status, content=body)

    if db.scalar(select(Equipment).where(Equipment.code == payload.code)) is not None:
        raise HTTPException(status_code=409, detail={"code": "EQUIPMENT_CODE_EXISTS"})
    if payload.organization_id is not None and db.get(Organization, payload.organization_id) is None:
        raise HTTPException(status_code=404, detail={"code": "ORGANIZATION_NOT_FOUND"})

    item = Equipment(**payload.model_dump())
    db.add(item)
    try:
        db.flush()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=409, detail={"code": "EQUIPMENT_CODE_EXISTS"}
        ) from error
    event = write_audit_event(
        db,
        actor_user_id=user.id,
        action="equipment.create",
        resource_type="equipment",
        resource_id=item.id,
        result="success",
        metadata=request_body,
    )
    body: dict[str, object] = {
        "id": item.id,
        "code": item.code,
        "name": item.name,
        "organization_id": item.organization_id,
        "status": item.status.value,
        "audit_event_id": event.id,
    }
    save_idempotent_response(
        db,
        user_id=user.id,
        method="POST",
        path="/api/equipment",
        key=idempotency_key,
        request_body=request_body,
        status=201,
        body=body,
    )
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=409, detail={"code": "EQUIPMENT_CODE_EXISTS"}
        ) from error
    return body


@router.patch("/{equipment_id}", response_model=None)
def update_equipment(
    equipment_id: str,
    payload: EquipmentUpdate,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("equipment:write")),
) -> dict[str, object] | JSONResponse:
    path = f"/api/equipment/{equipment_id}"
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
    item = db.get(Equipment, equipment_id)
    if item is None:
        raise HTTPException(status_code=404, detail={"code": "EQUIPMENT_NOT_FOUND"})
    if payload.organization_id is not None and db.get(Organization, payload.organization_id) is None:
        raise HTTPException(status_code=404, detail={"code": "ORGANIZATION_NOT_FOUND"})

    item.name = payload.name
    item.organization_id = payload.organization_id
    item.status = payload.status
    event = write_audit_event(
        db,
        actor_user_id=user.id,
        action="equipment.update",
        resource_type="equipment",
        resource_id=item.id,
        result="success",
        metadata=request_body,
    )
    body: dict[str, object] = {
        "id": item.id,
        "code": item.code,
        "name": item.name,
        "organization_id": item.organization_id,
        "status": item.status.value,
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
