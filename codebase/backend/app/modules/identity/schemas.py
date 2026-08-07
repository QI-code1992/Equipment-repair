from pydantic import BaseModel, ConfigDict, Field


class PasswordChangeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_password: str = Field(min_length=1, max_length=200)
    new_password: str = Field(min_length=8, max_length=200)
    confirm_password: str = Field(min_length=8, max_length=200)


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=200)
    role_ids: list[str] = Field(min_length=1)


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool
    role_ids: list[str] = Field(min_length=1)


class RolePermissionsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    permission_codes: list[str]


class PermissionRead(BaseModel):
    code: str


class RoleRead(BaseModel):
    id: str
    code: str
    name: str
    permission_codes: list[str]


class RoleWriteResponse(RoleRead):
    audit_event_id: str


class UserRead(BaseModel):
    id: str
    username: str
    enabled: bool
    role_ids: list[str]


class UserWriteResponse(UserRead):
    audit_event_id: str
