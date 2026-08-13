from pydantic import BaseModel, ConfigDict, Field, field_validator


def validate_contact(value: str | None, *, kind: str) -> str | None:
    if value is None:
        return None
    import re
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$" if kind == "email" else r"^\+?[0-9][0-9 -]{5,28}$"
    if re.fullmatch(pattern, value) is None:
        raise ValueError(f"invalid {kind}")
    return value


class PasswordChangeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_password: str = Field(min_length=1, max_length=200)
    new_password: str = Field(min_length=8, max_length=200)
    confirm_password: str = Field(min_length=8, max_length=200)


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=200)
    role_ids: list[str] = Field(default_factory=list)
    display_name: str | None = Field(default=None, max_length=100)
    gender: str | None = Field(default=None, pattern="^(MALE|FEMALE|UNSPECIFIED)$")
    email: str | None = Field(default=None, max_length=254)
    phone: str | None = Field(default=None, max_length=30)
    remark: str | None = Field(default=None, max_length=2000)
    organization_id: str | None = None

    @field_validator("email")
    @classmethod
    def email_format(cls, value: str | None) -> str | None:
        return validate_contact(value, kind="email")

    @field_validator("phone")
    @classmethod
    def phone_format(cls, value: str | None) -> str | None:
        return validate_contact(value, kind="phone")


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool
    role_ids: list[str] = Field(default_factory=list)
    display_name: str | None = Field(default=None, max_length=100)
    gender: str | None = Field(default=None, pattern="^(MALE|FEMALE|UNSPECIFIED)$")
    email: str | None = Field(default=None, max_length=254)
    phone: str | None = Field(default=None, max_length=30)
    remark: str | None = Field(default=None, max_length=2000)
    organization_id: str | None = None

    @field_validator("email")
    @classmethod
    def email_format(cls, value: str | None) -> str | None:
        return validate_contact(value, kind="email")

    @field_validator("phone")
    @classmethod
    def phone_format(cls, value: str | None) -> str | None:
        return validate_contact(value, kind="phone")


class RoleCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str = Field(min_length=1, max_length=100, pattern="^[A-Z][A-Z0-9_]*$")
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=2000)
    enabled: bool = True
    permission_codes: list[str] = Field(default_factory=list)


class RoleUpdate(RoleCreate):
    pass


class PasswordResetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    new_password: str = Field(min_length=8, max_length=200)


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
    built_in: bool
    enabled: bool
    description: str | None
    user_count: int
    updated_at: str


class RoleWriteResponse(RoleRead):
    audit_event_id: str


class UserRead(BaseModel):
    id: str
    username: str
    enabled: bool
    role_ids: list[str]
    display_name: str | None
    gender: str | None
    email: str | None
    phone: str | None
    remark: str | None
    organization_id: str | None


class UserWriteResponse(UserRead):
    audit_event_id: str
