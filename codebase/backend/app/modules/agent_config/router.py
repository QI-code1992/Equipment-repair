from collections.abc import Callable

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.idempotency import find_idempotent_response, save_idempotent_response
from app.modules.audit.service import write_audit_event
from app.modules.identity.dependencies import require_permission
from app.modules.identity.models import User

from .domain import AgentConfig, DeepThinkingLevel
from .models import AgentConfigModel, ModelBinding, ModelProvider
from .repository import SqlAgentConfigRepository, SqlModelCatalog
from .schemas import (
    AgentConfigRead,
    AgentConfigWrite,
    AgentConfigWriteResponse,
    BindingRead,
    BindingWrite,
    BindingWriteResponse,
    DeleteResponse,
    ModelCapabilityRead,
    ProviderRead,
    ProviderWrite,
    ProviderWriteResponse,
)
from .service import AgentConfigError, AgentConfigService, parse_agent_id


router = APIRouter(prefix="/api", tags=["agent-config"])


def provider_body(provider: ModelProvider) -> dict[str, object]:
    return {"id": provider.id, "name": provider.name, "enabled": provider.enabled}


def binding_body(binding: ModelBinding) -> dict[str, object]:
    return {
        "id": binding.id,
        "provider_id": binding.provider_id,
        "name": binding.name,
        "model_name": binding.model_name,
        "supports_reasoning": binding.supports_reasoning,
        "enabled": binding.enabled,
    }


def agent_config_body(
    service: AgentConfigService, config: AgentConfig
) -> dict[str, object]:
    capability = service.model_capability(config.model_binding_id)
    return {
        "agent_id": config.agent_id.value,
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
        "deep_thinking_level": config.deep_thinking_level.value,
        "max_reply_tokens": config.max_reply_tokens,
        "model_capability": (
            None
            if capability is None
            else {
                "binding_id": capability.binding_id,
                "display_name": capability.display_name,
                "supports_reasoning": capability.supports_reasoning,
            }
        ),
    }


def agent_service(db: Session) -> AgentConfigService:
    return AgentConfigService(SqlAgentConfigRepository(db), SqlModelCatalog(db))


def idempotent_write(
    db: Session,
    actor: User,
    method: str,
    path: str,
    key: str,
    request_body: dict[str, object],
    write: Callable[[], tuple[int, dict[str, object]]],
) -> dict[str, object] | JSONResponse:
    replay = find_idempotent_response(
        db,
        user_id=actor.id,
        method=method,
        path=path,
        key=key,
        request_body=request_body,
    )
    if replay is not None:
        return JSONResponse(status_code=replay[0], content=replay[1])
    status, body = write()
    save_idempotent_response(
        db,
        user_id=actor.id,
        method=method,
        path=path,
        key=key,
        request_body=request_body,
        status=status,
        body=body,
    )
    db.commit()
    return body


def raise_agent_error(error: AgentConfigError) -> None:
    status_code = 404 if error.code in {"UNKNOWN_AGENT_ID", "AGENT_CONFIG_NOT_FOUND"} else 422
    raise HTTPException(
        status_code=status_code,
        detail={
            "code": error.code,
            "message": error.message,
            "fields": {issue.field: "invalid" for issue in error.issues},
        },
    ) from error


def provider_or_404(db: Session, provider_id: str) -> ModelProvider:
    provider = db.get(ModelProvider, provider_id)
    if provider is None:
        raise HTTPException(status_code=404, detail={"code": "MODEL_PROVIDER_NOT_FOUND"})
    return provider


def binding_or_404(db: Session, binding_id: str) -> ModelBinding:
    binding = db.get(ModelBinding, binding_id)
    if binding is None:
        raise HTTPException(status_code=404, detail={"code": "MODEL_BINDING_NOT_FOUND"})
    return binding


@router.get("/model-providers", response_model=list[ProviderRead])
def list_providers(
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("intelligence:model")),
) -> list[dict[str, object]]:
    del actor
    return [provider_body(row) for row in db.scalars(select(ModelProvider).order_by(ModelProvider.name))]


@router.post("/model-providers", status_code=201, response_model=ProviderWriteResponse)
def create_provider(
    payload: ProviderWrite,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("intelligence:model")),
) -> dict[str, object] | JSONResponse:
    request_body = payload.model_dump(mode="json")

    def write() -> tuple[int, dict[str, object]]:
        provider = ModelProvider(**request_body)
        db.add(provider)
        db.flush()
        event = write_audit_event(
            db, actor_user_id=actor.id, action="model_provider.create",
            resource_type="model_provider", resource_id=provider.id, result="success",
            metadata={"name": provider.name},
        )
        return 201, {**provider_body(provider), "audit_event_id": event.id}

    return idempotent_write(db, actor, "POST", "/api/model-providers", idempotency_key, request_body, write)


@router.put("/model-providers/{provider_id}", response_model=ProviderWriteResponse)
def update_provider(
    provider_id: str,
    payload: ProviderWrite,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("intelligence:model")),
) -> dict[str, object] | JSONResponse:
    request_body = payload.model_dump(mode="json")
    path = f"/api/model-providers/{provider_id}"

    def write() -> tuple[int, dict[str, object]]:
        provider = provider_or_404(db, provider_id)
        provider.name = payload.name
        provider.secret_ref = payload.secret_ref
        provider.enabled = payload.enabled
        db.flush()
        event = write_audit_event(
            db, actor_user_id=actor.id, action="model_provider.update",
            resource_type="model_provider", resource_id=provider.id, result="success",
            metadata={"name": provider.name},
        )
        return 200, {**provider_body(provider), "audit_event_id": event.id}

    return idempotent_write(db, actor, "PUT", path, idempotency_key, request_body, write)


@router.delete("/model-providers/{provider_id}", response_model=DeleteResponse)
def delete_provider(
    provider_id: str,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("intelligence:model")),
) -> dict[str, object] | JSONResponse:
    path = f"/api/model-providers/{provider_id}"

    def write() -> tuple[int, dict[str, object]]:
        provider = provider_or_404(db, provider_id)
        db.delete(provider)
        event = write_audit_event(
            db, actor_user_id=actor.id, action="model_provider.delete",
            resource_type="model_provider", resource_id=provider_id, result="success",
            metadata={"name": provider.name},
        )
        return 200, {"id": provider_id, "audit_event_id": event.id}

    return idempotent_write(db, actor, "DELETE", path, idempotency_key, {}, write)


@router.get("/model-bindings", response_model=list[BindingRead])
def list_bindings(
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("intelligence:model")),
) -> list[dict[str, object]]:
    del actor
    return [binding_body(row) for row in db.scalars(select(ModelBinding).order_by(ModelBinding.name))]


@router.post("/model-bindings", status_code=201, response_model=BindingWriteResponse)
def create_binding(
    payload: BindingWrite,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("intelligence:model")),
) -> dict[str, object] | JSONResponse:
    request_body = payload.model_dump(mode="json")

    def write() -> tuple[int, dict[str, object]]:
        provider_or_404(db, payload.provider_id)
        binding = ModelBinding(**request_body)
        db.add(binding)
        db.flush()
        event = write_audit_event(
            db, actor_user_id=actor.id, action="model_binding.create",
            resource_type="model_binding", resource_id=binding.id, result="success",
            metadata=binding_body(binding),
        )
        return 201, {**binding_body(binding), "audit_event_id": event.id}

    return idempotent_write(db, actor, "POST", "/api/model-bindings", idempotency_key, request_body, write)


@router.put("/model-bindings/{binding_id}", response_model=BindingWriteResponse)
def update_binding(
    binding_id: str,
    payload: BindingWrite,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("intelligence:model")),
) -> dict[str, object] | JSONResponse:
    request_body = payload.model_dump(mode="json")
    path = f"/api/model-bindings/{binding_id}"

    def write() -> tuple[int, dict[str, object]]:
        provider_or_404(db, payload.provider_id)
        binding = binding_or_404(db, binding_id)
        binding.provider_id = payload.provider_id
        binding.name = payload.name
        binding.model_name = payload.model_name
        binding.supports_reasoning = payload.supports_reasoning
        binding.enabled = payload.enabled
        db.flush()
        event = write_audit_event(
            db, actor_user_id=actor.id, action="model_binding.update",
            resource_type="model_binding", resource_id=binding.id, result="success",
            metadata=binding_body(binding),
        )
        return 200, {**binding_body(binding), "audit_event_id": event.id}

    return idempotent_write(db, actor, "PUT", path, idempotency_key, request_body, write)


@router.delete("/model-bindings/{binding_id}", response_model=DeleteResponse)
def delete_binding(
    binding_id: str,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("intelligence:model")),
) -> dict[str, object] | JSONResponse:
    path = f"/api/model-bindings/{binding_id}"

    def write() -> tuple[int, dict[str, object]]:
        binding = binding_or_404(db, binding_id)
        db.delete(binding)
        event = write_audit_event(
            db, actor_user_id=actor.id, action="model_binding.delete",
            resource_type="model_binding", resource_id=binding_id, result="success",
            metadata={"name": binding.name},
        )
        return 200, {"id": binding_id, "audit_event_id": event.id}

    return idempotent_write(db, actor, "DELETE", path, idempotency_key, {}, write)


@router.get("/agent-configs", response_model=list[AgentConfigRead])
def list_agent_configs(
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("intelligence:agent")),
) -> list[dict[str, object]]:
    del actor
    service = agent_service(db)
    return [agent_config_body(service, config) for config in service.list_all()]


@router.get("/agent-configs/{agent_id}", response_model=AgentConfigRead)
def get_agent_config(
    agent_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("intelligence:agent")),
) -> dict[str, object]:
    del actor
    service = agent_service(db)
    try:
        config = service.initialize(agent_id)
    except AgentConfigError as error:
        raise_agent_error(error)
    db.commit()
    return agent_config_body(service, config)


@router.put("/agent-configs/{agent_id}", response_model=AgentConfigWriteResponse)
def update_agent_config(
    agent_id: str,
    payload: AgentConfigWrite,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("intelligence:agent")),
) -> dict[str, object] | JSONResponse:
    request_body = payload.model_dump(mode="json")
    path = f"/api/agent-configs/{agent_id}"

    def write() -> tuple[int, dict[str, object]]:
        service = agent_service(db)
        try:
            candidate = AgentConfig(
                agent_id=parse_agent_id(payload.agent_id),
                enabled=payload.enabled,
                model_binding_id=payload.model_binding_id,
                knowledge_dataset_ids=tuple(payload.knowledge_dataset_ids),
                streaming_enabled=payload.streaming_enabled,
                suggestions_enabled=payload.suggestions_enabled,
                sources_enabled=payload.sources_enabled,
                context_turns=payload.context_turns,
                retrieval_limit=payload.retrieval_limit,
                similarity_threshold=payload.similarity_threshold,
                deep_thinking_enabled=payload.deep_thinking_enabled,
                deep_thinking_level=DeepThinkingLevel(payload.deep_thinking_level),
                max_reply_tokens=payload.max_reply_tokens,
            )
            config = service.save(agent_id, candidate)
        except AgentConfigError as error:
            raise_agent_error(error)
        row = db.scalar(select(AgentConfigModel).where(AgentConfigModel.agent_id == config.agent_id.value))
        assert row is not None
        row.updated_by = actor.id
        event = write_audit_event(
            db, actor_user_id=actor.id, action="agent_config.update",
            resource_type="agent_config", resource_id=config.agent_id.value, result="success",
            metadata={"agent_id": config.agent_id.value},
        )
        return 200, {**agent_config_body(service, config), "audit_event_id": event.id}

    return idempotent_write(db, actor, "PUT", path, idempotency_key, request_body, write)
