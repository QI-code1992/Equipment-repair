from dataclasses import dataclass

from app.modules.agent_config.models import AgentConfigModel


@dataclass(frozen=True, slots=True)
class ModelRequest:
    model_binding_id: str
    max_tokens: int
    reasoning_effort: str | None
    stream: bool


def build_model_request(config: AgentConfigModel) -> ModelRequest:
    """Translate the persisted AgentConfig into provider-neutral model arguments."""
    return ModelRequest(
        model_binding_id=config.model_binding_id or "",
        max_tokens=config.max_reply_tokens,
        reasoning_effort=(config.deep_thinking_level if config.deep_thinking_enabled else None),
        stream=config.streaming_enabled,
    )
