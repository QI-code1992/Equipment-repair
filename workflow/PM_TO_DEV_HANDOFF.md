# 产品到开发交接

## 状态

更新后的 Stage 4 → Stage 5 门禁 `Gate-007` 已针对精确 Commit `25e15709a3f1d92f661d37acdb8aa3e1e0e41346` 获项目负责人批准。项目状态为 Stage 5 可开始，首个任务为 DEV-001 的 TASK-001。

## 交接材料

- 已批准基线：Stage 1 需求、Stage 2 交互、Stage 3 原型、Stage 4 架构与实施计划。
- Stage 5 编码约束：[AGENTS.md](../04-architecture-plan/AGENTS.md)。
- 实施顺序：[IMPLEMENTATION_PLAN.md](../04-architecture-plan/IMPLEMENTATION_PLAN.md)。
- 已批准开发任务书：[DEVELOPMENT_TASK_BOOK.md](../04-architecture-plan/DEVELOPMENT_TASK_BOOK.md)，v1.1。
- 人员配置：`DEV-001` 负责最终集成和全部 Docker/Compose 验证；`DEV-002` 负责 AI、知识适配和正式前端，不具备 Docker 环境。
- 当前任务：`DEV-001` 按任务书启动 TASK-001，修复并验证平台运行基线；`DEV-002` 和所有下游任务继续等待 TASK-001 检查点。

`DEV-001` 无需额外任务级授权即可开始 TASK-001。所有开发只允许在新的 `codex/*` 隔离分支和独立工作区执行；不得直接向 `main` 推送，也不得在 TASK-001 通过前启动下游任务。

## CR-040 Stage 5 协作规则交接（2026-07-17）

- 参与角色仅为 `DEV-001 Agent`、`DEV-002 Agent` 和项目负责人；不设置 DEV-001 人工同事角色。
- 任务开发 Agent 从集成分支创建任务分支，并为自己的任务创建一个 Draft PR；后续修改、Ready 和复审都在同一 PR 完成。
- 另一 Agent 是指定审核者，必须对精确 HEAD 给出 Approve 或 Changes requested；任务开发 Agent 不得批准或合并自己的 PR。
- `DEV-001 Agent` 是唯一 Stage 5 集成执行者：自动核查目标、HEAD、Review、checks、依赖、冲突、共享契约、风险和回滚，然后逐 PR 向项目负责人请求 Merge 授权。
- 项目负责人负责授权，不承担代码检查。只有明确批准 PR 编号和精确 HEAD 后，DEV-001 Agent 才可执行 Merge Commit。
- HEAD、目标分支、依赖或检查结论变化后原授权失效；必须重新审核、检查并询问。
- 禁止 auto-merge、merge queue、直接 push `codex/stage-05-integration` 和任何 Stage 5 普通开发 PR 指向 `main`。
- 本规则在 CR-040 治理 PR 合入 `codex/stage-05-integration` 后生效；不追溯改写既有历史。
