"""FastAPI routes for agent configuration."""

from collections.abc import Awaitable, Callable
from typing import NoReturn

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from pydantic import BaseModel

from .domain import AgentConfig, DeepThinkingLevel
from .service import AgentConfigError, AgentConfigService, parse_agent_id


class AgentConfigRequest(BaseModel):
    agent_id: str
    enabled: bool
    model_binding_id: str | None
    knowledge_dataset_ids: list[str]
    streaming_enabled: bool
    suggestions_enabled: bool
    sources_enabled: bool
    context_turns: int
    retrieval_limit: int
    similarity_threshold: float
    deep_thinking_enabled: bool
    deep_thinking_level: DeepThinkingLevel
    max_reply_tokens: int


class ModelCapabilityResponse(BaseModel):
    binding_id: str
    display_name: str
    supports_reasoning: bool


class AgentConfigResponse(AgentConfigRequest):
    model_capability: ModelCapabilityResponse | None


class _SanitizedValidationRoute(APIRoute):
    def get_route_handler(self) -> Callable[[Request], Awaitable[Response]]:
        route_handler = super().get_route_handler()

        async def sanitized_route_handler(request: Request) -> Response:
            try:
                return await route_handler(request)
            except RequestValidationError as error:
                fields = [
                    {
                        "field": ".".join(
                            str(part) for part in issue["loc"] if part != "body"
                        ),
                        "message": "请求字段无效。",
                    }
                    for issue in error.errors()
                ]
                return JSONResponse(
                    status_code=422,
                    content={
                        "detail": {
                            "code": "AGENT_CONFIG_INVALID",
                            "message": "Agent 配置请求无效。",
                            "fields": fields,
                        }
                    },
                )

        return sanitized_route_handler


def _raise_http(error: AgentConfigError) -> NoReturn:
    status_code = (
        404
        if error.code in {"UNKNOWN_AGENT_ID", "AGENT_CONFIG_NOT_FOUND"}
        else 422
    )
    raise HTTPException(
        status_code=status_code,
        detail={
            "code": error.code,
            "message": error.message,
            "fields": [
                {"field": issue.field, "message": issue.message}
                for issue in error.issues
            ],
        },
    ) from error


def _response(service: AgentConfigService, config: AgentConfig) -> AgentConfigResponse:
    capability = service.model_capability(config.model_binding_id)
    return AgentConfigResponse(
        agent_id=config.agent_id.value,
        enabled=config.enabled,
        model_binding_id=config.model_binding_id,
        knowledge_dataset_ids=list(config.knowledge_dataset_ids),
        streaming_enabled=config.streaming_enabled,
        suggestions_enabled=config.suggestions_enabled,
        sources_enabled=config.sources_enabled,
        context_turns=config.context_turns,
        retrieval_limit=config.retrieval_limit,
        similarity_threshold=config.similarity_threshold,
        deep_thinking_enabled=config.deep_thinking_enabled,
        deep_thinking_level=config.deep_thinking_level,
        max_reply_tokens=config.max_reply_tokens,
        model_capability=(
            None
            if capability is None
            else ModelCapabilityResponse(
                binding_id=capability.binding_id,
                display_name=capability.display_name,
                supports_reasoning=capability.supports_reasoning,
            )
        ),
    )


def create_agent_config_router(service: AgentConfigService) -> APIRouter:
    router = APIRouter(
        prefix="/api/agent-configs",
        tags=["agent-configs"],
        route_class=_SanitizedValidationRoute,
    )

    @router.get("", response_model=list[AgentConfigResponse])
    def list_agent_configs() -> list[AgentConfigResponse]:
        return [_response(service, config) for config in service.list_all()]

    @router.get("/{agent_id}", response_model=AgentConfigResponse)
    def get_agent_config(agent_id: str) -> AgentConfigResponse:
        try:
            return _response(service, service.get(agent_id))
        except AgentConfigError as error:
            _raise_http(error)

    @router.put("/{agent_id}", response_model=AgentConfigResponse)
    def save_agent_config(
        agent_id: str, payload: AgentConfigRequest
    ) -> AgentConfigResponse:
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
                deep_thinking_level=payload.deep_thinking_level,
                max_reply_tokens=payload.max_reply_tokens,
            )
            return _response(service, service.save(agent_id, candidate))
        except AgentConfigError as error:
            _raise_http(error)

    return router
