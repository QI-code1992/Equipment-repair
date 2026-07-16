from fastapi import HTTPException
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.modules.equipment.models import Equipment, Organization, OrganizationType
from app.modules.equipment.schemas import OrganizationCreate, OrganizationUpdate


ORGANIZATION_TREE_LOCK_ID = 824003
ALLOWED_CHILD = {
    OrganizationType.ROOT: OrganizationType.FACTORY,
    OrganizationType.FACTORY: OrganizationType.WORKSHOP,
    OrganizationType.WORKSHOP: OrganizationType.LINE,
}


def acquire_organization_tree_lock(db: Session) -> None:
    if db.get_bind().dialect.name == "postgresql":
        db.execute(
            text("SELECT pg_advisory_xact_lock(:lock_id)"),
            {"lock_id": ORGANIZATION_TREE_LOCK_ID},
        )


def _error(status_code: int, code: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code})


def organizations(db: Session) -> list[Organization]:
    return list(
        db.scalars(
            select(Organization).order_by(
                Organization.sort_order, Organization.name, Organization.id
            )
        )
    )


def _organization(db: Session, organization_id: str) -> Organization:
    organization = db.get(Organization, organization_id)
    if organization is None:
        raise _error(404, "ORGANIZATION_NOT_FOUND")
    return organization


def _validate_unique(
    db: Session,
    *,
    code: str,
    name: str,
    parent_id: str,
    exclude_id: str | None = None,
) -> None:
    code_owner = db.scalar(select(Organization).where(Organization.code == code))
    if code_owner is not None and code_owner.id != exclude_id:
        raise _error(409, "ORGANIZATION_CODE_EXISTS")
    name_owner = db.scalar(
        select(Organization).where(
            Organization.parent_id == parent_id, Organization.name == name
        )
    )
    if name_owner is not None and name_owner.id != exclude_id:
        raise _error(409, "ORGANIZATION_SIBLING_NAME_EXISTS")


def create_organization(db: Session, payload: OrganizationCreate) -> Organization:
    acquire_organization_tree_lock(db)
    parent = db.get(Organization, payload.parent_id)
    if parent is None:
        raise _error(404, "ORGANIZATION_PARENT_NOT_FOUND")
    if not parent.enabled:
        raise _error(409, "ORGANIZATION_PARENT_DISABLED")
    if ALLOWED_CHILD.get(parent.type) != payload.type:
        raise _error(422, "ORGANIZATION_LEVEL_INVALID")
    _validate_unique(
        db, code=payload.code, name=payload.name, parent_id=payload.parent_id
    )
    created = Organization(**payload.model_dump())
    db.add(created)
    db.flush()
    return created


def _disable_descendants(db: Session, organization_id: str) -> None:
    pending = [organization_id]
    while pending:
        parent_ids = pending
        descendants = list(
            db.scalars(select(Organization).where(Organization.parent_id.in_(parent_ids)))
        )
        for descendant in descendants:
            descendant.enabled = False
        pending = [descendant.id for descendant in descendants]


def update_organization(
    db: Session, organization_id: str, payload: OrganizationUpdate
) -> Organization:
    acquire_organization_tree_lock(db)
    organization = _organization(db, organization_id)
    if organization.type == OrganizationType.ROOT:
        raise _error(409, "ORGANIZATION_ROOT_PROTECTED")
    if payload.enabled:
        parent = _organization(db, organization.parent_id or "")
        if not parent.enabled:
            raise _error(409, "ORGANIZATION_PARENT_DISABLED")
    _validate_unique(
        db,
        code=payload.code,
        name=payload.name,
        parent_id=organization.parent_id or "",
        exclude_id=organization.id,
    )
    for field, value in payload.model_dump().items():
        setattr(organization, field, value)
    if not payload.enabled:
        _disable_descendants(db, organization.id)
    db.flush()
    return organization


def delete_organization(db: Session, organization_id: str) -> Organization:
    acquire_organization_tree_lock(db)
    organization = _organization(db, organization_id)
    if organization.type == OrganizationType.ROOT:
        raise _error(409, "ORGANIZATION_ROOT_PROTECTED")
    if db.scalar(select(Organization.id).where(Organization.parent_id == organization.id)):
        raise _error(409, "ORGANIZATION_HAS_CHILDREN")
    if db.scalar(select(Equipment.id).where(Equipment.organization_id == organization.id)):
        raise _error(409, "ORGANIZATION_HAS_EQUIPMENT")
    db.delete(organization)
    db.flush()
    return organization
