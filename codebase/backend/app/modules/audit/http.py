from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.idempotency import IdempotencyKeyReused
from app.modules.audit.service import write_audit_event


def protected_write(request: Request) -> bool:
    return (
        request.url.path.startswith("/api/")
        and request.method in {"POST", "PUT", "PATCH", "DELETE"}
        and request.url.path != "/api/auth/login"
    )


def route_action(request: Request) -> str:
    route = request.scope.get("route")
    return getattr(route, "name", None) or f"http.{request.method.lower()}"


def response_detail(detail: object, event_id: str | None) -> dict[str, object]:
    normalized = (
        detail
        if isinstance(detail, dict)
        else {"code": "REQUEST_FAILED", "message": str(detail)}
    )
    result = dict(normalized)
    if event_id is not None:
        result["audit_event_id"] = event_id
    return result


def validation_detail(error: RequestValidationError) -> dict[str, object]:
    fields: list[dict[str, str]] = []
    for item in error.errors():
        field = next(
            (member for member in reversed(item["loc"]) if isinstance(member, str)),
            "request",
        )
        fields.append({"field": field, "type": item["type"]})
    return {"code": "VALIDATION_ERROR", "fields": fields}


def persist_failure(request: Request, detail: object) -> str | None:
    event_id = getattr(request.state, "audit_event_id", None)
    if not protected_write(request) or event_id is not None:
        return event_id

    with request.app.state.session_factory() as db:
        action = route_action(request)
        event = write_audit_event(
            db,
            actor_user_id=getattr(request.state, "current_user_id", None),
            action=action,
            resource_type=action.partition(".")[0],
            resource_id=None,
            result="failure",
            metadata={
                "method": request.method,
                "path": request.url.path,
                "detail": detail,
            },
        )
        db.commit()
        event_id = event.id
    request.state.audit_event_id = event_id
    return event_id


def register_audit_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, error: HTTPException
    ) -> JSONResponse:
        event_id = persist_failure(request, error.detail)
        return JSONResponse(
            status_code=error.status_code,
            content={"detail": response_detail(error.detail, event_id)},
            headers=error.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, error: RequestValidationError
    ) -> JSONResponse:
        detail = validation_detail(error)
        event_id = persist_failure(request, detail)
        return JSONResponse(
            status_code=422,
            content={"detail": response_detail(detail, event_id)},
        )

    @app.exception_handler(IdempotencyKeyReused)
    async def idempotency_exception_handler(
        request: Request, error: IdempotencyKeyReused
    ) -> JSONResponse:
        del error
        detail = {"code": "IDEMPOTENCY_KEY_REUSED"}
        event_id = persist_failure(request, detail)
        return JSONResponse(
            status_code=409,
            content={"detail": response_detail(detail, event_id)},
        )
