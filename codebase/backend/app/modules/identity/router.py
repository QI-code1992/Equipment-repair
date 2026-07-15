from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.identity.dependencies import bearer, get_current_user
from app.modules.identity.models import User
from app.modules.identity.service import create_login_session, revoke_token


router = APIRouter(prefix="/api/auth", tags=["identity"])


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    token = create_login_session(db, payload.username, payload.password)
    if token is None:
        raise HTTPException(status_code=401, detail={"code": "INVALID_CREDENTIALS"})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
def read_current_user(user: User = Depends(get_current_user)) -> dict[str, object]:
    return {"id": user.id, "username": user.username, "enabled": user.enabled}


@router.delete("/session", status_code=204)
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    del user
    revoke_token(db, credentials.credentials)
