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

## CR-038 治理补救交接（2026-07-16）

- 事件：PR #15 在审核结论仍为 `Changes requested` 时被合入 `codex/stage-05-integration`，合并提交为 `e328cec64f1aa9c7cdc383579af042692dce5679`。
- 批准：项目负责人批准保留开发成果并通过独立 PR 非破坏性回滚该集成结果。
- 补救分支：`codex/cr-038-revert-pr-15-gate-violation`。
- 授权记录：`6650f615e48d88b9a54179c27a7f03d1bf48f391`。
- 回滚候选：`5d91e83679acefa5486a25bf5b921e9c12fd52d6`。
- 验证：Python 3.13.14 `4 passed, 1 warning`；`compileall`、Compose 配置和差异检查通过。
- 当前边界：补救 PR 未合入；TASK-002 仍为 `Changes requested`；CR-037、TASK-002 R6/R7、TASK-003、TASK-004 和依赖 TASK-002 的数据库集成继续暂停。
- 下一步：创建 CR-038 补救 PR；合入后同步 CR-037 治理分支，再恢复 TASK-002 整改与 DEV-002 复审。
