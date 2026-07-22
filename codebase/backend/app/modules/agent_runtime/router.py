import json
from collections.abc import Iterator
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.agent_config.domain import AgentId
from app.modules.agent_config.models import AgentConfigModel
from app.modules.identity.dependencies import require_permission
from app.modules.identity.models import User

from .models import AgentConfirmation, AgentRun, AgentThread
from .schemas import MessageCreate, ResumeCreate, ThreadCreate
from .gateway import build_model_request


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


@router.post("/threads", status_code=201)
def create_thread(
    payload: ThreadCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("intelligence:agent")),
) -> dict[str, object]:
    if payload.agent_id not in _PUBLIC_AGENT_IDS:
        raise HTTPException(status_code=422, detail={"code": "AGENT_NOT_AVAILABLE"})
    if any(key.lower() in {"token", "password", "cookie", "secret", "api_key"} for key in payload.business_context):
        raise HTTPException(status_code=422, detail={"code": "SENSITIVE_CONTEXT_FORBIDDEN"})
    thread = AgentThread(
        agent_id=payload.agent_id,
        creator_user_id=user.id,
        business_context_json=payload.business_context,
        messages_json=[],
        status="OPEN",
    )
    db.add(thread)
    db.commit()
    return {"thread_id": thread.id, "agent_id": thread.agent_id, "status": thread.status}


@router.post("/threads/{thread_id}/messages", status_code=202)
def create_run(
    thread_id: str,
    payload: MessageCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("intelligence:agent")),
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
) -> dict[str, object]:
    del idempotency_key  # Runtime writes are currently persisted once per request.
    thread = _thread_or_404(db, thread_id, user)
    config = db.scalar(select(AgentConfigModel).where(AgentConfigModel.agent_id == thread.agent_id))
    if config is None or not config.enabled or config.model_binding_id is None:
        raise HTTPException(status_code=503, detail={"code": "AGENT_CONFIG_INVALID"})
    message = {"role": "user", "text": _safe_text(payload.text), "attachment_refs": payload.attachment_refs}
    model_request = build_model_request(config)
    thread.messages_json = [*thread.messages_json, message]
    run = AgentRun(
        thread_id=thread.id,
        config_snapshot_json=_snapshot(config),
        model_binding_id=config.model_binding_id,
        status="RUNNING",
        started_at=_now(),
        state_json={"step": "waiting_for_model", "events": [
            _event("run_started", {"run_id": "pending", "status": "RUNNING"}),
            _event("reasoning_status", {"status": "not_exposed", "level": config.deep_thinking_level}),
            _event("model_request", {
                "stream": model_request.stream,
                "max_tokens": model_request.max_tokens,
                "reasoning_effort": model_request.reasoning_effort,
            }),
        ]},
    )
    db.add(run)
    db.flush()
    events = list(run.state_json["events"])
    events[0]["data"]["run_id"] = run.id
    events.append(_event("run_waiting", {"status": "WAITING_FOR_MODEL"}))
    run.state_json = {"step": "waiting_for_model", "events": events}
    thread.checkpoint_ref = run.id
    thread.updated_at = _now()
    db.commit()
    return {"run_id": run.id, "thread_id": thread.id, "status": run.status}


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
) -> dict[str, object]:
    thread = _thread_or_404(db, thread_id, user)
    if thread.checkpoint_ref is None:
        raise HTTPException(status_code=409, detail={"code": "CHECKPOINT_NOT_FOUND"})
    run = db.get(AgentRun, thread.checkpoint_ref)
    if run is None:
        raise HTTPException(status_code=409, detail={"code": "CHECKPOINT_NOT_FOUND"})
    run.state_json = {**run.state_json, "resume": payload.resume, "confirmation": payload.confirmation}
    run.status = "RESUMED"
    thread.status = "OPEN"
    thread.updated_at = _now()
    db.add(AgentConfirmation(run_id=run.id, confirmation_type="resume", status="accepted", payload_json=payload.confirmation))
    db.commit()
    return {"run_id": run.id, "thread_id": thread.id, "status": run.status}


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
