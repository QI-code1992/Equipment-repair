from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.idempotency import find_idempotent_response, save_idempotent_response
from app.modules.audit.service import write_audit_event
from app.modules.identity.dependencies import require_permission
from app.modules.identity.models import User
from app.modules.maintenance import service
from app.modules.maintenance.models import FaultReport
from app.modules.maintenance.schemas import FaultReportCreate


router = APIRouter(tags=["maintenance"])


def fault_report_body(item: FaultReport) -> dict[str, object]:
    return {
        "id": item.id,
        "number": item.number,
        "equipment_id": item.equipment_id,
        "organization_snapshot": item.organization_snapshot,
        "urgency": item.urgency,
        "symptom": item.symptom,
        "occurred_at": item.occurred_at.isoformat(),
        "possible_location": item.possible_location,
        "description": item.description,
        "attachment_refs": item.attachment_refs,
        "status": item.status.value,
        "submitter_id": item.submitter_id,
        "submitted_at": item.submitted_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
    }


@router.post(
    "/api/fault-reports",
    status_code=201,
    response_model=None,
    name="fault_report.create",
)
def create_fault_report(
    payload: FaultReportCreate,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("fault:create")),
) -> dict[str, object] | JSONResponse:
    path = "/api/fault-reports"
    request_body = payload.model_dump(mode="json")
    replay = find_idempotent_response(
        db,
        user_id=actor.id,
        method="POST",
        path=path,
        key=idempotency_key,
        request_body=request_body,
    )
    if replay is not None:
        return JSONResponse(status_code=replay[0], content=replay[1])

    item = service.create_fault_report(db, payload, submitter_id=actor.id)
    event = write_audit_event(
        db,
        actor_user_id=actor.id,
        action="fault_report.create",
        resource_type="fault_report",
        resource_id=item.id,
        result="success",
        metadata=request_body,
    )
    body = {**fault_report_body(item), "audit_event_id": event.id}
    save_idempotent_response(
        db,
        user_id=actor.id,
        method="POST",
        path=path,
        key=idempotency_key,
        request_body=request_body,
        status=201,
        body=body,
    )
    db.commit()
    return body
