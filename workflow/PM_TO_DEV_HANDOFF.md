# 产品到开发交接

## 状态

既有 Stage 4 门禁与 `Hold-001` 已有历史批准，但代码库目录、开发任务书和准入缺陷发生后续变化。当前处于 Stage 4 补充整改，等待更新后的 Stage 4 → Stage 5 门禁；不得以旧 Gate-006 直接启动新的开发任务。

## 交接材料

- 已批准基线：Stage 1 需求、Stage 2 交互、Stage 3 原型、Stage 4 架构与实施计划。
- Stage 5 编码约束：[AGENTS.md](../04-architecture-plan/AGENTS.md)。
- 实施顺序：[IMPLEMENTATION_PLAN.md](../04-architecture-plan/IMPLEMENTATION_PLAN.md)。
- 已批准开发任务书：[DEVELOPMENT_TASK_BOOK.md](../04-architecture-plan/DEVELOPMENT_TASK_BOOK.md)，v1.0；该批准仅确认任务分配基线。
- 人员配置：`DEV-001` 负责最终集成和全部 Docker/Compose 验证；`DEV-002` 负责 AI、知识适配和正式前端，不具备 Docker 环境。
- 当前任务：关闭更新后的 Stage 5 准入阻塞；`DEV-001` 执行 TASK-001 仍需项目负责人明确授权，其他任务继续受阻。

所有开发只允许在新的 `codex/*` 隔离分支和独立工作区执行；不得直接向 `main` 推送，也不得在 TASK-001 通过前启动下游任务。
