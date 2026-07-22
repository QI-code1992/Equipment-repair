# 产品到开发交接

## 状态

更新后的 Stage 4 → Stage 5 门禁 `Gate-007` 已针对精确 Commit `25e15709a3f1d92f661d37acdb8aa3e1e0e41346` 获项目负责人批准。项目当前处于 Stage 5：TASK-002 代码、技术验证和合并后治理收尾均已完成；不进入 Stage 6。

## 交接材料

- 已批准基线：Stage 1 需求、Stage 2 交互、Stage 3 原型、Stage 4 架构与实施计划。
- Stage 5 编码约束：[AGENTS.md](../04-architecture-plan/AGENTS.md)。
- 实施顺序：[IMPLEMENTATION_PLAN.md](../04-architecture-plan/IMPLEMENTATION_PLAN.md)。
- 已批准开发任务书：[DEVELOPMENT_TASK_BOOK.md](../04-architecture-plan/DEVELOPMENT_TASK_BOOK.md)，v1.3（CR-040 已随 PR #23 Merge Commit `d633308de8277c343faf3e266476b64baffcb565` 生效）；v1.4 候选通过 CR-041 新增正式前端工程初始化前置任务，合入前不改变当前有效门禁。
- 人员配置：`DEV-001` 负责最终集成和全部 Docker/Compose 验证；`DEV-002` 负责 AI、知识适配和正式前端，不具备 Docker 环境。
- 当前任务：`DEV-001` 可按任务书启动 TASK-003、TASK-004；`DEV-002` 可继续 TASK-006 后端/迁移范围。CR-041 治理候选合入后，DEV-002 可先执行 TASK-006-FE，再完成 TASK-006 的智能配置前端子范围和 TASK-007 的共享前端对话子范围。TASK-005 仍等待 TASK-004 的环境与契约交付。

TASK-001、TASK-002 均已完成并保留历史交接。所有开发只允许在新的 `codex/*` 隔离分支和独立工作区执行；不得直接向 `main` 推送，也不得绕过各任务自身的 PR、审核和授权门禁。

## CR-040 Stage 5 协作规则交接（2026-07-17）

- Stage 5 只有 `DEV-001`、`DEV-002` 两名开发者和项目负责人；不另设“DEV-001 Agent”或“DEV-002 Agent”角色。
- 任务开发者从集成分支创建任务分支，并为自己的开发任务创建一个 Draft PR；后续修改、Ready 和复审都在同一 PR 完成。
- 另一名开发者是开发任务审核者，必须对精确 HEAD 给出 Approve 或 Changes requested；任务开发者不得批准或合并自己的开发任务 PR。
- 纯治理文档 PR 不要求两名开发者交叉代码审核；项目负责人确认治理内容和精确 HEAD，DEV-001 执行集成核查和请求授权，非 PR 作者的开发者获批后合并。
- `DEV-001` 是最终集成负责人：核查目标、HEAD、适用的 Review 或治理确认、checks、依赖、冲突、共享契约、风险和回滚，然后逐 PR 向项目负责人请求 Merge 授权；最终集成责任不等于可以合并自己的 PR。
- 项目负责人对开发任务 PR 负责 Merge 授权而不代替代码审核；对纯治理文档 PR 同时负责治理内容确认。只有明确批准 PR 编号和精确 HEAD 后，非任务开发者/非治理 PR 作者才可执行 Merge Commit。
- HEAD、目标分支、依赖或检查结论变化后原授权失效；必须重新核查并询问。开发任务 PR 还须重新审核，纯治理文档 PR 还须由项目负责人重新确认治理内容和精确 HEAD。
- 禁止 auto-merge、merge queue、直接 push `codex/stage-05-integration` 和任何 Stage 5 普通开发 PR 指向 `main`。
- 本规则已随 CR-040 PR #23 Merge Commit `d633308de8277c343faf3e266476b64baffcb565` 合入 `codex/stage-05-integration` 并生效；不追溯改写既有历史。

## TASK-002 合并后治理收尾边界（2026-07-17）

- 代码事实：DEV-002 已批准精确任务 HEAD `2e89dcd8d8dff6af5b841f32ac0a7d5feb794e15`；PR #20 已由 DEV-001（`ll979053897-arch`）手动合入，Merge Commit `904886f48061e27c775f6ee2f8ddae99f5571ead`；Python 3.13、PostgreSQL 17、Compose 健康和 `/healthz` 证据均已归档。
- PR #25 治理合并：获批 HEAD `92ec18ec17f08d1d2226b0d98f59eeb2eba78d2f` 已由 DEV-002（`QI-code1992`）以 Merge Commit `028da42eb9ab4b55ef981ac462e09993a31e8813` 合入。
- 有效状态：TASK-002 治理收尾关闭；TASK-003/004 可按任务书启动；TASK-005 仍等待 TASK-004；TASK-006 已解除 TASK-002 的数据库前置，但仍按自身任务范围和 PR 门禁执行；不进入 Stage 6。
