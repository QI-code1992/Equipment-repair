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

## TASK-002 开发交接（2026-07-15）

- 分支与恢复点：`codex/task-002-identity-equipment`，远端实现 Commit `0b0d9cf0dc066143c0a57d4683567fadb4714c12`，交接证据 Commit `9f162b421f4fefae4cdd69a001891c7e83d4bc13`，PR 目标为 `codex/stage-05-integration`。
- PR：[#15](https://github.com/QI-code1992/Equipment-repair/pull/15) 已 Ready for review，待 Review 与集成。
- 交付契约：会话认证、操作权限依赖、角色/权限查询、登录/登出/拒绝审计、全局请求指纹幂等、组织树、设备主数据和 Alembic `0001`。
- 验证：Python 3.13.14 下 38 tests passed；Compose 配置、API 镜像构建、PostgreSQL downgrade/upgrade/current、`/healthz` 200、真实并发幂等/唯一冲突/组织树竞争均通过。
- Review：最终独立复审 Critical 0、Important 0、Minor 0。
- DEV-002 消费边界：可基于冻结的认证上下文继续 TASK-006 非数据库实现；只有 TASK-002 合入集成分支后，才可开始 TASK-006 数据库迁移/集成以及其他依赖 TASK-002 的数据库工作。
- DEV-001 下一步：提交并完成 TASK-002 PR/集成；合入后按依赖矩阵启动 TASK-003，并通知 DEV-002 数据库边界已解锁。

## TASK-002 交接状态更正（2026-07-16）

- 原因：DEV-002 对 PR #15 候选 `cfb8ed9b99b5e440b3c0bf4a8652f4f7d233ee77` 提交 `Changes requested`；上节“Ready for review”不再代表当前有效交接状态。
- 当前状态：TASK-002 / CR-036 `In Development`；本地整改代码和契约草稿保持原状。任务书 v1.2 精确候选 `cd9c9b5d9d0f0a695c30881e2594e76a9f36c20b` 已获项目负责人批准并推送治理分支，治理 PR 合入 `codex/stage-05-integration` 前继续暂停后续 R6/R7。
- 旧证据边界：`0b0d9cf`、`9f162b4` 和 PR #15 历史继续保留，但不得作为 TASK-002 完成、FCP、正式 PR 或集成依据。
- 协作分工：DEV-001 为任务开发者和集成负责人；DEV-002 为指定审核者及后继正式 PR 创建者。DEV-001 只能推送任务分支并发送书面审核请求。
- PR #15：保留为被拒绝候选的审核历史和本轮 Review Request 载体；DEV-002 审核新候选通过后创建后继正式 PR。
- 依赖边界：TASK-003、TASK-004、TASK-005 及 DEV-002 的数据库集成继续按任务书阻塞；TASK-006 仅保留已允许的非数据库范围。
- 下一次有效交接条件：任务书 v1.2 与本审批记录已通过治理 PR 合入集成分支；CR-036 R6/R7 完成；PostgreSQL/Compose 和完整回归通过；正式证据提交并推送；DEV-002 复审通过。
