# TASK-006 非数据库实现设计

## 1. 状态与依据

- 状态：项目负责人已于 2026-07-15 批准，进入实施计划评审。
- 负责人：`DEV-002`
- 输入基线：TASK-001 正式交接提交 `42098613ffa20faed3bb0dcb842a0121722565bd`
- 需求映射：FR-012、NFR-006、AC-032、AC-034
- 架构依据：`API_SPEC.md`、`DATA_MODEL.md`、`AI_RAGFLOW_LANGGRAPH_SPEC.md`、`DEVELOPMENT_TASK_BOOK.md`
- 批准方案：存储无关的领域层与依赖注入 API；不使用进程内全局配置冒充生产持久化。

## 2. 本次范围

本次只实现 TASK-006 可在 TASK-002 前独立完成的部分：

- 四个稳定 `agent_id`：
  - `fault_reporting`
  - `metric_query`
  - `operation_guidance`
  - `fault_diagnosis`
- Agent 配置领域模型、模型能力模型和配置快照模型。
- 单个 Agent 的首次初始化、独立读取、独立保存和快照生成规则。
- 深度思考与模型推理能力校验。
- 不泄露密钥的配置响应映射。
- 存储无关的配置服务和可注入的 FastAPI 路由工厂。
- 纯领域测试、服务测试和使用测试 Fake 的 API 契约测试。

明确不包含：

- SQLAlchemy、Alembic、PostgreSQL 表、数据库迁移和事务集成。
- 将路由挂载到正式 `app.main`；没有持久化实现前不得对外形成易失配置 API。
- 进程内全局仓储、JSON 文件仓储或其他临时生产存储。
- 真实模型调用、测试运行执行、LangGraph、SSE 和运行恢复；这些属于 TASK-007 或后续集成。
- 正式前端工程及页面接入；正式前端仍按 TASK-010 建立，不复制 Stage 3 原型。
- Docker、Compose、RAGFlow 和基础设施修改。

## 3. 方案选择

### 采用方案：领域模型 + 外部副作用端口

配置领域逻辑不依赖数据库框架。数据库和模型目录属于外部副作用边界，因此只定义两个最小端口：

- `AgentConfigRepository`：按 `agent_id` 读取、列出、原子首次插入和保存配置。
- `ModelCatalog`：按 `model_binding_id` 返回公开模型能力，不返回密钥。

测试 Fake 只放在测试代码中。生产代码不提供内存仓储实现。

未采用方案：

- 临时内存 API：重启丢失配置，容易被误认为生产可用，且会造成后续替换工作。
- 完全等待 TASK-002：无法利用任务书已经批准的并行窗口。

## 4. 领域模型

### `AgentId`

使用字符串枚举限定四个值。未知值在 API 边界返回字段级错误，不回退到其他 Agent。

### `ModelCapability`

公开字段仅包含：

- `binding_id`
- `display_name`
- `supports_reasoning`

模型密钥、Token、请求头和供应商凭据不属于该对象，也不得进入响应、异常或日志。

### `AgentConfig`

使用不可变数据对象表示当前有效配置输入：

- `agent_id`
- `enabled`
- `model_binding_id`
- `knowledge_dataset_ids`
- `streaming_enabled`
- `suggestions_enabled`
- `sources_enabled`
- `context_turns`
- `retrieval_limit`
- `similarity_threshold`
- `deep_thinking_enabled`
- `deep_thinking_level`
- `max_reply_tokens`

首次初始化采用安全空配置：Agent 默认禁用、无模型绑定、无知识库绑定、深度思考关闭。其余参数使用领域内明确的保守默认值，但只有在配置完整并通过校验后才允许生成可运行快照。初始化某个 `agent_id` 时不得创建或更新其他三个 Agent。

### `AgentConfigSnapshot`

快照是不可变值对象，包含该轮实际使用的 Agent、模型和全部运行参数。快照不包含密钥，不承担版本、发布或回滚功能。后续 TASK-007 将它序列化到 `AgentRun.config_snapshot`。

## 5. 服务行为

`AgentConfigService` 提供：

- `initialize(agent_id)`：仅在目标 Agent 不存在时原子插入安全默认配置。
- `get(agent_id)`：读取目标 Agent；不存在时不读取或复制其他 Agent。
- `list_all()`：按固定四 Agent 顺序返回已有配置；不得隐式批量初始化。
- `save(agent_id, candidate)`：校验路径参数与配置身份一致，仅保存目标 Agent。
- `build_snapshot(agent_id)`：校验启用状态、模型绑定和能力后生成不可变快照。

保存与快照共同使用同一校验器：

- 未知 Agent：`UNKNOWN_AGENT_ID`
- 已启用但缺少模型：`AGENT_CONFIG_INVALID`
- 深度思考开启但模型不支持推理：`MODEL_REASONING_UNSUPPORTED`
- 参数越界：字段级 `AGENT_CONFIG_INVALID`

保存一个 Agent 不改变其他 Agent；配置更新只影响后续生成的新快照。

## 6. API 边界

实现可注入的路由工厂，但不在本任务挂载到正式应用：

- `GET /api/agent-configs`
- `GET /api/agent-configs/{agent_id}`
- `PUT /api/agent-configs/{agent_id}`

`POST /api/agent-configs/{agent_id}/test-runs` 本次只保留为已批准契约，不实现伪运行。真实模型测试必须复用 TASK-007 的模型网关和配置快照执行路径。

API 响应只返回配置和公开模型能力。错误使用稳定错误码和字段信息；不得回显密钥或原始异常中的敏感值。

## 7. 测试设计

严格按 RED → GREEN 执行：

1. 四个 `agent_id` 均可被识别，未知值失败。
2. 首次初始化一个 Agent 不创建或覆盖另外三个。
3. 更新一个 Agent 后，另外三个配置保持不变。
4. 同一 Agent 重复初始化保持已有配置。
5. 非推理模型开启深度思考返回 `MODEL_REASONING_UNSUPPORTED`。
6. 推理模型开启深度思考可保存并生成快照。
7. 缺少模型的已启用 Agent不能生成快照。
8. 快照与源配置隔离且不可变，不包含密钥。
9. API 不回退到其他 Agent 配置，响应不包含密钥字段。

测试 Fake 实现仓储和模型目录端口，仅用于测试。不得以 Fake 通过宣称数据库集成、模型调用或 Docker 验证完成。

## 8. 文件计划

预计新增：

- `codebase/backend/app/modules/agent_config/__init__.py`
- `codebase/backend/app/modules/agent_config/domain.py`
- `codebase/backend/app/modules/agent_config/service.py`
- `codebase/backend/app/modules/agent_config/api.py`
- `codebase/backend/tests/modules/test_agent_config.py`
- `codebase/backend/tests/modules/test_agent_config_api.py`

允许更新：

- `05-development/DEV_NOTES.md`
- `05-development/SELF_TEST.md`
- `05-development/CODE_REVIEW.md`
- `05-development/COMMIT_LOG.md`
- `05-development/CHECKPOINTS.md`
- `workflow/DEV_TO_PM_HANDOFF.md`

本任务不修改 `codebase/infra/`、数据库迁移、PRD、SPEC、原型、公开 API 规格或正式前端。

## 9. 完成边界

本次非数据库切片完成时只能声明：

- TASK-006 的领域逻辑和存储无关 API 契约已验证。
- 可以向 DEV-001 交付仓储端口、模型目录端口和快照输入契约。

不得声明：

- TASK-006 全部完成。
- 数据库保存、迁移或并发唯一性已验证。
- 正式配置 API 已上线。
- 真实模型测试、Docker、RAGFlow 或前端集成已通过。

数据库部分继续 `Blocked By TASK-002`；完成后创建的是“TASK-006 非数据库切片”检查点，不解锁 TASK-007。
