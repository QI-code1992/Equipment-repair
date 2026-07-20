from datetime import UTC, datetime
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.equipment.models import Equipment, EquipmentStatus, Organization
from app.modules.maintenance.models import FaultReport
from app.modules.maintenance.schemas import FaultReportCreate


def _error(
    status_code: int,
    code: str,
    *,
    fields: dict[str, str] | None = None,
) -> HTTPException:
    detail: dict[str, object] = {"code": code}
    if fields:
        detail["fields"] = fields
    return HTTPException(status_code=status_code, detail=detail)


def _locked_equipment(db: Session, equipment_id: str) -> Equipment:
    statement = select(Equipment).where(Equipment.id == equipment_id)
    if db.get_bind().dialect.name == "postgresql":
        statement = statement.with_for_update()
    equipment = db.scalar(statement)
    if equipment is None:
        raise _error(404, "FAULT_EQUIPMENT_NOT_FOUND")
    return equipment


def _organization_snapshot(db: Session, line_id: str) -> dict[str, object]:
    line = db.get(Organization, line_id)
    if line is None:
        raise _error(409, "FAULT_ORGANIZATION_NOT_FOUND")
    workshop = None if line.parent_id is None else db.get(Organization, line.parent_id)
    factory = (
        None
        if workshop is None or workshop.parent_id is None
        else db.get(Organization, workshop.parent_id)
    )

    def item(organization: Organization | None) -> dict[str, str] | None:
        if organization is None:
            return None
        return {
            "id": organization.id,
            "code": organization.code,
            "name": organization.name,
        }

    return {"factory": item(factory), "workshop": item(workshop), "line": item(line)}


def create_fault_report(
    db: Session,
    payload: FaultReportCreate,
    *,
    submitter_id: str,
) -> FaultReport:
    equipment = _locked_equipment(db, payload.equipment_id)
    if equipment.status is EquipmentStatus.DISABLED:
        raise _error(409, "FAULT_EQUIPMENT_DISABLED")
    if payload.occurred_at > datetime.now(UTC):
        raise _error(
            422,
            "FAULT_OCCURRENCE_IN_FUTURE",
            fields={"occurred_at": "future"},
        )

    item = FaultReport(
        number=f"FR-{datetime.now(UTC):%Y%m%d}-{uuid4().hex[:12].upper()}",
        equipment_id=equipment.id,
        organization_snapshot=_organization_snapshot(db, equipment.organization_id),
        urgency=payload.urgency,
        symptom=payload.symptom,
        occurred_at=payload.occurred_at,
        possible_location=payload.possible_location,
        description=payload.description,
        attachment_refs=[reference.model_dump() for reference in payload.attachment_refs],
        submitter_id=submitter_id,
    )
    if equipment.status is EquipmentStatus.NORMAL:
        equipment.status = EquipmentStatus.FAULT
    db.add(item)
    db.flush()
    return item
