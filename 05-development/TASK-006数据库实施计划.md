# TASK-006 数据库实施 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `subagent-driven-development` (recommended) or `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为四个 Agent 提供安全、可审计、可持久化的模型目录和当前配置，并把已验证的配置 API 挂载到正式 FastAPI 应用。

**Architecture:** 继续以 `domain.py` 和 `service.py` 作为业务规则中心；新增 SQLAlchemy ORM 与 SQL 仓储实现既有 `AgentConfigRepository` / `ModelCatalog` 端口。模型供应商密钥仅以不可回显 `secret_ref` 表示，模型绑定能力由数据库目录提供；路由复用 TASK-002 的认证、权限、审计与幂等事务模式。

**Tech Stack:** Python 3.13、FastAPI、SQLAlchemy 2、Alembic、PostgreSQL、pytest、现有 TASK-002 审计/认证/幂等模块。

## Global Constraints

- 共享迁移 revision 固定命名为 `0003_task006_agent_config`，`down_revision="0002"`；DEV-001 必须先确认该 revision 未被占用并负责 PostgreSQL/Compose 验证。
- 不新增生产依赖、不保存或返回 API Key、Token、Cookie、请求头或真实供应商凭据。
- `secret_ref` 只允许 `intelligence:model` 写接口接收，任何读响应与审计元数据均不得包含它。
- 四个合法 `agent_id` 仍仅为 `fault_reporting`、`metric_query`、`operation_guidance`、`fault_diagnosis`；首次初始化只影响请求目标。
- 写 API 使用现有 `Idempotency-Key`、审计与权限机制；模型/Agent 写权限分别为 `intelligence:model`、`intelligence:agent`。
- DEV-002 运行 Python 3.13 单元/API/SQLite 迁移回归；DEV-001 运行 PostgreSQL 升降级、并发和 Docker/Compose 验证。
- 任何生产代码先写失败测试并观察预期 RED，再写最小 GREEN 实现。

---

## 文件结构

| 文件 | 责任 |
|---|---|
| `codebase/backend/alembic/versions/0003_task006_agent_config.py` | 创建/降级模型目录和 Agent 配置表。 |
| `codebase/backend/app/modules/agent_config/models.py` | 三个 ORM 模型与 JSON 序列化边界。 |
| `codebase/backend/app/modules/agent_config/repository.py` | SQL 仓储与模型目录端口实现。 |
| `codebase/backend/app/modules/agent_config/schemas.py` | 不泄露凭据的请求与响应模型。 |
| `codebase/backend/app/modules/agent_config/router.py` | 受保护、幂等、审计的模型与 Agent 配置 API。 |
| `codebase/backend/app/main.py` | 挂载 TASK-006 路由。 |
| `codebase/backend/tests/modules/test_task006_migration.py` | `0002 -> 0003 -> 0002` 迁移断言。 |
| `codebase/backend/tests/modules/test_agent_config_persistence.py` | SQL 仓储、隔离和能力校验。 |
| `codebase/backend/tests/modules/test_agent_config_routes.py` | 权限、脱敏响应、审计和幂等 API 契约。 |

## Task 1: 迁移分配与迁移 RED

**Files:**

- Create: `codebase/backend/tests/modules/test_task006_migration.py`
- Create: `codebase/backend/alembic/versions/0003_task006_agent_config.py`

**Interfaces:**

- Consumes: `0002_task002_contract_completion`、现有 Alembic 配置。
- Produces: `0003_task006_agent_config`，包含 `model_providers`、`model_bindings`、`agent_configs`。

- [ ] **Step 1: 由 DEV-001 分配 revision**

记录 DEV-001 对 `0003_task006_agent_config` 的确认，并执行：

```bash
cd codebase/backend
alembic heads
```

Expected: 当前唯一 head 为 `0002`，且没有其他开发任务占用 `0003`。

- [ ] **Step 2: 写迁移失败测试**

```python
def test_task006_upgrade_creates_catalog_and_config_constraints(migration_database):
    config, engine = migration_database
    command.upgrade(config, "0002")
    command.upgrade(config, "0003")

    inspector = inspect(engine)
    assert {"model_providers", "model_bindings", "agent_configs"} <= set(
        inspector.get_table_names()
    )
    assert {column["name"] for column in inspector.get_columns("agent_configs")} >= {
        "agent_id", "model_binding_id", "knowledge_dataset_ids", "updated_by"
    }
```

- [ ] **Step 3: 验证 RED**

Run: `cd codebase/backend && .venv/bin/python -m pytest tests/modules/test_task006_migration.py -q`

Expected: FAIL because revision `0003` does not exist.

- [ ] **Step 4: 写最小迁移**

迁移创建以下约束：

```python
op.create_table(
    "model_providers",
    sa.Column("id", sa.String(36), primary_key=True),
    sa.Column("name", sa.String(100), unique=True, nullable=False),
    sa.Column("secret_ref", sa.String(500), nullable=False),
    sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
)
op.create_table(
    "model_bindings",
    sa.Column("id", sa.String(36), primary_key=True),
    sa.Column("provider_id", sa.String(36), sa.ForeignKey("model_providers.id", ondelete="RESTRICT"), nullable=False),
    sa.Column("name", sa.String(100), nullable=False),
    sa.Column("model_name", sa.String(200), nullable=False),
    sa.Column("supports_reasoning", sa.Boolean(), nullable=False, server_default=sa.false()),
    sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
    sa.UniqueConstraint("provider_id", "name", name="uq_model_bindings_provider_name"),
)
```

`agent_configs.agent_id` 使用唯一约束；`model_binding_id` 用 `RESTRICT` 外键；`knowledge_dataset_ids` 使用 JSON；`updated_by` 外键引用 `users.id`，可空。

- [ ] **Step 5: 验证 GREEN 并提交**

Run: `cd codebase/backend && .venv/bin/python -m pytest tests/modules/test_task006_migration.py -q`

Expected: PASS。

```bash
git add codebase/backend/alembic/versions/0003_task006_agent_config.py codebase/backend/tests/modules/test_task006_migration.py
git commit -m "feat(task-006): add agent configuration schema"
```

## Task 2: ORM、SQL 端口与隔离 RED/GREEN

**Files:**

- Create: `codebase/backend/app/modules/agent_config/models.py`
- Create: `codebase/backend/app/modules/agent_config/repository.py`
- Create: `codebase/backend/tests/modules/test_agent_config_persistence.py`

**Interfaces:**

- Consumes: `AgentConfigRepository`、`ModelCatalog`、`AgentConfigService`。
- Produces: `SqlAgentConfigRepository(Session)` 与 `SqlModelCatalog(Session)`。

- [ ] **Step 1: 写隔离与能力失败测试**

```python
def test_sql_repository_initializes_only_one_agent(db_session, model_binding):
    repository = SqlAgentConfigRepository(db_session)
    service = AgentConfigService(repository, SqlModelCatalog(db_session))

    created = service.initialize("fault_reporting")

    assert created.agent_id is AgentId.FAULT_REPORTING
    assert repository.list_all() == [created]


def test_disabled_binding_is_not_accepted_for_enabled_agent(db_session, disabled_binding):
    service = AgentConfigService(SqlAgentConfigRepository(db_session), SqlModelCatalog(db_session))
    candidate = replace(AgentConfig.default_for(AgentId.METRIC_QUERY), enabled=True, model_binding_id=disabled_binding.id)

    with pytest.raises(AgentConfigError, match="模型绑定不存在"):
        service.save("metric_query", candidate)
```

- [ ] **Step 2: 验证 RED**

Run: `cd codebase/backend && .venv/bin/python -m pytest tests/modules/test_agent_config_persistence.py -q`

Expected: FAIL because SQL adapter classes do not exist.

- [ ] **Step 3: 实现最小 ORM 与适配器**

`AgentConfigModel` 显式逐字段映射领域对象；转换函数只在 `repository.py` 内存在：

```python
def to_domain(row: AgentConfigModel) -> AgentConfig:
    return AgentConfig(
        agent_id=AgentId(row.agent_id),
        enabled=row.enabled,
        model_binding_id=row.model_binding_id,
        knowledge_dataset_ids=tuple(row.knowledge_dataset_ids),
        streaming_enabled=row.streaming_enabled,
        suggestions_enabled=row.suggestions_enabled,
        sources_enabled=row.sources_enabled,
        context_turns=row.context_turns,
        retrieval_limit=row.retrieval_limit,
        similarity_threshold=row.similarity_threshold,
        deep_thinking_enabled=row.deep_thinking_enabled,
        deep_thinking_level=DeepThinkingLevel(row.deep_thinking_level),
        max_reply_tokens=row.max_reply_tokens,
    )
```

`SqlModelCatalog.get()` 仅返回启用绑定和启用供应商的 `ModelCapability`；不得读取或返回 `secret_ref`。

- [ ] **Step 4: 验证 GREEN 并提交**

Run: `cd codebase/backend && .venv/bin/python -m pytest tests/modules/test_agent_config.py tests/modules/test_agent_config_persistence.py -q`

Expected: PASS。

```bash
git add codebase/backend/app/modules/agent_config/models.py codebase/backend/app/modules/agent_config/repository.py codebase/backend/tests/modules/test_agent_config_persistence.py
git commit -m "feat(task-006): persist independent agent configurations"
```

## Task 3: 安全 Schema、受保护路由与审计 RED/GREEN

**Files:**

- Create: `codebase/backend/app/modules/agent_config/schemas.py`
- Create: `codebase/backend/app/modules/agent_config/router.py`
- Modify: `codebase/backend/app/main.py`
- Create: `codebase/backend/tests/modules/test_agent_config_routes.py`

**Interfaces:**

- Consumes: `require_permission`、`get_db`、`write_audit_event`、现有幂等帮助函数。
- Produces: 模型目录 CRUD、Agent 配置 GET/PUT 及 FastAPI 正式路由。

- [ ] **Step 1: 写权限、脱敏和审计失败测试**

```python
def test_model_provider_response_never_returns_secret_ref(client, model_admin_headers):
    response = client.post(
        "/api/model-providers",
        headers={**model_admin_headers, "Idempotency-Key": "provider-1"},
        json={"name": "OpenAI compatible", "secret_ref": "vault://models/prod", "enabled": True},
    )

    assert response.status_code == 201
    assert "secret_ref" not in response.json()
    assert "vault://models/prod" not in str(response.json())


def test_agent_config_write_requires_intelligence_agent(client, model_admin_headers):
    response = client.put(
        "/api/agent-configs/fault_reporting",
        headers={**model_admin_headers, "Idempotency-Key": "agent-1"},
        json=valid_agent_config_body(),
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "PERMISSION_DENIED"
```

- [ ] **Step 2: 验证 RED**

Run: `cd codebase/backend && .venv/bin/python -m pytest tests/modules/test_agent_config_routes.py -q`

Expected: FAIL because the formal routes are not mounted.

- [ ] **Step 3: 实现最小安全路由**

`ProviderWrite` 仅作为写模型含 `secret_ref`；`ProviderRead` 不定义该字段。所有成功写入执行：

```python
event = write_audit_event(
    db,
    actor_user_id=actor.id,
    action="model_provider.create",
    resource_type="model_provider",
    resource_id=provider.id,
    result="success",
    metadata={"name": provider.name},
)
db.commit()
return {**provider_read(provider), "audit_event_id": event.id}
```

将 `agent_config_router` 挂载到 `create_app()`；路由内部从 `Session` 构造 SQL 适配器，禁止全局缓存仓储。

- [ ] **Step 4: 验证 GREEN 并提交**

Run: `cd codebase/backend && .venv/bin/python -m pytest tests/modules/test_agent_config_routes.py tests/modules/test_agent_config_api.py -q`

Expected: PASS。

```bash
git add codebase/backend/app/modules/agent_config/schemas.py codebase/backend/app/modules/agent_config/router.py codebase/backend/app/main.py codebase/backend/tests/modules/test_agent_config_routes.py
git commit -m "feat(task-006): secure agent configuration APIs"
```

## Task 4: 回归、DEV-001 数据库交接与 PR 更新

**Files:**

- Modify: `05-development/SELF_TEST.md`
- Modify: `05-development/CHECKPOINTS.md`
- Modify: `workflow/DEV_TO_PM_HANDOFF.md`

- [ ] **Step 1: 运行 DEV-002 可执行验证**

```bash
cd codebase/backend
.venv/bin/python -m pytest tests/modules/test_agent_config.py tests/modules/test_agent_config_api.py tests/modules/test_agent_config_persistence.py tests/modules/test_agent_config_routes.py tests/modules/test_task006_migration.py -q
.venv/bin/python -m pytest tests -q
.venv/bin/python -m compileall -q app tests alembic
```

Expected: 所有非 PostgreSQL 测试通过；任何已知第三方 warning 逐条记录，不描述为无 warning。

- [ ] **Step 2: DEV-001 执行真实环境验证**

```bash
docker compose --env-file codebase/infra/.env.example -f codebase/infra/docker-compose.yml config --quiet
cd codebase/backend
python3.13 -m pytest tests/integration/test_task006_postgres.py -q
alembic upgrade 0003
alembic downgrade 0002
alembic upgrade 0003
```

Expected: PostgreSQL 中唯一配置、并发首次初始化、外键/权限/审计、升降级与正式路由冒烟均通过。

- [ ] **Step 3: 更新证据并请求审核**

记录精确 HEAD、DEV-002 测试、DEV-001 Docker/PostgreSQL 证据、风险与回退方式；保持 PR #14 为同一 PR，转 Ready 后请求 DEV-001 对精确 HEAD 审核。

- [ ] **Step 4: 提交证据**

```bash
git add 05-development/SELF_TEST.md 05-development/CHECKPOINTS.md workflow/DEV_TO_PM_HANDOFF.md
git commit -m "docs(task-006): record database integration evidence"
```

## 自检

- 设计中的三表、凭据不回显、权限、审计、唯一初始化、推理能力校验、迁移和 DEV-001 真实环境验证均至少有一个对应任务。
- 路由、模型、仓储、迁移与测试路径在后续任务间名称一致。
- 无占位标记、未命名文件、无来源的依赖或范围外 Agent 运行能力。
