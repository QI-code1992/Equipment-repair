# TASK-006 非数据库实现 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不依赖数据库、真实模型、Docker 或正式应用挂载的前提下，实现四个 Agent 的独立配置领域模型、服务契约、配置快照与可注入 FastAPI API 契约。

**Architecture:** 使用冻结 `dataclass` 表达配置、模型公开能力和运行快照，以 `Protocol` 定义仓储及模型目录两个外部端口。`AgentConfigService` 负责身份、隔离、参数和推理能力校验；路由工厂只接收已注入服务，测试 Fake 仅存在于测试目录，路由不挂载到 `app.main`。

**Tech Stack:** Python 3.13、FastAPI 0.115+、Pydantic 2（FastAPI 传递依赖）、pytest 9、标准库 `dataclasses` / `enum` / `typing.Protocol`。

## Global Constraints

- 只实现 TASK-006 非数据库切片；SQLAlchemy、Alembic、PostgreSQL、迁移、事务和共享数据模型仍 `Blocked By TASK-002`。
- 稳定 `agent_id` 仅为 `fault_reporting`、`metric_query`、`operation_guidance`、`fault_diagnosis`，顺序固定。
- 正式生产代码不得提供进程内、JSON 文件或其他临时仓储；Fake 只能放在测试目录。
- 不修改或挂载 `codebase/backend/app/main.py`，不实现 `/test-runs`，不调用真实模型、LangGraph、SSE 或 RAGFlow。
- 不修改 `codebase/infra/`、`codebase/frontend/`、`03-ui-prototype/`、数据库迁移或公开 Stage 4 规格。
- 不新增生产依赖，不实现 Agent 版本、发布、回滚或兼容层。
- 配置、响应、异常和日志不得包含密码、Token、API Key、请求头或供应商凭据。
- 严格执行 RED → GREEN → REFACTOR；每次 RED 必须表现为预期行为断言失败，测试收集、导入、环境、第三方依赖或语法错误均不能冒充 RED。
- 各任务展示的测试代码是最终目标状态，不得一次性粘贴后再实现；必须逐个行为加入测试并运行。新模块尚不存在时，首个测试使用 `importlib` 捕获 `ModuleNotFoundError` 并调用 `pytest.fail()` 形成明确失败，再创建最小模块；后续每个类型、方法和分支继续独立完成 RED → GREEN。
- 正式验收使用 Python `>=3.13,<3.14`；本机 bundled Python 3.12 只允许做语法检查，不能替代 pytest 验收。
- 本计划不修改 `pyproject.toml`，沿用现有 FastAPI、httpx、pytest 版本范围。

---

## 文件结构

| 文件 | 单一职责 |
|---|---|
| `codebase/backend/app/modules/__init__.py` | 标记后端业务模块包。 |
| `codebase/backend/app/modules/agent_config/__init__.py` | 仅导出 TASK-007/数据库适配器需要的稳定公开类型。 |
| `codebase/backend/app/modules/agent_config/domain.py` | Agent ID、深度等级、配置、公开模型能力和不可变快照。 |
| `codebase/backend/app/modules/agent_config/service.py` | 外部端口、稳定错误、隔离保存、能力校验与快照生成。 |
| `codebase/backend/app/modules/agent_config/api.py` | Pydantic 请求/响应模型、错误映射和可注入路由工厂。 |
| `codebase/backend/tests/modules/conftest.py` | 只供测试使用的仓储 Fake、模型目录 Fake 与 fixture。 |
| `codebase/backend/tests/modules/test_agent_config.py` | 领域值、初始化、隔离、校验和快照服务测试。 |
| `codebase/backend/tests/modules/test_agent_config_api.py` | GET/PUT API 契约、错误结构和敏感字段测试。 |

---

### Task 1: 不可变领域模型与安全默认配置

**Files:**
- Create: `codebase/backend/app/modules/__init__.py`
- Create: `codebase/backend/app/modules/agent_config/__init__.py`
- Create: `codebase/backend/app/modules/agent_config/domain.py`
- Create: `codebase/backend/tests/modules/test_agent_config.py`

**Interfaces:**
- Consumes: 无。
- Produces: `AgentId`、`DeepThinkingLevel`、`ModelCapability`、`AgentConfig.default_for()`、`AgentConfigSnapshot`。

- [ ] **Step 1: 创建包文件，并写领域模型失败测试**

`test_agent_config.py` 首批测试使用以下内容：

```python
from dataclasses import FrozenInstanceError

import pytest

from app.modules.agent_config.domain import AgentConfig, AgentId, DeepThinkingLevel


@pytest.mark.parametrize(
    "raw_agent_id",
    ["fault_reporting", "metric_query", "operation_guidance", "fault_diagnosis"],
)
def test_all_supported_agent_ids_are_stable(raw_agent_id: str) -> None:
    assert AgentId(raw_agent_id).value == raw_agent_id


def test_unknown_agent_id_is_rejected() -> None:
    with pytest.raises(ValueError):
        AgentId("shared_default")


def test_default_config_is_safe_and_agent_specific() -> None:
    config = AgentConfig.default_for(AgentId.FAULT_REPORTING)

    assert config.agent_id is AgentId.FAULT_REPORTING
    assert config.enabled is False
    assert config.model_binding_id is None
    assert config.knowledge_dataset_ids == ()
    assert config.deep_thinking_enabled is False
    assert config.deep_thinking_level is DeepThinkingLevel.MEDIUM
    assert config.context_turns == 3
    assert config.retrieval_limit == 6
    assert config.similarity_threshold == 0.62
    assert config.max_reply_tokens == 4096


def test_config_is_immutable() -> None:
    config = AgentConfig.default_for(AgentId.METRIC_QUERY)

    with pytest.raises(FrozenInstanceError):
        config.enabled = True  # type: ignore[misc]
```

- [ ] **Step 2: 运行测试并确认 RED**

Run:

```bash
cd codebase/backend
python3.13 -m pytest tests/modules/test_agent_config.py -q
```

Expected: 首个逐行为测试以 `pytest.fail("agent_config domain module is missing")` 失败；不得出现收集错误。随后只创建使该断言通过的最小包/模块，再逐项加入本任务其余测试并观察各自的行为断言失败。若 `python3.13` 不可用，必须停止处理环境，不能记录为 RED。

- [ ] **Step 3: 实现最小领域模型**

`domain.py` 写入：

```python
from dataclasses import dataclass
from enum import StrEnum


class AgentId(StrEnum):
    FAULT_REPORTING = "fault_reporting"
    METRIC_QUERY = "metric_query"
    OPERATION_GUIDANCE = "operation_guidance"
    FAULT_DIAGNOSIS = "fault_diagnosis"


class DeepThinkingLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class ModelCapability:
    binding_id: str
    display_name: str
    supports_reasoning: bool


@dataclass(frozen=True, slots=True)
class AgentConfig:
    agent_id: AgentId
    enabled: bool
    model_binding_id: str | None
    knowledge_dataset_ids: tuple[str, ...]
    streaming_enabled: bool
    suggestions_enabled: bool
    sources_enabled: bool
    context_turns: int
    retrieval_limit: int
    similarity_threshold: float
    deep_thinking_enabled: bool
    deep_thinking_level: DeepThinkingLevel
    max_reply_tokens: int

    @classmethod
    def default_for(cls, agent_id: AgentId) -> "AgentConfig":
        return cls(
            agent_id=agent_id,
            enabled=False,
            model_binding_id=None,
            knowledge_dataset_ids=(),
            streaming_enabled=True,
            suggestions_enabled=True,
            sources_enabled=True,
            context_turns=3,
            retrieval_limit=6,
            similarity_threshold=0.62,
            deep_thinking_enabled=False,
            deep_thinking_level=DeepThinkingLevel.MEDIUM,
            max_reply_tokens=4096,
        )


@dataclass(frozen=True, slots=True)
class AgentConfigSnapshot:
    agent_id: AgentId
    enabled: bool
    model_binding_id: str
    knowledge_dataset_ids: tuple[str, ...]
    streaming_enabled: bool
    suggestions_enabled: bool
    sources_enabled: bool
    context_turns: int
    retrieval_limit: int
    similarity_threshold: float
    deep_thinking_enabled: bool
    deep_thinking_level: DeepThinkingLevel
    max_reply_tokens: int
```

`app/modules/__init__.py` 保持空文件；`agent_config/__init__.py` 暂保持空文件，最后任务统一冻结公开导出。

- [ ] **Step 4: 运行领域测试并确认 GREEN**

Run: `cd codebase/backend && python3.13 -m pytest tests/modules/test_agent_config.py -q`

Expected: `7 passed`。

- [ ] **Step 5: 提交领域模型检查点**

```bash
git add codebase/backend/app/modules codebase/backend/tests/modules/test_agent_config.py
git commit -m "feat(task-006): add immutable agent configuration domain"
```

---

### Task 2: 隔离配置服务、外部端口与快照校验

**Files:**
- Create: `codebase/backend/app/modules/agent_config/service.py`
- Create: `codebase/backend/tests/modules/conftest.py`
- Modify: `codebase/backend/tests/modules/test_agent_config.py`

**Interfaces:**
- Consumes: Task 1 的 `AgentId`、`AgentConfig`、`ModelCapability`、`AgentConfigSnapshot`。
- Produces: `AgentConfigRepository.get/list_all/insert_if_absent/save`、`ModelCatalog.get`、`AgentConfigError`、`ValidationIssue`、`parse_agent_id()`、`AgentConfigService.initialize/get/list_all/save/build_snapshot/model_capability`。

- [ ] **Step 1: 创建测试 Fake**

`conftest.py` 写入：

```python
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
```

- [ ] **Step 2: 追加服务失败测试**

在 `test_agent_config.py` 导入 `replace`、全部领域类型和服务类型，然后追加以下测试：

```python
from dataclasses import replace

from app.modules.agent_config.domain import AgentConfigSnapshot
from app.modules.agent_config.service import AgentConfigError, AgentConfigService


def enabled_config(agent_id: AgentId, model_binding_id: str = "reasoning-pro") -> AgentConfig:
    return replace(
        AgentConfig.default_for(agent_id),
        enabled=True,
        model_binding_id=model_binding_id,
    )


def test_initialize_only_creates_requested_agent(repository, model_catalog) -> None:
    service = AgentConfigService(repository, model_catalog)

    created = service.initialize("fault_reporting")

    assert created.agent_id is AgentId.FAULT_REPORTING
    assert set(repository.configs) == {AgentId.FAULT_REPORTING}


def test_repeated_initialize_preserves_existing_config(repository, model_catalog) -> None:
    existing = enabled_config(AgentId.METRIC_QUERY)
    repository.save(existing)
    service = AgentConfigService(repository, model_catalog)

    assert service.initialize("metric_query") is existing


def test_save_changes_only_target_agent(repository, model_catalog) -> None:
    original_reporting = enabled_config(AgentId.FAULT_REPORTING)
    original_query = enabled_config(AgentId.METRIC_QUERY)
    repository.save(original_reporting)
    repository.save(original_query)
    service = AgentConfigService(repository, model_catalog)

    changed = replace(original_reporting, context_turns=8)
    service.save("fault_reporting", changed)

    assert repository.get(AgentId.FAULT_REPORTING) == changed
    assert repository.get(AgentId.METRIC_QUERY) is original_query


def test_non_reasoning_model_rejects_deep_thinking(repository, model_catalog) -> None:
    candidate = replace(
        enabled_config(AgentId.FAULT_DIAGNOSIS, "chat-basic"),
        deep_thinking_enabled=True,
    )
    service = AgentConfigService(repository, model_catalog)

    with pytest.raises(AgentConfigError) as caught:
        service.save("fault_diagnosis", candidate)

    assert caught.value.code == "MODEL_REASONING_UNSUPPORTED"
    assert caught.value.issues[0].field == "deep_thinking_enabled"


def test_reasoning_model_builds_immutable_secret_free_snapshot(repository, model_catalog) -> None:
    candidate = replace(
        enabled_config(AgentId.FAULT_DIAGNOSIS),
        deep_thinking_enabled=True,
        deep_thinking_level=DeepThinkingLevel.HIGH,
    )
    repository.save(candidate)
    service = AgentConfigService(repository, model_catalog)

    snapshot = service.build_snapshot("fault_diagnosis")

    assert isinstance(snapshot, AgentConfigSnapshot)
    assert snapshot.deep_thinking_level is DeepThinkingLevel.HIGH
    assert "secret" not in repr(snapshot).lower()
    with pytest.raises(FrozenInstanceError):
        snapshot.context_turns = 1  # type: ignore[misc]


def test_enabled_config_without_model_cannot_build_snapshot(repository, model_catalog) -> None:
    repository.save(replace(AgentConfig.default_for(AgentId.OPERATION_GUIDANCE), enabled=True))
    service = AgentConfigService(repository, model_catalog)

    with pytest.raises(AgentConfigError) as caught:
        service.build_snapshot("operation_guidance")

    assert caught.value.code == "AGENT_CONFIG_INVALID"
    assert caught.value.issues[0].field == "model_binding_id"


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("context_turns", 11),
        ("retrieval_limit", 0),
        ("similarity_threshold", 1.1),
        ("max_reply_tokens", 511),
    ],
)
def test_out_of_range_parameter_is_rejected(
    field: str, invalid_value: int | float, repository, model_catalog
) -> None:
    candidate = replace(enabled_config(AgentId.FAULT_REPORTING), **{field: invalid_value})
    service = AgentConfigService(repository, model_catalog)

    with pytest.raises(AgentConfigError) as caught:
        service.save("fault_reporting", candidate)

    assert caught.value.code == "AGENT_CONFIG_INVALID"
    assert caught.value.issues[0].field == field
```

- [ ] **Step 3: 运行新增测试并确认 RED**

Run: `cd codebase/backend && python3.13 -m pytest tests/modules/test_agent_config.py -q`

Expected: 首个服务测试通过 `importlib` 捕获缺失模块并以 `pytest.fail("agent_config service module is missing")` 形成失败；不得出现收集错误。创建最小模块后，按初始化、隔离保存、推理能力、快照和参数边界顺序逐个加入测试，每个测试都先因目标行为缺失而失败。

- [ ] **Step 4: 实现服务、端口、稳定错误和共享校验**

`service.py` 实现以下完整契约：

```python
from dataclasses import dataclass
from typing import Protocol

from .domain import AgentConfig, AgentConfigSnapshot, AgentId, ModelCapability


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    field: str
    message: str


class AgentConfigError(Exception):
    def __init__(self, code: str, message: str, *issues: ValidationIssue) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.issues = issues


class AgentConfigRepository(Protocol):
    def get(self, agent_id: AgentId) -> AgentConfig | None: ...
    def list_all(self) -> list[AgentConfig]: ...
    def insert_if_absent(self, config: AgentConfig) -> AgentConfig: ...
    def save(self, config: AgentConfig) -> AgentConfig: ...


class ModelCatalog(Protocol):
    def get(self, binding_id: str) -> ModelCapability | None: ...


def parse_agent_id(raw_agent_id: str | AgentId) -> AgentId:
    try:
        return AgentId(raw_agent_id)
    except ValueError as error:
        raise AgentConfigError(
            "UNKNOWN_AGENT_ID",
            "未知 Agent 标识。",
            ValidationIssue("agent_id", "仅允许四个已登记的 agent_id。"),
        ) from error


class AgentConfigService:
    def __init__(self, repository: AgentConfigRepository, model_catalog: ModelCatalog) -> None:
        self._repository = repository
        self._model_catalog = model_catalog

    def initialize(self, agent_id: str | AgentId) -> AgentConfig:
        parsed = parse_agent_id(agent_id)
        return self._repository.insert_if_absent(AgentConfig.default_for(parsed))

    def get(self, agent_id: str | AgentId) -> AgentConfig:
        parsed = parse_agent_id(agent_id)
        config = self._repository.get(parsed)
        if config is None:
            raise AgentConfigError(
                "AGENT_CONFIG_NOT_FOUND",
                "Agent 配置尚未初始化。",
                ValidationIssue("agent_id", "目标 Agent 没有当前有效配置。"),
            )
        return config

    def list_all(self) -> list[AgentConfig]:
        configs = {config.agent_id: config for config in self._repository.list_all()}
        return [configs[agent_id] for agent_id in AgentId if agent_id in configs]

    def save(self, agent_id: str | AgentId, candidate: AgentConfig) -> AgentConfig:
        parsed = parse_agent_id(agent_id)
        if candidate.agent_id is not parsed:
            raise AgentConfigError(
                "AGENT_CONFIG_INVALID",
                "路径与配置身份不一致。",
                ValidationIssue("agent_id", "请求体 agent_id 必须与路径一致。"),
            )
        self._validate(candidate, require_enabled=False)
        return self._repository.save(candidate)

    def build_snapshot(self, agent_id: str | AgentId) -> AgentConfigSnapshot:
        config = self.get(agent_id)
        self._validate(config, require_enabled=True)
        assert config.model_binding_id is not None
        return AgentConfigSnapshot(
            agent_id=config.agent_id,
            enabled=config.enabled,
            model_binding_id=config.model_binding_id,
            knowledge_dataset_ids=tuple(config.knowledge_dataset_ids),
            streaming_enabled=config.streaming_enabled,
            suggestions_enabled=config.suggestions_enabled,
            sources_enabled=config.sources_enabled,
            context_turns=config.context_turns,
            retrieval_limit=config.retrieval_limit,
            similarity_threshold=config.similarity_threshold,
            deep_thinking_enabled=config.deep_thinking_enabled,
            deep_thinking_level=config.deep_thinking_level,
            max_reply_tokens=config.max_reply_tokens,
        )

    def model_capability(self, binding_id: str | None) -> ModelCapability | None:
        return None if binding_id is None else self._model_catalog.get(binding_id)

    def _validate(self, config: AgentConfig, *, require_enabled: bool) -> None:
        if require_enabled and not config.enabled:
            raise AgentConfigError("AGENT_DISABLED", "Agent 未启用。")

        ranges = (
            ("context_turns", 0 <= config.context_turns <= 10, "必须在 0 到 10 之间。"),
            ("retrieval_limit", 1 <= config.retrieval_limit <= 20, "必须在 1 到 20 之间。"),
            (
                "similarity_threshold",
                0.0 <= config.similarity_threshold <= 1.0,
                "必须在 0.0 到 1.0 之间。",
            ),
            (
                "max_reply_tokens",
                512 <= config.max_reply_tokens <= 8192,
                "必须在 512 到 8192 之间。",
            ),
        )
        for field, valid, message in ranges:
            if not valid:
                raise AgentConfigError(
                    "AGENT_CONFIG_INVALID",
                    "Agent 配置参数无效。",
                    ValidationIssue(field, message),
                )

        model_required = config.enabled or config.deep_thinking_enabled
        if model_required and not config.model_binding_id:
            raise AgentConfigError(
                "AGENT_CONFIG_INVALID",
                "Agent 配置缺少模型绑定。",
                ValidationIssue("model_binding_id", "启用或深度思考配置必须绑定模型。"),
            )
        capability = self.model_capability(config.model_binding_id)
        if config.model_binding_id and capability is None:
            raise AgentConfigError(
                "AGENT_CONFIG_INVALID",
                "模型绑定不存在。",
                ValidationIssue("model_binding_id", "请选择模型目录中的有效绑定。"),
            )
        if config.deep_thinking_enabled and capability and not capability.supports_reasoning:
            raise AgentConfigError(
                "MODEL_REASONING_UNSUPPORTED",
                "当前模型不支持深度思考。",
                ValidationIssue("deep_thinking_enabled", "请关闭深度思考或更换推理模型。"),
            )
```

- [ ] **Step 5: 运行服务测试并确认 GREEN**

Run: `cd codebase/backend && python3.13 -m pytest tests/modules/test_agent_config.py -q`

Expected: `17 passed`。

- [ ] **Step 6: 提交服务检查点**

```bash
git add codebase/backend/app/modules/agent_config/service.py codebase/backend/tests/modules
git commit -m "feat(task-006): enforce independent agent configurations"
```

---

### Task 3: 可注入 FastAPI 配置 API 契约

**Files:**
- Create: `codebase/backend/app/modules/agent_config/api.py`
- Create: `codebase/backend/tests/modules/test_agent_config_api.py`
- Modify: `codebase/backend/app/modules/agent_config/__init__.py`

**Interfaces:**
- Consumes: Task 2 的 `AgentConfigService`、`AgentConfigError`、`parse_agent_id()`。
- Produces: `create_agent_config_router(service: AgentConfigService) -> APIRouter`；GET list、GET one、PUT one；公开包导出数据库适配器和 TASK-007 所需类型。

- [ ] **Step 1: 写 API 失败测试和独立测试应用工厂**

`test_agent_config_api.py` 写入：

```python
from dataclasses import replace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.agent_config.api import create_agent_config_router
from app.modules.agent_config.domain import AgentConfig, AgentId
from app.modules.agent_config.service import AgentConfigService


def make_client(repository, model_catalog) -> TestClient:
    service = AgentConfigService(repository, model_catalog)
    app = FastAPI()
    app.include_router(create_agent_config_router(service))
    return TestClient(app)


def initialize_all(repository) -> None:
    for agent_id in AgentId:
        repository.save(AgentConfig.default_for(agent_id))


def test_list_returns_four_configs_in_stable_order(repository, model_catalog) -> None:
    initialize_all(repository)
    response = make_client(repository, model_catalog).get("/api/agent-configs")

    assert response.status_code == 200
    assert [item["agent_id"] for item in response.json()] == [item.value for item in AgentId]


def test_get_unknown_agent_does_not_fall_back(repository, model_catalog) -> None:
    repository.save(AgentConfig.default_for(AgentId.FAULT_REPORTING))
    response = make_client(repository, model_catalog).get("/api/agent-configs/shared_default")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "UNKNOWN_AGENT_ID"


def test_put_rejects_unsupported_reasoning_with_stable_error(repository, model_catalog) -> None:
    payload = {
        "agent_id": "fault_diagnosis",
        "enabled": True,
        "model_binding_id": "chat-basic",
        "knowledge_dataset_ids": [],
        "streaming_enabled": True,
        "suggestions_enabled": True,
        "sources_enabled": True,
        "context_turns": 3,
        "retrieval_limit": 6,
        "similarity_threshold": 0.62,
        "deep_thinking_enabled": True,
        "deep_thinking_level": "medium",
        "max_reply_tokens": 4096,
    }

    response = make_client(repository, model_catalog).put(
        "/api/agent-configs/fault_diagnosis", json=payload
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "MODEL_REASONING_UNSUPPORTED"
    assert response.json()["detail"]["fields"][0]["field"] == "deep_thinking_enabled"


def test_get_exposes_capability_without_provider_secret(repository, model_catalog) -> None:
    config = replace(
        AgentConfig.default_for(AgentId.METRIC_QUERY),
        enabled=True,
        model_binding_id="reasoning-pro",
    )
    repository.save(config)

    response = make_client(repository, model_catalog).get("/api/agent-configs/metric_query")

    assert response.status_code == 200
    assert response.json()["model_capability"] == {
        "binding_id": "reasoning-pro",
        "display_name": "推理模型",
        "supports_reasoning": True,
    }
    assert "never-return-this-api-key" not in response.text
    assert "api_key" not in response.text.lower()
    assert "access_token" not in response.text.lower()
    assert "provider_secret" not in response.text.lower()
```

- [ ] **Step 2: 运行 API 测试并确认 RED**

Run: `cd codebase/backend && python3.13 -m pytest tests/modules/test_agent_config_api.py -q`

Expected: 首个 API 测试通过 `importlib` 捕获缺失模块并以 `pytest.fail("agent_config api module is missing")` 形成失败；不得出现收集错误。创建最小模块后，按列表、未知 Agent、推理错误和敏感字段顺序逐个加入契约测试并分别确认 RED。

- [ ] **Step 3: 实现 Pydantic 映射、错误响应和路由工厂**

`api.py` 写入：

```python
from typing import NoReturn

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .domain import AgentConfig, DeepThinkingLevel
from .service import AgentConfigError, AgentConfigService, parse_agent_id


class AgentConfigRequest(BaseModel):
    agent_id: str
    enabled: bool
    model_binding_id: str | None
    knowledge_dataset_ids: list[str]
    streaming_enabled: bool
    suggestions_enabled: bool
    sources_enabled: bool
    context_turns: int
    retrieval_limit: int
    similarity_threshold: float
    deep_thinking_enabled: bool
    deep_thinking_level: DeepThinkingLevel
    max_reply_tokens: int


class ModelCapabilityResponse(BaseModel):
    binding_id: str
    display_name: str
    supports_reasoning: bool


class AgentConfigResponse(AgentConfigRequest):
    model_capability: ModelCapabilityResponse | None


def _raise_http(error: AgentConfigError) -> NoReturn:
    status_code = 404 if error.code in {"UNKNOWN_AGENT_ID", "AGENT_CONFIG_NOT_FOUND"} else 422
    raise HTTPException(
        status_code=status_code,
        detail={
            "code": error.code,
            "message": error.message,
            "fields": [
                {"field": issue.field, "message": issue.message} for issue in error.issues
            ],
        },
    ) from error


def _response(service: AgentConfigService, config: AgentConfig) -> AgentConfigResponse:
    capability = service.model_capability(config.model_binding_id)
    return AgentConfigResponse(
        agent_id=config.agent_id.value,
        enabled=config.enabled,
        model_binding_id=config.model_binding_id,
        knowledge_dataset_ids=list(config.knowledge_dataset_ids),
        streaming_enabled=config.streaming_enabled,
        suggestions_enabled=config.suggestions_enabled,
        sources_enabled=config.sources_enabled,
        context_turns=config.context_turns,
        retrieval_limit=config.retrieval_limit,
        similarity_threshold=config.similarity_threshold,
        deep_thinking_enabled=config.deep_thinking_enabled,
        deep_thinking_level=config.deep_thinking_level,
        max_reply_tokens=config.max_reply_tokens,
        model_capability=(
            None
            if capability is None
            else ModelCapabilityResponse(
                binding_id=capability.binding_id,
                display_name=capability.display_name,
                supports_reasoning=capability.supports_reasoning,
            )
        ),
    )


def create_agent_config_router(service: AgentConfigService) -> APIRouter:
    router = APIRouter(prefix="/api/agent-configs", tags=["agent-configs"])

    @router.get("", response_model=list[AgentConfigResponse])
    def list_agent_configs() -> list[AgentConfigResponse]:
        return [_response(service, config) for config in service.list_all()]

    @router.get("/{agent_id}", response_model=AgentConfigResponse)
    def get_agent_config(agent_id: str) -> AgentConfigResponse:
        try:
            return _response(service, service.get(agent_id))
        except AgentConfigError as error:
            _raise_http(error)

    @router.put("/{agent_id}", response_model=AgentConfigResponse)
    def save_agent_config(agent_id: str, payload: AgentConfigRequest) -> AgentConfigResponse:
        try:
            candidate = AgentConfig(
                agent_id=parse_agent_id(payload.agent_id),
                enabled=payload.enabled,
                model_binding_id=payload.model_binding_id,
                knowledge_dataset_ids=tuple(payload.knowledge_dataset_ids),
                streaming_enabled=payload.streaming_enabled,
                suggestions_enabled=payload.suggestions_enabled,
                sources_enabled=payload.sources_enabled,
                context_turns=payload.context_turns,
                retrieval_limit=payload.retrieval_limit,
                similarity_threshold=payload.similarity_threshold,
                deep_thinking_enabled=payload.deep_thinking_enabled,
                deep_thinking_level=payload.deep_thinking_level,
                max_reply_tokens=payload.max_reply_tokens,
            )
            return _response(service, service.save(agent_id, candidate))
        except AgentConfigError as error:
            _raise_http(error)

    return router
```

- [ ] **Step 4: 冻结包的公开导出**

`agent_config/__init__.py` 写入：

```python
from .api import create_agent_config_router
from .domain import (
    AgentConfig,
    AgentConfigSnapshot,
    AgentId,
    DeepThinkingLevel,
    ModelCapability,
)
from .service import AgentConfigRepository, AgentConfigService, ModelCatalog

__all__ = [
    "AgentConfig",
    "AgentConfigRepository",
    "AgentConfigService",
    "AgentConfigSnapshot",
    "AgentId",
    "DeepThinkingLevel",
    "ModelCapability",
    "ModelCatalog",
    "create_agent_config_router",
]
```

- [ ] **Step 5: 运行 API 与领域测试并确认 GREEN**

Run:

```bash
cd codebase/backend
python3.13 -m pytest tests/modules/test_agent_config.py tests/modules/test_agent_config_api.py -q
```

Expected: `21 passed`。

- [ ] **Step 6: 确认未挂载正式应用且不存在生产 Fake**

Run:

```bash
git diff -- codebase/backend/app/main.py
rg -n "Fake|InMemory|include_router\(create_agent_config_router|test-runs|sqlalchemy|alembic" codebase/backend/app
```

Expected: `app/main.py` 无 diff；扫描不出现生产 Fake、路由挂载、test-runs、SQLAlchemy 或 Alembic。`create_agent_config_router` 的定义/导出命中允许存在。

- [ ] **Step 7: 提交 API 检查点**

```bash
git add codebase/backend/app/modules/agent_config codebase/backend/tests/modules/test_agent_config_api.py
git commit -m "feat(task-006): add injectable agent configuration API"
```

---

### Task 4: 全量回归、差异验收与非数据库切片证据

**Files:**
- Modify after real results exist: `05-development/DEV_NOTES.md`
- Modify after real results exist: `05-development/SELF_TEST.md`
- Modify after review exists: `05-development/CODE_REVIEW.md`
- Modify after implementation SHA exists: `05-development/COMMIT_LOG.md`
- Modify after remote SHA exists: `05-development/CHECKPOINTS.md`
- Modify after review and push exist: `workflow/DEV_TO_PM_HANDOFF.md`

**Interfaces:**
- Consumes: Tasks 1–3 的实现提交和真实命令输出。
- Produces: 可供 DEV-001 审查的 TASK-006 非数据库切片检查点；不产生 TASK-006 完成状态，不解锁 TASK-007。

- [ ] **Step 1: 使用 Python 3.13 执行模块测试与后端全量回归**

Run:

```bash
cd codebase/backend
python3.13 -m pytest tests/modules/test_agent_config.py tests/modules/test_agent_config_api.py -q
python3.13 -m pytest -q
```

Expected: module suite `21 passed`; full backend suite `25 passed`。任何 warning、skip 或环境错误均逐项记录，不能归类为通过。

- [ ] **Step 2: 执行语法、空白和范围检查**

Run from repository root:

```bash
python3.13 -m compileall -q codebase/backend/app codebase/backend/tests
git diff --check 42098613ffa20faed3bb0dcb842a0121722565bd..HEAD
git diff --name-status 42098613ffa20faed3bb0dcb842a0121722565bd..HEAD
git status --short
```

Expected: compile and `diff --check` exit 0；文件清单只包含本计划文件及 Stage 5 证据；没有 `codebase/infra/`、`codebase/frontend/`、`03-ui-prototype/`、迁移或 `app/main.py` 变更；提交后工作树干净。

- [ ] **Step 3: 独立审查实现差异**

Review exact range from `42098613ffa20faed3bb0dcb842a0121722565bd` to current implementation HEAD against:

```text
规格符合性：四 Agent 稳定 ID、单独初始化、单独保存、固定排序、快照。
安全性：无密钥字段、无原始异常回显、无生产 Fake、无易失存储。
边界：无数据库、模型调用、LangGraph、SSE、test-runs、前端、Docker 修改。
质量：无新增依赖、兼容层、无关重构或未使用导入；Protocol 仅两个外部边界。
测试：RED 证据真实，模块 21 cases，全量 25 cases，错误码和字段断言明确。
```

发现问题时回到对应 Task 的 RED → GREEN 周期；审查未通过不得写交接状态。

- [ ] **Step 4: 用真实结果更新 Stage 5 证据台账**

仅在 Step 1–3 全部完成后写入六个既有台账。每份记录必须使用命令实际输出和 `git rev-parse HEAD` 返回的完整 SHA，并包含以下确定结论：

```text
状态：TASK-006 非数据库切片已验证，TASK-006 总任务仍未完成。
已完成：领域模型、两个外部端口、独立初始化/读取/保存、模型推理能力校验、不可变配置快照、未挂载 API 契约。
未完成：数据库仓储、迁移、事务/并发唯一性、认证/权限/审计接入、正式路由挂载、真实模型测试、前端集成。
依赖：数据库部分继续 Blocked By TASK-002；TASK-007 不得解锁。
环境声明：DEV-002 未执行或宣称 Docker、Compose、RAGFlow 验证通过。
工程声明：未新增生产依赖、兼容代码或范围外抽象；无无关修改。
```

`CHECKPOINTS.md` 的新条目标识为 `FCP-006-NDB`，明确它是可恢复的非数据库实现检查点，不是 TASK-006 完成门禁。

- [ ] **Step 5: 提交证据台账**

```bash
git add 05-development/DEV_NOTES.md 05-development/SELF_TEST.md \
  05-development/CODE_REVIEW.md 05-development/COMMIT_LOG.md \
  05-development/CHECKPOINTS.md workflow/DEV_TO_PM_HANDOFF.md
git commit -m "docs(task-006): record non-database slice evidence"
```

- [ ] **Step 6: 推送并交给 DEV-001 集成审查**

```bash
git push origin codex/task-006-agent-config
git status --short --branch
```

Expected: push succeeds；本地分支与 `origin/codex/task-006-agent-config` 同步；工作树干净。交接只请求 DEV-001 审查两个端口、认证/审计接入点和后续数据库适配，不请求合并数据库实现。

---

## 计划自检

- 规格覆盖：设计第 2–9 节均映射到 Task 1–4；四 Agent 隔离、能力校验、快照、API 安全和禁止范围都有测试或扫描证据。
- 类型一致：`AgentId`、`DeepThinkingLevel`、`AgentConfig`、`AgentConfigSnapshot`、端口方法和路由工厂签名在所有任务一致。
- 依赖边界：仅两个 `Protocol` 对应真实外部副作用；没有为单一场景增加 repository 实现、factory manager 或兼容层。
- 测试计数：领域基础 7 cases；服务新增 10 cases；API 4 cases；模块共 21 cases；加现有健康检查 4 cases 后端共 25 cases。
- 完整性扫描：每个代码步骤均给出具体内容和签名；动态 Commit SHA 和测试输出只允许在真实执行后写入证据台账。
- 完成边界：最终仅形成 `FCP-006-NDB`，TASK-006 数据库部分仍阻塞，TASK-007 保持未解锁。
