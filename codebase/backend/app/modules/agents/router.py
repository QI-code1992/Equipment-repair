from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Header
from fastapi.responses import JSONResponse

from app.modules.agents.metric_query import (
    HealthScoreReader,
    InvalidMetricQueryError,
    METRIC_CATALOG,
    MetricQuery,
    MetricQueryService,
    ServiceUnavailableError,
)
from app.core.idempotency import (
    IdempotencyKeyReused,
    find_idempotent_response,
    save_idempotent_response,
)
from app.core.database import get_db
from app.modules.audit.service import write_audit_event
from app.modules.identity.dependencies import require_permission
from app.modules.identity.models import User
from app.modules.maintenance import service as maintenance_service
from app.modules.maintenance.router import fault_report_body
from app.modules.maintenance.schemas import FaultReportCreate
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from app.modules.agents.fault_reporting import (
    FaultDraft,
    FaultReportingAgent,
    MissingFaultFieldsError,
    SubmissionNotConfirmedError,
)


router = APIRouter(tags=["agents"])


def _default_metric_service() -> MetricQueryService:
    def unavailable(_: MetricQuery) -> list[dict[str, Any]]:
        raise ServiceUnavailableError("metrics service unavailable")

    return MetricQueryService(unavailable)


def _default_health_reader() -> HealthScoreReader:
    def unavailable(_: str) -> dict[str, Any]:
        raise ServiceUnavailableError("health score service unavailable")

    return HealthScoreReader(unavailable)


class FaultSubmissionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    draft: FaultDraft
    confirmed: bool


@router.get("/api/metrics/catalog")
def metric_catalog(_: User = Depends(require_permission("equipment:read"))) -> list[dict[str, Any]]:
    return [item.model_dump(mode="json") for item in METRIC_CATALOG]


@router.post("/api/metrics/query-batch", response_model=None)
def query_metrics(
    payload: MetricQuery,
    request: Request,
    _: User = Depends(require_permission("equipment:read")),
) -> dict[str, Any] | JSONResponse:
    service = getattr(request.app.state, "metric_query_service", None) or _default_metric_service()
    try:
        result = service.query(payload)
    except InvalidMetricQueryError as error:
        raise HTTPException(status_code=422, detail={"code": "INVALID_METRIC_QUERY", "message": str(error)}) from error
    if result["status"] == "UNAVAILABLE":
        return JSONResponse(status_code=503, content=result)
    return result


@router.post("/api/agent/fault-reports/submit", status_code=201, response_model=None)
def submit_fault_report(
    payload: FaultSubmissionRequest,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("fault:create")),
) -> dict[str, Any] | JSONResponse:
    path = "/api/agent/fault-reports/submit"
    request_body = payload.model_dump(mode="json")
    try:
        replay = find_idempotent_response(
            db, user_id=actor.id, method="POST", path=path,
            key=idempotency_key, request_body=request_body,
        )
    except IdempotencyKeyReused:
        raise HTTPException(
            status_code=409, detail={"code": "IDEMPOTENCY_KEY_REUSED"}
        ) from None
    if replay is not None:
        return JSONResponse(status_code=replay[0], content=replay[1])

    created = []

    def submitter(draft: FaultDraft) -> str:
        item = maintenance_service.create_fault_report(
            db,
            FaultReportCreate(
                equipment_id=draft.equipment_id,
                urgency=draft.urgency,
                symptom=draft.symptom,
                occurred_at=draft.occurred_at,
                possible_location=draft.possible_location,
                description=draft.description,
                attachment_refs=draft.attachment_refs,
            ),
            submitter_id=actor.id,
        )
        created.append(item)
        return item.id

    agent = FaultReportingAgent(submitter)
    try:
        preview = agent.preview(payload.draft)
        result = agent.submit(preview, confirmed=payload.confirmed)
    except MissingFaultFieldsError as error:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "FAULT_DRAFT_INCOMPLETE",
                "fields": {field: "required" for field in error.fields},
            },
        ) from None
    except SubmissionNotConfirmedError as error:
        raise HTTPException(status_code=409, detail={"code": "CONFIRMATION_REQUIRED"}) from error
    item = created[0]
    event = write_audit_event(
        db, actor_user_id=actor.id, action="agent.fault_report.submit",
        resource_type="fault_report", resource_id=item.id, result="success",
        metadata={"fault_report_id": item.id},
    )
    body = {**fault_report_body(item), "audit_event_id": event.id, "agent_status": result["status"]}
    save_idempotent_response(
        db, user_id=actor.id, method="POST", path=path, key=idempotency_key,
        request_body=request_body, status=201, body=body,
    )
    db.commit()
    return body


@router.get("/api/agent/health-score/{equipment_id}", response_model=None)
def read_health_score(
    equipment_id: str,
    request: Request,
    _: User = Depends(require_permission("intelligence:agent")),
) -> dict[str, Any] | JSONResponse:
    reader = getattr(request.app.state, "health_score_reader", None) or _default_health_reader()
    result = reader.read(equipment_id)
    if result["status"] == "UNAVAILABLE":
        return JSONResponse(status_code=503, content=result)
    return result
