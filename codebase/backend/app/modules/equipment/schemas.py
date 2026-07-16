from pydantic import BaseModel, ConfigDict, Field

from app.modules.equipment.models import OrganizationType


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
