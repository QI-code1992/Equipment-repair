from decimal import Decimal

from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.idempotency import find_idempotent_response, save_idempotent_response
from app.modules.audit.service import write_audit_event
from app.modules.equipment import service
from app.modules.equipment.models import Equipment
from app.modules.equipment.organization_service import acquire_organization_tree_lock
from app.modules.equipment.schemas import EquipmentRead, EquipmentWrite, EquipmentWriteResponse
from app.modules.identity.dependencies import require_permission
from app.modules.identity.models import User


router = APIRouter(prefix="/api/equipment", tags=["equipment"])


def _number(value: Decimal) -> int | float:
    return int(value) if value == value.to_integral() else float(value)


def equipment_body(item: Equipment) -> dict[str, object]:
    return {
        "id": item.id,
        "code": item.code,
        "name": item.name,
        "model": item.model,
        "type": item.type,
        "manufacturer": item.manufacturer,
        "manufactured_at": item.manufactured_at.isoformat() if item.manufactured_at else None,
        "commissioned_at": item.commissioned_at.isoformat() if item.commissioned_at else None,
        "operating_hours": _number(item.operating_hours),
        "status": item.status.value,
        "organization_id": item.organization_id,
        "owner_user_id": item.owner_user_id,
        "image_refs": item.image_refs,
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
    }


def _replay(
    db: Session, actor: User, method: str, path: str, key: str, body: object
) -> JSONResponse | None:
    result = find_idempotent_response(
        db, user_id=actor.id, method=method, path=path, key=key, request_body=body
    )
    if result is None:
        return None
    return JSONResponse(status_code=result[0], content=result[1])


def _complete_write(
    db: Session, actor: User, item: Equipment, *, action: str, method: str,
    path: str, key: str, request_body: object, status: int,
) -> dict[str, object]:
    event = write_audit_event(
        db, actor_user_id=actor.id, action=action, resource_type="equipment",
        resource_id=item.id, result="success", metadata=request_body,
    )
    body = {**equipment_body(item), "audit_event_id": event.id}
    save_idempotent_response(
        db, user_id=actor.id, method=method, path=path, key=key,
        request_body=request_body, status=status, body=body,
    )
    db.commit()
    return body


@router.get(
    "", response_model=None, responses={200: {"model": list[EquipmentRead]}}
)
def list_equipment(
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("equipment:read")),
) -> list[dict[str, object]]:
    del actor
    return [equipment_body(item) for item in service.equipment_items(db)]


@router.get(
    "/{equipment_id}", response_model=None, responses={200: {"model": EquipmentRead}}
)
def get_equipment(
    equipment_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("equipment:read")),
) -> dict[str, object]:
    del actor
    return equipment_body(service.equipment_detail(db, equipment_id))


@router.post(
    "",
    status_code=201,
    response_model=None,
    responses={201: {"model": EquipmentWriteResponse}},
    name="equipment.create",
)
def create_equipment(
    payload: EquipmentWrite,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("equipment:write")),
) -> dict[str, object] | JSONResponse:
    acquire_organization_tree_lock(db)
    request_body = payload.model_dump(mode="json")
    replay = _replay(db, actor, "POST", "/api/equipment", idempotency_key, request_body)
    if replay is not None:
        return replay
    item = service.create_equipment(db, payload)
    return _complete_write(
        db, actor, item, action="equipment.create", method="POST",
        path="/api/equipment", key=idempotency_key, request_body=request_body, status=201,
    )


@router.patch(
    "/{equipment_id}",
    response_model=None,
    responses={200: {"model": EquipmentWriteResponse}},
    name="equipment.update",
)
def update_equipment(
    equipment_id: str,
    payload: EquipmentWrite,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("equipment:write")),
) -> dict[str, object] | JSONResponse:
    acquire_organization_tree_lock(db)
    path = f"/api/equipment/{equipment_id}"
    request_body = payload.model_dump(mode="json")
    replay = _replay(db, actor, "PATCH", path, idempotency_key, request_body)
    if replay is not None:
        return replay
    item = service.update_equipment(db, equipment_id, payload)
    return _complete_write(
        db, actor, item, action="equipment.update", method="PATCH", path=path,
        key=idempotency_key, request_body=request_body, status=200,
    )
