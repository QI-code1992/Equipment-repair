from dataclasses import replace
from typing import Any, Literal

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
from app.modules.agent_config.domain import AgentId
from app.modules.agent_config.models import AgentConfigModel
from app.modules.audit.service import write_audit_event
from app.modules.identity.dependencies import require_permission
from app.modules.identity.models import User
from app.modules.maintenance import service as maintenance_service
from app.modules.maintenance.models import DiagnosisDraft, DiagnosisDraftStatus, FaultReport
from app.modules.equipment.models import Equipment
from app.modules.maintenance.schemas import SimilarCaseQuery
from app.modules.knowledge import service as knowledge_service
from app.modules.maintenance.router import fault_report_body
from app.modules.notifications.service import add_health_notification_if_band_changed, add_notification
from app.modules.maintenance.schemas import FaultReportCreate
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.modules.agents.fault_reporting import (
    FaultDraft,
    FaultReportingAgent,
    MissingFaultFieldsError,
    SubmissionNotConfirmedError,
)
from app.modules.agents.operation_guidance import (
    GuidanceContext,
    GuidanceSession,
    OperationGuidanceAgent,
)
from app.modules.agents.fault_diagnosis import (
    DiagnosisContext,
    DiagnosisState,
    DiagnosisSession,
    Evidence,
    FaultDiagnosisAgent,
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


class OperationGuidanceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    equipment_id: str
    equipment_model: str
    symptom: str
    description: str
    dataset_ids: list[str] = Field(default_factory=list)


class DiagnosisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["start", "answer", "evidence"] = "start"
    fault_report_id: str | None = None
    alarm_code_present: bool = False
    diagnosis_draft_id: str | None = None
    answer: str | None = None
    category: str | None = None
    detail: str | None = None


def _guidance_references(db: Session, request: Request, context: GuidanceContext, dataset_ids: list[str]) -> list[dict[str, str]]:
    adapter = getattr(request.app.state, "knowledge_adapter", None)
    if adapter is None or not dataset_ids:
        raise ConnectionError("knowledge service unavailable")
    result = knowledge_service.retrieve_knowledge(
        db, f"{context.equipment_model} {context.symptom} {context.description}", dataset_ids, adapter
    )
    if result.unavailable:
        raise ConnectionError("knowledge service unavailable")
    return [
        {
            "document_id": item.business_document_id,
            "chunk_id": item.chunk_id,
            "citation": item.chunk_id,
            "text": item.content,
        }
        for item in result.citations
    ]


def _guidance_body(session: GuidanceSession) -> dict[str, Any]:
    return {
        "state": session.state.value,
        "question": session.question,
        "evidence": [
            {
                "document_id": item.document_id,
                "chunk_id": item.chunk_id,
                "citation": item.citation,
                "text": item.text,
            }
            for item in session.evidence
        ],
        "retrieval_count": session.retrieval_count,
        "manual_fallback": session.manual_fallback,
        "loading_seconds": session.loading_seconds,
    }


def _diagnosis_body(session: DiagnosisSession, draft_id: str | None = None) -> dict[str, Any]:
    return {
        "state": session.state.value,
        "question": session.question,
        "evidence": [{"category": item.category, "detail": item.detail} for item in session.evidence],
        "prefill": session.prefill,
        "summary": session.summary,
        "steps": session.steps,
        "questions": session.questions,
        "diagnosis_draft_id": draft_id,
    }


def _session_state(session: DiagnosisSession, dataset_ids: list[str]) -> dict[str, Any]:
    return {
        "fault_report_id": session.context.fault_report_id,
        "equipment_model": session.context.equipment_model,
        "symptom": session.context.symptom,
        "description": session.context.description,
        "alarm_code_present": session.context.alarm_code_present,
        "state": session.state.value,
        "question": session.question,
        "evidence": [{"category": item.category, "detail": item.detail} for item in session.evidence],
        "prefill": session.prefill,
        "summary": session.summary,
        "steps": session.steps,
        "questions": session.questions,
        "dataset_ids": dataset_ids,
    }


def _restore_diagnosis_session(raw: dict[str, Any]) -> DiagnosisSession:
    context = DiagnosisContext(
        fault_report_id=str(raw["fault_report_id"]),
        equipment_model=str(raw["equipment_model"]),
        symptom=str(raw["symptom"]),
        description=str(raw["description"]),
        alarm_code_present=bool(raw.get("alarm_code_present", False)),
    )
    return DiagnosisSession(
        context=context,
        state=DiagnosisState(raw["state"]),
        question=raw.get("question"),
        evidence=tuple(Evidence(**item) for item in raw.get("evidence", [])),
        prefill=raw.get("prefill"),
        summary=raw.get("summary"),
        steps=int(raw.get("steps", 0)),
        questions=int(raw.get("questions", 0)),
    )


def _fault_diagnosis_dataset_ids(db: Session) -> list[str]:
    return _configured_dataset_ids(db, AgentId.FAULT_DIAGNOSIS)


def _configured_dataset_ids(db: Session, agent_id: AgentId) -> list[str]:
    config = db.scalar(
        select(AgentConfigModel).where(AgentConfigModel.agent_id == agent_id.value)
    )
    if config is None or not config.enabled:
        return []
    return list(config.knowledge_dataset_ids)


def _server_diagnosis_context(
    fault: FaultReport, equipment: Equipment, *, alarm_code_present: bool
) -> DiagnosisContext:
    return DiagnosisContext(
        fault_report_id=fault.id,
        equipment_model=equipment.model,
        symptom=fault.symptom,
        description=fault.description or "",
        alarm_code_present=alarm_code_present,
    )


@router.post("/api/agent/operation-guidance", response_model=None)
def operation_guidance(
    payload: OperationGuidanceRequest,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("intelligence:agent")),
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
) -> dict[str, Any]:
    path = "/api/agent/operation-guidance"
    request_body = payload.model_dump(mode="json")
    try:
        replay = find_idempotent_response(
            db, user_id=actor.id, method="POST", path=path,
            key=idempotency_key, request_body=request_body,
        )
    except IdempotencyKeyReused:
        raise HTTPException(status_code=409, detail={"code": "IDEMPOTENCY_KEY_REUSED"}) from None
    if replay is not None:
        return replay[1]
    context = GuidanceContext(
        equipment_id=payload.equipment_id,
        equipment_model=payload.equipment_model,
        symptom=payload.symptom,
        description=payload.description,
    )
    dataset_ids = _configured_dataset_ids(db, AgentId.OPERATION_GUIDANCE)
    agent = OperationGuidanceAgent(
        lambda query: _guidance_references(
            db, request, context, dataset_ids
        )
    )
    session = agent.start(context)
    write_audit_event(
        db, actor_user_id=actor.id, action="agent.operation_guidance.start",
        resource_type="equipment", resource_id=context.equipment_id,
        result="success" if session.state.value != "UNAVAILABLE" else "unavailable",
        metadata={"retrieval_count": session.retrieval_count, "state": session.state.value},
    )
    response = _guidance_body(session)
    save_idempotent_response(
        db, user_id=actor.id, method="POST", path=path,
        key=idempotency_key, request_body=request_body, status=200, body=response,
    )
    db.commit()
    return response


@router.post("/api/agent/fault-diagnosis", response_model=None)
def fault_diagnosis(
    payload: DiagnosisRequest,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("intelligence:agent")),
    _: User = Depends(require_permission("fault:repair")),
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
) -> dict[str, Any]:
    path = "/api/agent/fault-diagnosis"
    request_body = payload.model_dump(mode="json")
    try:
        replay = find_idempotent_response(
            db, user_id=actor.id, method="POST", path=path,
            key=idempotency_key, request_body=request_body,
        )
    except IdempotencyKeyReused:
        raise HTTPException(status_code=409, detail={"code": "IDEMPOTENCY_KEY_REUSED"}) from None
    if replay is not None:
        return replay[1]

    if payload.action == "start":
        if not payload.fault_report_id:
            raise HTTPException(status_code=422, detail={"code": "DIAGNOSIS_CONTEXT_REQUIRED"})
        fault = db.get(FaultReport, payload.fault_report_id)
        if fault is None:
            raise HTTPException(status_code=404, detail={"code": "FAULT_REPORT_NOT_FOUND"})
        equipment = db.get(Equipment, fault.equipment_id)
        if equipment is None:
            raise HTTPException(status_code=404, detail={"code": "EQUIPMENT_NOT_FOUND"})
        context = _server_diagnosis_context(
            fault, equipment, alarm_code_present=payload.alarm_code_present
        )
        request_dataset_ids = _fault_diagnosis_dataset_ids(db)
    else:
        if not payload.diagnosis_draft_id:
            raise HTTPException(status_code=422, detail={"code": "DIAGNOSIS_DRAFT_REQUIRED"})
        draft = db.get(DiagnosisDraft, payload.diagnosis_draft_id)
        raw = None if draft is None else (draft.read_only_summary or {}).get("_session")
        owner = None if draft is None else (draft.read_only_summary or {}).get("_owner_user_id")
        if draft is None or not isinstance(raw, dict):
            raise HTTPException(status_code=404, detail={"code": "DIAGNOSIS_DRAFT_NOT_FOUND"})
        if owner != actor.id:
            raise HTTPException(status_code=403, detail={"code": "DIAGNOSIS_DRAFT_ACCESS_DENIED"})
        if draft.status == DiagnosisDraftStatus.DIAGNOSIS_READY:
            response = _diagnosis_body(_restore_diagnosis_session(raw), draft.id)
            save_idempotent_response(
                db, user_id=actor.id, method="POST", path=path,
                key=idempotency_key, request_body=request_body, status=200, body=response,
            )
            db.commit()
            return response
        context = _restore_diagnosis_session(raw).context
        request_dataset_ids = list(raw.get("dataset_ids", []))
        fault = db.get(FaultReport, context.fault_report_id)
        if fault is None:
            raise HTTPException(status_code=404, detail={"code": "FAULT_REPORT_NOT_FOUND"})
        equipment = db.get(Equipment, fault.equipment_id)
        if equipment is None:
            raise HTTPException(status_code=404, detail={"code": "EQUIPMENT_NOT_FOUND"})

    case_items: list[dict[str, Any]] = []
    knowledge_items: list[dict[str, Any]] = []

    def case_retrieve(_: DiagnosisContext) -> list[dict[str, Any]]:
        query = SimilarCaseQuery(
            equipment_type=equipment.type,
            equipment_model=equipment.model,
            symptom=context.symptom,
            limit=4,
        )
        case_items[:] = [
            {
                "case_id": item.id,
                "actual_cause": item.actual_cause,
                "actual_solution": item.actual_solution,
                "repair_result": item.repair_result,
            }
            for item in maintenance_service.find_similar_cases(db, query)
        ]
        return case_items

    def knowledge_retrieve(_: DiagnosisContext) -> list[dict[str, Any]]:
        knowledge_items[:] = _guidance_references(db, request, context, request_dataset_ids)
        return knowledge_items

    def analyze(_: DiagnosisContext, evidence: tuple[Evidence, ...]) -> dict[str, Any]:
        case = case_items[0] if case_items else {}
        root_cause = str(case.get("actual_cause") or "候选根因需人工确认")
        recommendations = str(
            case.get("actual_solution")
            or (knowledge_items[0].get("text") if knowledge_items else "按已收集证据执行人工检查清单")
        )
        return {
            "root_cause": root_cause,
            "recommendations": recommendations,
            "safety_notes": ["高风险系统先停机并执行安全检查"],
        }

    agent = FaultDiagnosisAgent(case_retrieve, knowledge_retrieve, analyze=analyze)
    if payload.action == "start":
        session = agent.start(context)
        draft = DiagnosisDraft(
            fault_report_id=fault.id,
            status=DiagnosisDraftStatus.DRAFT,
            read_only_summary={
                "_owner_user_id": actor.id,
                "_session": _session_state(session, request_dataset_ids),
            },
        )
        db.add(draft)
        db.flush()
    else:
        session = _restore_diagnosis_session(raw)
        case_retrieve(context)
        knowledge_retrieve(context)
        if payload.action == "answer":
            session = agent.answer(session, payload.answer or "")
        else:
            session = agent.add_evidence(session, payload.category or "", payload.detail or "")

    if session.state is DiagnosisState.DIAGNOSIS_READY and not case_items and not knowledge_items:
        session = replace(
            session,
            state=DiagnosisState.EVIDENCE_PENDING,
            question="未检索到可引用的案例或知识依据，不能生成根因建议；请补充现场证据或直接开始维修。",
            prefill=None,
            summary=None,
        )

    draft_id = draft.id
    if session.state == DiagnosisState.DIAGNOSIS_READY and session.prefill and session.summary:
        draft.status = DiagnosisDraftStatus.DIAGNOSIS_READY
        draft.allowed_prefill = session.prefill
        draft.read_only_summary = {
            "_owner_user_id": actor.id,
            "_session": _session_state(session, request_dataset_ids),
            **session.summary,
        }
        write_audit_event(
            db, actor_user_id=actor.id, action="agent.fault_diagnosis.ready",
            resource_type="diagnosis_draft", resource_id=draft.id,
            result="success", metadata={"fault_report_id": fault.id},
        )
        add_notification(
            db,
            notification_type="AGENT",
            title="诊断建议已生成",
            body=f"故障 {fault.number} 的诊断 Agent 已完成建议。",
            level="INFO",
            related_object_id=fault.id,
            action_url=f"/fault-reports/{fault.id}",
        )
    else:
        draft.read_only_summary = {
            "_owner_user_id": actor.id,
            "_session": _session_state(session, request_dataset_ids),
        }
        write_audit_event(
            db, actor_user_id=actor.id, action="agent.fault_diagnosis.step",
            resource_type="fault_report", resource_id=fault.id,
            result="success" if session.state != DiagnosisState.UNAVAILABLE else "unavailable",
            metadata={"action": payload.action, "state": session.state.value},
        )
    response = _diagnosis_body(session, draft_id)
    save_idempotent_response(
        db, user_id=actor.id, method="POST", path=path,
        key=idempotency_key, request_body=request_body, status=200, body=response,
    )
    db.commit()
    return response


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
        if not payload.confirmed:
            return JSONResponse(status_code=200, content={
                "agent_status": "PREVIEW",
                "draft": preview.draft.model_dump(mode="json"),
                "missing_fields": list(preview.missing_fields),
            })
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
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("intelligence:agent")),
) -> dict[str, Any] | JSONResponse:
    reader = getattr(request.app.state, "health_score_reader", None) or _default_health_reader()
    result = reader.read(equipment_id)
    if result["status"] == "UNAVAILABLE":
        return JSONResponse(status_code=503, content=result)
    score = result.get("score")
    if isinstance(score, (int, float)):
        add_health_notification_if_band_changed(db, equipment_id=equipment_id, score=score)
        db.commit()
    return result
