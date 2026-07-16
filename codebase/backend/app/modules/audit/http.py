import json
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.core.idempotency import IdempotencyKeyReused
from app.modules.audit.service import sanitize_audit_metadata, write_audit_event
from app.modules.identity.service import login_session_for_token


logger = logging.getLogger(__name__)

STABLE_ERROR_FIELDS = {
    "IDEMPOTENCY_KEY_REUSED": {"idempotency_key": "conflict"},
    "USERNAME_EXISTS": {"username": "duplicate"},
    "ORGANIZATION_CODE_EXISTS": {"code": "duplicate"},
    "ORGANIZATION_SIBLING_NAME_EXISTS": {"name": "duplicate"},
    "EQUIPMENT_CODE_EXISTS": {"code": "duplicate"},
}


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
    result: dict[str, object] = {
        "code": "REQUEST_FAILED",
        "message": "REQUEST_FAILED",
        "fields": {},
    }
    if isinstance(detail, dict):
        sanitized = sanitize_audit_metadata(detail)
        if isinstance(sanitized, dict):
            if isinstance(sanitized.get("code"), str):
                result["code"] = sanitized["code"]
            result["message"] = (
                sanitized["message"]
                if isinstance(sanitized.get("message"), str)
                else result["code"]
            )
            fields = sanitized.get("fields")
            if isinstance(fields, list):
                result["fields"] = {
                    item["field"]: item["type"]
                    for item in fields
                    if isinstance(item, dict)
                    and isinstance(item.get("field"), str)
                    and isinstance(item.get("type"), str)
                }
            elif isinstance(fields, dict):
                result["fields"] = {
                    str(field): value
                    for field, value in fields.items()
                    if isinstance(value, str)
                }
    if not result["fields"]:
        result["fields"] = STABLE_ERROR_FIELDS.get(str(result["code"]), {})
    if event_id is not None:
        result["audit_event_id"] = event_id
    return result


def validation_detail(error: RequestValidationError) -> dict[str, object]:
    fields: dict[str, str] = {}
    for item in error.errors():
        field = next(
            (member for member in reversed(item["loc"]) if isinstance(member, str)),
            "request",
        )
        fields[field] = item["type"]
    return {"code": "VALIDATION_ERROR", "fields": fields}


def bearer_token(request: Request) -> str | None:
    scheme, _, token = request.headers.get("authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token


async def request_summary(request: Request, body: object = None) -> object | None:
    content_type = request.headers.get("content-type", "").split(";", 1)[0].lower()
    if content_type != "application/json" and not content_type.endswith("+json"):
        return None
    value = body
    if value is None:
        raw_body = await request.body()
        if not raw_body:
            return None
        try:
            value = json.loads(raw_body)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None
    if not isinstance(value, (dict, list)):
        return None
    return sanitize_audit_metadata(value)


async def persist_failure(
    request: Request, detail: object, *, body: object = None
) -> tuple[str | None, bool]:
    event_id = getattr(request.state, "audit_event_id", None)
    if not protected_write(request) or event_id is not None:
        return event_id, False

    with request.app.state.session_factory() as db:
        try:
            actor_user_id = getattr(request.state, "current_user_id", None)
            if actor_user_id is None:
                token = bearer_token(request)
                login_session = (
                    None if token is None else login_session_for_token(db, token)
                )
                if login_session is not None:
                    actor_user_id = login_session.user_id
            action = route_action(request)
            metadata: dict[str, object] = {
                "method": request.method,
                "path": request.url.path,
                "detail": response_detail(detail, None),
            }
            summary = await request_summary(request, body)
            if summary is not None:
                metadata["request"] = summary
            event = write_audit_event(
                db,
                actor_user_id=actor_user_id,
                action=action,
                resource_type=action.partition(".")[0],
                resource_id=None,
                result="failure",
                metadata=metadata,
            )
            db.commit()
            event_id = event.id
        except SQLAlchemyError:
            try:
                db.rollback()
            except SQLAlchemyError:
                logger.error("Failed to roll back audit transaction")
            logger.error("Failed to persist audit event")
            return None, True
    request.state.audit_event_id = event_id
    return event_id, False


def audit_persist_failed_response() -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "detail": response_detail({"code": "AUDIT_PERSIST_FAILED"}, None)
        },
    )


def register_audit_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, error: HTTPException
    ) -> JSONResponse:
        event_id, persist_failed = await persist_failure(request, error.detail)
        if persist_failed:
            return audit_persist_failed_response()
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
        event_id, persist_failed = await persist_failure(
            request, detail, body=error.body
        )
        if persist_failed:
            return audit_persist_failed_response()
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
        event_id, persist_failed = await persist_failure(request, detail)
        if persist_failed:
            return audit_persist_failed_response()
        return JSONResponse(
            status_code=409,
            content={"detail": response_detail(detail, event_id)},
        )
