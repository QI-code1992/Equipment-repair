from collections.abc import Iterable

import pytest

from app.modules.agent_config.domain import AgentConfig, AgentId, ModelCapability


class FakeAgentConfigRepository:
    def __init__(self, configs: Iterable[AgentConfig] = ()) -> None:
        self.configs = {config.agent_id: config for config in configs}

    def get(self, agent_id: AgentId) -> AgentConfig | None:
        return self.configs.get(agent_id)

    def list_all(self) -> list[AgentConfig]:
        return list(reversed(tuple(self.configs.values())))

    def insert_if_absent(self, config: AgentConfig) -> AgentConfig:
        return self.configs.setdefault(config.agent_id, config)

    def save(self, config: AgentConfig) -> AgentConfig:
        self.configs[config.agent_id] = config
        return config


class FakeModelCatalog:
    def __init__(self) -> None:
        self.models = {
            "chat-basic": ModelCapability("chat-basic", "基础模型", False),
            "reasoning-pro": ModelCapability("reasoning-pro", "推理模型", True),
        }
        self.provider_secrets = {"chat-basic": "never-return-this-api-key"}

    def get(self, binding_id: str) -> ModelCapability | None:
        return self.models.get(binding_id)


@pytest.fixture
def repository() -> FakeAgentConfigRepository:
    return FakeAgentConfigRepository()


@pytest.fixture
def model_catalog() -> FakeModelCatalog:
    return FakeModelCatalog()
