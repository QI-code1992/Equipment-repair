import json
from collections.abc import Iterator
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.idempotency import (
    IdempotencyKeyReused,
    find_idempotent_response,
    save_idempotent_response,
)
from app.modules.agent_config.domain import AgentId
from app.modules.agent_config.models import AgentConfigModel
from app.modules.audit.service import write_audit_event, sanitize_audit_metadata
from app.modules.identity.dependencies import require_permission
from app.modules.identity.models import User

from .models import AgentConfirmation, AgentRun, AgentThread
from .schemas import MessageCreate, ResumeCreate, ThreadCreate
from .gateway import build_model_request
from .langgraph_runtime import run_checkpoint


router = APIRouter(prefix="/api/agent", tags=["agent-runtime"])
_PUBLIC_AGENT_IDS = {AgentId.FAULT_REPORTING.value, AgentId.METRIC_QUERY.value, AgentId.OPERATION_GUIDANCE.value}


def _now() -> datetime:
    return datetime.now(UTC)


def _thread_or_404(db: Session, thread_id: str, user: User) -> AgentThread:
    thread = db.get(AgentThread, thread_id)
    if thread is None:
        raise HTTPException(status_code=404, detail={"code": "THREAD_NOT_FOUND"})
    if thread.creator_user_id != user.id and "SYSTEM_ADMIN" not in {role.code for role in user.roles}:
        raise HTTPException(status_code=403, detail={"code": "THREAD_ACCESS_DENIED"})
    return thread


def _snapshot(config: AgentConfigModel | None) -> dict[str, object]:
    if config is None:
        return {}
    return {
        "agent_id": config.agent_id,
        "enabled": config.enabled,
        "model_binding_id": config.model_binding_id,
        "knowledge_dataset_ids": list(config.knowledge_dataset_ids),
        "streaming_enabled": config.streaming_enabled,
        "suggestions_enabled": config.suggestions_enabled,
        "sources_enabled": config.sources_enabled,
        "context_turns": config.context_turns,
        "retrieval_limit": config.retrieval_limit,
        "similarity_threshold": config.similarity_threshold,
        "deep_thinking_enabled": config.deep_thinking_enabled,
        "deep_thinking_level": config.deep_thinking_level,
        "max_reply_tokens": config.max_reply_tokens,
    }


def _event(name: str, data: dict[str, object]) -> dict[str, object]:
    return {"event": name, "data": data}


def _safe_text(text: str) -> str:
    # Runtime events contain status only; user text is never echoed into an event.
    return "[message received]" if text else ""


def _database_url(db: Session) -> str | None:
    bind = db.get_bind()
    return bind.url.render_as_string(hide_password=False) if bind is not None else None


def _response(db: Session, *, user: User, key: str, body: dict[str, object]) -> dict[str, object]:
    save_idempotent_response(
        db, user_id=user.id, method="POST", path="/api/agent/threads/{thread_id}/messages",
        key=key, request_body=body["request"], status=202, body=body["response"],
    )
    db.commit()
    return body["response"]


@router.post("/threads", status_code=201)
def create_thread(
    payload: ThreadCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("intelligence:agent")),
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
) -> dict[str, object]:
    if payload.agent_id not in _PUBLIC_AGENT_IDS:
        raise HTTPException(status_code=422, detail={"code": "AGENT_NOT_AVAILABLE"})
    request_body = payload.model_dump()
    try:
        replay = find_idempotent_response(
            db, user_id=user.id, method="POST", path="/api/agent/threads",
            key=idempotency_key, request_body=request_body,
        )
    except IdempotencyKeyReused:
        raise HTTPException(status_code=409, detail={"code": "IDEMPOTENCY_KEY_REUSED"}) from None
    if replay is not None:
        return replay[1]
    thread = AgentThread(
        agent_id=payload.agent_id,
        creator_user_id=user.id,
        business_context_json=sanitize_audit_metadata(payload.business_context),
        messages_json=[],
        status="OPEN",
    )
    db.add(thread)
    db.flush()
    response = {"thread_id": thread.id, "agent_id": thread.agent_id, "status": thread.status}
    write_audit_event(
        db, actor_user_id=user.id, action="agent.thread.create", resource_type="agent_thread",
        resource_id=thread.id, result="success", metadata={"agent_id": thread.agent_id, "business_context": payload.business_context},
    )
    save_idempotent_response(
        db, user_id=user.id, method="POST", path="/api/agent/threads", key=idempotency_key,
        request_body=request_body, status=201, body=response,
    )
    db.commit()
    return response


@router.post("/threads/{thread_id}/messages", status_code=202)
def create_run(
    thread_id: str,
    payload: MessageCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("intelligence:agent")),
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
) -> dict[str, object]:
    thread = _thread_or_404(db, thread_id, user)
    request_body = {"thread_id": thread_id, **payload.model_dump()}
    try:
        replay = find_idempotent_response(
            db, user_id=user.id, method="POST", path="/api/agent/threads/{thread_id}/messages",
            key=idempotency_key, request_body=request_body,
        )
    except IdempotencyKeyReused:
        raise HTTPException(status_code=409, detail={"code": "IDEMPOTENCY_KEY_REUSED"}) from None
    if replay is not None:
        return replay[1]
    config = db.scalar(select(AgentConfigModel).where(AgentConfigModel.agent_id == thread.agent_id))
    if config is None or not config.enabled or config.model_binding_id is None:
        raise HTTPException(status_code=503, detail={"code": "AGENT_CONFIG_INVALID"})
    message = {"role": "user", "text": _safe_text(payload.text), "attachment_refs": sanitize_audit_metadata(payload.attachment_refs)}
    model_request = build_model_request(config)
    thread.messages_json = [*thread.messages_json, message]
    run = AgentRun(
        thread_id=thread.id,
        config_snapshot_json=_snapshot(config),
        model_binding_id=config.model_binding_id,
        status="RUNNING",
        started_at=_now(),
        state_json=sanitize_audit_metadata({"step": "waiting_for_model", "events": [
            _event("run_started", {"run_id": "pending", "status": "RUNNING"}),
            _event("reasoning_status", {"status": "not_exposed", "level": config.deep_thinking_level}),
            _event("model_request", {
                "stream": model_request.stream,
                "max_tokens": model_request.max_tokens,
                "reasoning_effort": model_request.reasoning_effort,
            }),
        ]}),
    )
    db.add(run)
    db.flush()
    events = list(run.state_json["events"])
    events[0]["data"]["run_id"] = run.id
    events.append(_event("run_waiting", {"status": "WAITING_FOR_MODEL"}))
    run.state_json = run_checkpoint(
        run_id=run.id,
        initial_state={"step": "waiting_for_model", "status": "RUNNING", "events": events},
        database_url=_database_url(db),
    )
    thread.checkpoint_ref = run.id
    thread.updated_at = _now()
    response = {"run_id": run.id, "thread_id": thread.id, "status": run.status}
    write_audit_event(
        db, actor_user_id=user.id, action="agent.run.create", resource_type="agent_run",
        resource_id=run.id, result="success", metadata={"thread_id": thread.id, "agent_id": thread.agent_id},
    )
    return _response(db, user=user, key=idempotency_key, body={"request": request_body, "response": response})


@router.get("/runs/{run_id}/events")
def run_events(
    run_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("intelligence:agent")),
) -> StreamingResponse:
    run = db.get(AgentRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail={"code": "RUN_NOT_FOUND"})
    _thread_or_404(db, run.thread_id, user)

    def stream() -> Iterator[str]:
        for item in run.state_json.get("events", []):
            yield f"event: {item['event']}\ndata: {json.dumps(item['data'], ensure_ascii=False)}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})


@router.post("/threads/{thread_id}/resume", status_code=202)
def resume_thread(
    thread_id: str,
    payload: ResumeCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("intelligence:agent")),
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
) -> dict[str, object]:
    thread = _thread_or_404(db, thread_id, user)
    request_body = {"thread_id": thread_id, **payload.model_dump()}
    try:
        replay = find_idempotent_response(
            db, user_id=user.id, method="POST", path="/api/agent/threads/{thread_id}/resume",
            key=idempotency_key, request_body=request_body,
        )
    except IdempotencyKeyReused:
        raise HTTPException(status_code=409, detail={"code": "IDEMPOTENCY_KEY_REUSED"}) from None
    if replay is not None:
        return replay[1]
    if thread.checkpoint_ref is None:
        raise HTTPException(status_code=409, detail={"code": "CHECKPOINT_NOT_FOUND"})
    run = db.get(AgentRun, thread.checkpoint_ref)
    if run is None:
        raise HTTPException(status_code=409, detail={"code": "CHECKPOINT_NOT_FOUND"})
    confirmation = sanitize_audit_metadata(payload.confirmation)
    run.state_json = run_checkpoint(
        run_id=run.id,
        initial_state={"resume": payload.resume, "confirmation": confirmation},
        database_url=_database_url(db),
        resumed=True,
    )
    run.status = "RESUMED"
    thread.status = "OPEN"
    thread.updated_at = _now()
    db.add(AgentConfirmation(run_id=run.id, confirmation_type="resume", status="accepted", payload_json=confirmation))
    write_audit_event(
        db, actor_user_id=user.id, action="agent.run.resume", resource_type="agent_run",
        resource_id=run.id, result="success", metadata={"confirmation": confirmation},
    )
    response = {"run_id": run.id, "thread_id": thread.id, "status": run.status}
    save_idempotent_response(
        db, user_id=user.id, method="POST", path="/api/agent/threads/{thread_id}/resume",
        key=idempotency_key, request_body=request_body, status=202, body=response,
    )
    db.commit()
    return response


@router.get("/threads/{thread_id}")
def read_thread(
    thread_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("intelligence:agent")),
) -> dict[str, object]:
    thread = _thread_or_404(db, thread_id, user)
    runs = db.scalars(select(AgentRun).where(AgentRun.thread_id == thread.id)).all()
    return {
        "thread_id": thread.id,
        "agent_id": thread.agent_id,
        "status": thread.status,
        "messages": thread.messages_json,
        "runs": [{"run_id": run.id, "status": run.status, "state": run.state_json} for run in runs],
    }
