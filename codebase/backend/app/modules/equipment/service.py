from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.equipment.models import (
    Equipment,
    EquipmentStatus,
    Organization,
    OrganizationType,
)
from app.modules.equipment.schemas import EquipmentWrite
from app.modules.identity.models import User
from app.modules.maintenance.models import FaultReport, FaultStatus


def _error(status_code: int, code: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code})


def equipment_items(db: Session) -> list[Equipment]:
    return list(db.scalars(select(Equipment).order_by(Equipment.code, Equipment.id)))


def equipment_detail(db: Session, equipment_id: str) -> Equipment:
    item = db.get(Equipment, equipment_id)
    if item is None:
        raise _error(404, "EQUIPMENT_NOT_FOUND")
    return item


def _locked_equipment(db: Session, equipment_id: str) -> Equipment:
    statement = select(Equipment).where(Equipment.id == equipment_id)
    if db.get_bind().dialect.name == "postgresql":
        statement = statement.with_for_update()
    item = db.scalar(statement)
    if item is None:
        raise _error(404, "EQUIPMENT_NOT_FOUND")
    return item


def _has_active_fault(db: Session, equipment_id: str) -> bool:
    return db.scalar(
        select(FaultReport.id)
        .where(
            FaultReport.equipment_id == equipment_id,
            FaultReport.status.in_(
                [FaultStatus.PENDING_ACCEPT, FaultStatus.IN_REPAIR]
            ),
        )
        .limit(1)
    ) is not None


def equipment_code_exists(
    db: Session, code: str, *, exclude_id: str | None = None
) -> bool:
    item = db.scalar(select(Equipment).where(Equipment.code == code))
    return item is not None and item.id != exclude_id


def _validate_references(db: Session, payload: EquipmentWrite) -> None:
    organization = db.get(Organization, payload.organization_id)
    if organization is None:
        raise _error(404, "EQUIPMENT_ORGANIZATION_NOT_FOUND")
    if organization.type != OrganizationType.LINE:
        raise _error(409, "EQUIPMENT_ORGANIZATION_NOT_LINE")
    if not organization.enabled:
        raise _error(409, "EQUIPMENT_ORGANIZATION_DISABLED")
    if payload.owner_user_id is None:
        return
    owner = db.get(User, payload.owner_user_id)
    if owner is None:
        raise _error(404, "EQUIPMENT_OWNER_NOT_FOUND")
    if not owner.enabled:
        raise _error(409, "EQUIPMENT_OWNER_DISABLED")


def _flush(db: Session) -> None:
    try:
        db.flush()
    except IntegrityError as error:
        db.rollback()
        diagnostic = getattr(error.orig, "diag", None)
        constraint = str(getattr(diagnostic, "constraint_name", "") or "").lower()
        message = str(error.orig).lower()
        duplicate_code = (
            ("equipment" in constraint and "code" in constraint)
            or ("unique" in message and "equipment.code" in message)
        )
        code = "EQUIPMENT_CODE_EXISTS" if duplicate_code else "EQUIPMENT_CONFLICT"
        raise _error(409, code) from error


def _values(payload: EquipmentWrite) -> dict[str, object]:
    values = payload.model_dump()
    values["image_refs"] = [reference.model_dump() for reference in payload.image_refs]
    return values


def create_equipment(db: Session, payload: EquipmentWrite) -> Equipment:
    if equipment_code_exists(db, payload.code):
        raise _error(409, "EQUIPMENT_CODE_EXISTS")
    _validate_references(db, payload)
    item = Equipment(**_values(payload))
    db.add(item)
    _flush(db)
    return item


def update_equipment(
    db: Session, equipment_id: str, payload: EquipmentWrite
) -> Equipment:
    item = _locked_equipment(db, equipment_id)
    if (
        payload.status is EquipmentStatus.DISABLED
        and _has_active_fault(db, equipment_id)
    ):
        raise _error(409, "EQUIPMENT_ACTIVE_FAULT")
    if equipment_code_exists(db, payload.code, exclude_id=item.id):
        raise _error(409, "EQUIPMENT_CODE_EXISTS")
    _validate_references(db, payload)
    for field, value in _values(payload).items():
        setattr(item, field, value)
    _flush(db)
    return item
