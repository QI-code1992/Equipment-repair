from collections.abc import Callable

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.identity.models import User
from app.modules.identity.service import permission_codes_for_user, user_for_token
from app.modules.audit.service import write_audit_event


bearer = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    user = None if credentials is None else user_for_token(db, credentials.credentials)
    if user is None:
        raise HTTPException(status_code=401, detail={"code": "UNAUTHENTICATED"})
    request.state.current_user_id = user.id
    return user


def require_permission(code: str) -> Callable[..., User]:
    def dependency(
        request: Request,
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        if code not in permission_codes_for_user(db, user.id):
            event = write_audit_event(
                db,
                actor_user_id=user.id,
                action="permission.denied",
                resource_type="permission",
                resource_id=code,
                result="denied",
                metadata={"permission_code": code},
            )
            db.commit()
            request.state.audit_event_id = event.id
            raise HTTPException(status_code=403, detail={"code": "PERMISSION_DENIED"})
        return user

    return dependency
