from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.idempotency import find_idempotent_response, save_idempotent_response
from app.modules.audit.service import write_audit_event
from app.modules.identity.dependencies import bearer, get_current_user
from app.modules.identity.models import LoginSession, User
from app.modules.identity.schemas import PasswordChangeRequest
from app.modules.identity.security import hash_password, verify_password
from app.modules.identity.service import (
    active_user_for_session,
    create_login_session,
    login_session_for_token,
    permission_codes_for_user,
)


router = APIRouter(prefix="/api/auth", tags=["identity"])


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str
    password: str


@router.patch("/password")
def change_password(
    payload: PasswordChangeRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, str]:
    if not verify_password(payload.current_password, user.password_hash):
        event = write_audit_event(
            db,
            actor_user_id=user.id,
            action="password_change",
            resource_type="user",
            resource_id=user.id,
            result="failed",
            metadata={"reason": "current_password_invalid"},
        )
        db.commit()
        raise HTTPException(
            status_code=422,
            detail={
                "code": "CURRENT_PASSWORD_INVALID",
                "fields": {"current_password": "INVALID"},
                "audit_event_id": event.id,
            },
        )
    if payload.new_password != payload.confirm_password:
        event = write_audit_event(
            db,
            actor_user_id=user.id,
            action="password_change",
            resource_type="user",
            resource_id=user.id,
            result="failed",
            metadata={"reason": "confirmation_mismatch"},
        )
        db.commit()
        raise HTTPException(
            status_code=422,
            detail={
                "code": "PASSWORD_CONFIRMATION_MISMATCH",
                "fields": {"confirm_password": "MISMATCH"},
                "audit_event_id": event.id,
            },
        )

    user.password_hash = hash_password(payload.new_password)
    sessions = db.scalars(
        select(LoginSession).where(
            LoginSession.user_id == user.id,
            LoginSession.revoked_at.is_(None),
        )
    )
    for session in sessions:
        session.revoked_at = datetime.now(UTC)
    event = write_audit_event(
        db,
        actor_user_id=user.id,
        action="password_change",
        resource_type="user",
        resource_id=user.id,
        result="success",
        metadata={"sessions_revoked": True},
    )
    db.commit()
    return {"audit_event_id": event.id}


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    token = create_login_session(db, payload.username, payload.password)
    if token is None:
        raise HTTPException(status_code=401, detail={"code": "INVALID_CREDENTIALS"})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
def read_current_user(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, object]:
    return {
        "id": user.id,
        "username": user.username,
        "enabled": user.enabled,
        "permission_codes": sorted(permission_codes_for_user(db, user.id)),
    }


@router.delete("/session", response_model=None, name="session.logout")
def logout(
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> dict[str, object] | JSONResponse:
    if credentials is None:
        raise HTTPException(status_code=401, detail={"code": "UNAUTHENTICATED"})
    login_session = login_session_for_token(db, credentials.credentials)
    if login_session is None:
        raise HTTPException(status_code=401, detail={"code": "UNAUTHENTICATED"})

    replay = find_idempotent_response(
        db,
        user_id=login_session.user_id,
        method="DELETE",
        path="/api/auth/session",
        key=idempotency_key,
        request_body={},
    )
    if replay is not None:
        status, body = replay
        return JSONResponse(status_code=status, content=body)
    if active_user_for_session(db, login_session) is None:
        raise HTTPException(status_code=401, detail={"code": "UNAUTHENTICATED"})

    login_session.revoked_at = datetime.now(UTC)
    event = write_audit_event(
        db,
        actor_user_id=login_session.user_id,
        action="logout",
        resource_type="session",
        resource_id=login_session.id,
        result="success",
        metadata={},
    )
    body: dict[str, object] = {"audit_event_id": event.id}
    save_idempotent_response(
        db,
        user_id=login_session.user_id,
        method="DELETE",
        path="/api/auth/session",
        key=idempotency_key,
        request_body={},
        status=200,
        body=body,
    )
    db.commit()
    return body
