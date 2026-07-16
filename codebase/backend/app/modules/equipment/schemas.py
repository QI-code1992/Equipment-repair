from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.equipment.models import EquipmentStatus, OrganizationType


class ImageRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    object_key: str = Field(min_length=1, max_length=500)
    filename: str = Field(min_length=1, max_length=255)


class EquipmentWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    model: str = Field(min_length=1, max_length=200)
    type: str = Field(min_length=1, max_length=100)
    manufacturer: str = Field(min_length=1, max_length=200)
    manufactured_at: date | None = None
    commissioned_at: date | None = None
    operating_hours: Decimal = Field(
        ge=0, max_digits=12, decimal_places=2
    )
    status: EquipmentStatus
    organization_id: str
    owner_user_id: str | None = None
    image_refs: list[ImageRef] = Field(default_factory=list)


class OrganizationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: OrganizationType
    code: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    parent_id: str
    sort_order: int = Field(ge=0)
    enabled: bool = True
    remark: str = Field(default="", max_length=1000)


class OrganizationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    sort_order: int = Field(ge=0)
    enabled: bool
    remark: str = Field(default="", max_length=1000)


class OrganizationRead(BaseModel):
    id: str
    type: OrganizationType
    code: str
    name: str
    parent_id: str | None
    sort_order: int
    enabled: bool
    remark: str


class OrganizationWriteResponse(OrganizationRead):
    audit_event_id: str


class EquipmentRead(BaseModel):
    id: str
    code: str
    name: str
    model: str
    type: str
    manufacturer: str
    manufactured_at: date | None
    commissioned_at: date | None
    operating_hours: Decimal
    status: EquipmentStatus
    organization_id: str
    owner_user_id: str | None
    image_refs: list[ImageRef]
    created_at: datetime
    updated_at: datetime


class EquipmentWriteResponse(EquipmentRead):
    audit_event_id: str
