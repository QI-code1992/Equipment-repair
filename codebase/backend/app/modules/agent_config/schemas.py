from pydantic import BaseModel, ConfigDict, Field

from .domain import DeepThinkingLevel


class ProviderWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=100)
    secret_ref: str = Field(min_length=1, max_length=500)
    enabled: bool


class ProviderRead(BaseModel):
    id: str
    name: str
    enabled: bool


class ProviderWriteResponse(ProviderRead):
    audit_event_id: str


class BindingWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider_id: str = Field(min_length=1, max_length=36)
    name: str = Field(min_length=1, max_length=100)
    model_name: str = Field(min_length=1, max_length=200)
    supports_reasoning: bool
    enabled: bool


class BindingRead(BindingWrite):
    id: str


class BindingWriteResponse(BindingRead):
    audit_event_id: str


class AgentConfigWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent_id: str = Field(min_length=1, max_length=36)
    enabled: bool
    model_binding_id: str | None = Field(default=None, max_length=36)
    knowledge_dataset_ids: list[str] = Field(default_factory=list)
    streaming_enabled: bool
    suggestions_enabled: bool
    sources_enabled: bool
    context_turns: int = Field(ge=0, le=10)
    retrieval_limit: int = Field(ge=1, le=20)
    similarity_threshold: float = Field(ge=0.0, le=1.0)
    deep_thinking_enabled: bool
    deep_thinking_level: DeepThinkingLevel
    max_reply_tokens: int = Field(ge=512, le=8192)


class ModelCapabilityRead(BaseModel):
    binding_id: str
    display_name: str
    supports_reasoning: bool


class AgentConfigRead(AgentConfigWrite):
    model_capability: ModelCapabilityRead | None


class AgentConfigWriteResponse(AgentConfigRead):
    audit_event_id: str


class DeleteResponse(BaseModel):
    id: str
    audit_event_id: str
