# 开发到产品交接

## TASK-001 正式交接（2026-07-15）

- 已批准输入基线：`25e15709a3f1d92f661d37acdb8aa3e1e0e41346`（`baseline/stage-04-development-v1.1`）。
- 修复范围：清除 `codebase/` 中后端应用工厂、配置字段、Compose 服务和网络的重复定义；不改变 PRD、SPEC、原型或公开业务 API。
- 远端提交：修复 `87538b04a168cb3c11c2e65dfb976d3a206d8218`，验证证据 `45725ac083c98ea999492b709e9792082c3db284`，分支 `codex/task-001-runtime-baseline`。
- 验证：Python 3.13.14 下健康检查测试 4 passed（仅一个第三方弃用警告）；Compose 配置通过；PostgreSQL、Redis healthy；API 容器内 `/healthz` 返回 `200` 与 `{'status': 'ok', 'service': 'equipment-operations-platform'}`。
- 缺陷：`DEF-003`、`DEF-004` 已解决并更新台账；独立 Review 通过，无阻断、重要或次要问题。

## DEV-002 启动边界

- 可启动：TASK-006 的四 Agent 独立配置领域测试与非数据库实现。
- 禁止提前：TASK-006 的数据库迁移、数据库集成和共享数据模型，直到 TASK-002 完成并合入。
- 仍阻塞：TASK-005 必须等待 TASK-002 与 TASK-004；其他任务继续严格遵循任务书依赖矩阵。
- 容器责任：DEV-002 不得自行宣称 Docker、Compose 或 RAGFlow 验证通过；相关真实环境验证仍由 DEV-001 提供。

## TASK-006 非数据库切片交接 DEV-001 审查（2026-07-15）

- 状态：TASK-006 非数据库切片已验证；TASK-006 总任务仍未完成。本次只交接 `FCP-006-NDB` 可恢复检查点，不请求将其认定为 TASK-006 完成门禁。
- 精确实现：`33d7712334044437eba0d3fc884859d48a3c71ed`、`7cbf76bb9ae627e023cbeaa86fd883b18a916373`、`f7da3393f8861e3f7b8a453629fce7079915e58e`（实现 HEAD），分支 `codex/task-006-agent-config`；Tasks 1–3 已逐任务审查。
- 远端证据与恢复提交：`56a3c1028ee0731d6b6ec4bc51e7dd6d73679608`；它记录六份 Stage 5 台账并形成远端恢复点，不替代实现 HEAD `f7da3393f8861e3f7b8a453629fce7079915e58e`。
- 已完成：领域模型、两个外部端口、独立初始化/读取/保存、模型推理能力校验、不可变配置快照、未挂载 API 契约。
- 验证：Python 3.13.14 模块 `21 passed, 1 warning`，后端全量 `25 passed, 1 warning`；warning 为现有第三方 `StarletteDeprecationWarning`。编译、空白与范围检查通过。
- 非阻塞关注：Task 2 后续可增强空列表/未初始化、身份不匹配隔离、完整快照 sentinel、精确范围边界四类测试；不影响当前非数据库切片检查点。
- 请求 DEV-001 仅审查：`AgentConfigRepository` 与 `ModelCatalog` 两个端口边界、认证/权限/审计接入点，以及 TASK-002 完成后的数据库适配方案；本次不请求合并或认可数据库实现。
- 未完成与依赖：数据库仓储、迁移、事务/并发唯一性、认证/权限/审计接入、正式路由挂载、真实模型测试、前端集成均未完成；数据库继续 Blocked By TASK-002，TASK-007 不解锁。
- 环境与工程声明：DEV-002 未执行或宣称 Docker、Compose、RAGFlow 通过；未新增生产依赖、兼容代码、范围外抽象或无关修改。
- 最终审查安全修复：`04e651c1453fbd0551303aff9f4d6236ea2e59d4` 已关闭 RequestValidationError 回显原始输入的 Important；新增三个场景逐项 RED/GREEN，补充结果为 API `7 passed`、模块 `24 passed`、后端全量 `28 passed`，原 `21/25` 证据保留。
- 风险与回退方式：Agent 配置路由仍未挂载到正式应用，因此本修复尚无线上流量风险；如需回退，回退本次 Agent 配置安全实现提交 `04e651c1453fbd0551303aff9f4d6236ea2e59d4` 及其对应证据提交即可。没有数据库状态需要回滚；数据库部分仍由 TASK-002 后续处理。
- 仍未完成边界：数据库仓储、迁移、事务/并发唯一性、认证/权限/审计接入、正式路由挂载、真实模型测试与前端集成未完成，TASK-007 仍不解锁。既有四项 Minor 测试增强与 `_validate` 约 50 行长度关注继续作为非阻塞项。
