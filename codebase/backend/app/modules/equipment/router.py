from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.equipment.models import Equipment
from app.modules.identity.dependencies import require_permission
from app.modules.identity.models import User


router = APIRouter(prefix="/api/equipment", tags=["equipment"])


@router.get("")
def list_equipment(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("equipment:read")),
) -> list[dict[str, object]]:
    del user
    equipment = db.scalars(select(Equipment).order_by(Equipment.code)).all()
    return [
        {
            "id": item.id,
            "code": item.code,
            "name": item.name,
            "organization_id": item.organization_id,
            "enabled": item.enabled,
        }
        for item in equipment
    ]
