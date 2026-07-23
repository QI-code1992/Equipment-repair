# TASK-006 数据库实施设计

## 状态与范围

- 状态：项目负责人已确认本设计方向；待审阅本文件后进入实施计划。
- 任务：TASK-006 四个 Agent 独立配置与模型能力校验。
- 分支与 PR：`codex/task-006-agent-config` / PR #14。
- 前置：TASK-002 已正式集成；本设计不解锁 TASK-007 或进入 Stage 6。

本切片补齐已验证的非数据库领域模型所需的 PostgreSQL 持久化、模型目录、权限、审计与正式路由挂载。真实模型调用、LangGraph、SSE、RAGFlow、Agent 运行和前端仍不在本范围。

## 数据模型

新增三类当前有效配置实体：

- `model_providers`：供应商公开元数据、启用状态与 `secret_ref`。`secret_ref` 仅是外部密钥管理系统的引用，不保存 API Key、Token 或请求头。
- `model_bindings`：供应商下可供 Agent 选择的模型绑定，包含稳定 ID、展示名称、模型名、`supports_reasoning` 与启用状态。
- `agent_configs`：每个 `agent_id` 一条当前有效配置。保存现有领域字段、知识库 ID JSON、更新时间和更新人；`agent_id` 唯一，`model_binding_id` 可空且引用启用模型绑定。

所有主键沿用现有 `String(36)` UUID 约定。`updated_by` 可为空以允许受控初始化；经 API 写入时必须记录当前已认证用户。删除供应商或绑定时使用 `RESTRICT`，避免配置静默指向失效对象。

迁移使用 DEV-001 分配的共享 Alembic revision（预期为 `0003`，实际 revision 以 DEV-001 分配为准），其 `down_revision` 必须为当前集成头 `0002`。降级删除三张本任务新增表，属于有损操作，只能在专用验证环境或已备份数据上执行。

## 服务与 API

持久化仓储实现既有 `AgentConfigRepository` 端口；模型目录实现既有 `ModelCatalog` 端口。服务层继续承担四 Agent 隔离、参数范围、模型存在性和推理能力校验，避免把业务规则放进路由或 ORM 模型。

新增或挂载的受保护 API：

- `GET /api/model-providers`、`POST /api/model-providers`、`PUT /api/model-providers/{id}`
- `GET /api/model-bindings`、`POST /api/model-bindings`、`PUT /api/model-bindings/{id}`
- 已定义的 `GET/PUT /api/agent-configs...` 路由正式挂载

模型供应商与绑定写入要求 `intelligence:model`；Agent 配置读取与写入分别要求 `intelligence:agent` 对应读写权限。所有写入经现有审计边界记录，但请求、响应、错误和审计元数据都不得含真实凭据；`secret_ref` 仅在具备模型管理权限的写入接口接受，永不在响应中返回。

## 初始化、事务与错误

首次初始化仅为请求的 `agent_id` 原子插入安全默认配置，不批量创建四个 Agent。并发首次初始化依赖唯一约束与冲突后读取，返回同一条配置。

模型绑定不存在、停用或不支持推理时，配置保存失败且不写入配置；错误继续使用稳定字段和错误码。更新配置、成功审计和请求幂等性遵循 TASK-002 已集成的事务规则。未预期失败必须回滚主事务并产生脱敏失败审计。

## TDD 与验证

每项生产行为按 RED → GREEN → REFACTOR 完成：

1. 迁移升级后表、唯一约束、外键和降级边界存在。
2. 供应商与模型绑定的安全响应不返回 `secret_ref` 或凭据。
3. 同一 `agent_id` 并发初始化只留下一个配置；初始化其他 Agent 不受影响。
4. 被禁用或不支持推理的模型绑定不能保存对应配置。
5. 权限不足、路径与配置身份不一致、异常回滚和审计脱敏均有 API/持久化断言。
6. Python 3.13 单元/API 回归由 DEV-002 执行；迁移升降级、PostgreSQL 并发、Compose 与正式路由冒烟由 DEV-001 在 Docker 环境执行。

不新增生产依赖、兼容层、全局内存仓储或范围外抽象。回退优先回退本任务应用提交；数据库降级仅按受控备份与验证流程执行。
