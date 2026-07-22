from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ThreadCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent_id: str
    business_context: dict[str, Any] = Field(default_factory=dict)


class MessageCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=20_000)
    attachment_refs: list[dict[str, str]] = Field(default_factory=list)


class ResumeCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirmation: dict[str, Any] = Field(default_factory=dict)
    resume: bool = True
