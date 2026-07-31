# 产品到开发交接

## Stage 7 P0 正式前端偏离回流 Stage 5（2026-07-30）

- 决定：项目负责人已确认 `DEF-STAGE7-001` 的书面设计和实施计划，要求修复页面功能矩阵中的全部 P0 页面；Data import 继续排除。
- 当前治理状态：PR #71 已将 `TASK-012-API-001` 合入 `codex/stage-05-integration`，并关闭 `API-GAP-001`。TASK-012 仍被 `TASK-012-API-002`—`007` 阻断，禁止创建 TASK-012 前端代码 PR。
- 实施边界：正式 React 前端以批准 Stage 3 原型的结构、布局、导航与交互状态为基线，但只能消费正式 API、真实权限与运行状态；严禁复制/运行原型源码、伪造业务数据或未经确认新增 API、迁移、依赖、权限和部署配置。
- API 阻断：工作台待办/告警/快捷事项读取已由 API-001 正式集成；BI 聚合、设备历史、维修/工单读取、审计读取和智能调用记录等 `API-GAP-002`—`007` 仍须逐项完成项目负责人确认的公开 API、审核与集成，不能以前端 mock 替代。
- 当前门禁：Stage 7 受影响 UI 验收暂停；本回流不改写 Stage 1—4 基线、不构成 Stage 6 重测通过、Stage 7 验收通过或 Stage 8 发布授权。

## Stage 7 独立产品验收授权（2026-07-29）

- 项目负责人已批准集成 HEAD `89fbd2129169fb6ece42094b17907885637f3c48` 通过 Stage 6 → Stage 7 Gate。
- 授权范围：以 Stage 1—4 已批准基线、Stage 6 测试材料及该精确候选执行独立产品验收；逐项记录 AC 结论、证据、残余风险和缺陷回流决定。
- 边界：本授权不代表验收通过、Stage 8 发布、生产操作或直接合入 `main`。实施缺陷须回流 Stage 5；测试证据须在修复后针对新精确候选重新验证。

## Stage 6 独立测试授权（2026-07-27）

- 项目负责人已批准候选集成 HEAD `8a5e6ced473ea6219666d858ce5b751e61362871` 通过 Stage 5 → Stage 6 Gate。
- 授权范围：按 `06-testing/TEST_PLAN.md` 和 `06-testing/TEST_CASES.md` 对该批准基线执行独立测试与质量验证；每项证据须记录精确 SHA、环境、夹具、命令、结果、缺陷和残余风险。
- 已知风险：RAGFlow 外部依赖曾间歇性不可用；前端依赖审计有 2 项既有 high-severity 发现。不得将其静默忽略，须在 Stage 6 报告中复核和处置。
- 禁止事项：本授权不等于 Stage 7 产品验收、Stage 8 发布、生产操作或直接合入 `main`；任何测试中发现的基线/实现问题按适用流程回退到受影响阶段。

## 状态

更新后的 Stage 4 → Stage 5 门禁 `Gate-007` 已针对精确 Commit `25e15709a3f1d92f661d37acdb8aa3e1e0e41346` 获项目负责人批准。项目当前处于 Stage 5：TASK-002 代码、技术验证和合并后治理收尾均已完成；不进入 Stage 6。

## 交接材料

- 已批准基线：Stage 1 需求、Stage 2 交互、Stage 3 原型、Stage 4 架构与实施计划。
- Stage 5 编码约束：[AGENTS.md](../04-architecture-plan/AGENTS.md)。
- 实施顺序：[IMPLEMENTATION_PLAN.md](../04-architecture-plan/IMPLEMENTATION_PLAN.md)。
- 已批准开发任务书：[DEVELOPMENT_TASK_BOOK.md](../04-architecture-plan/DEVELOPMENT_TASK_BOOK.md)，v1.4（CR-041 已随 PR #28 Merge Commit `7a44401bacbdc48d58f697a6b252449ecf44bb29` 生效）；新增正式前端工程初始化前置任务。
- 人员配置：`DEV-001` 负责最终集成和全部 Docker/Compose 验证；`DEV-002` 负责 AI、知识适配和正式前端，不具备 Docker 环境。
- 当前任务：`DEV-001` 可按任务书启动 TASK-003、TASK-004；`DEV-002` 可继续 TASK-006 后端/迁移范围。PR #33 已集成，但在其治理收尾 PR 合入前，TASK-006 智能配置前端子范围和 TASK-007 共享前端对话子范围继续锁定；收尾合入后可按各自任务书、PR、审核和授权门禁继续。TASK-005 仍等待 TASK-004 的环境与契约交付。

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
## CR-048 治理候选已集成，等待开发启动确认（2026-07-31）

- PR #73 的获批 HEAD `b4e28368c1294f30b80f4dd72187660eba06fc10` 已由 DEV-001 合入，Merge Commit 为 `8d9beaefe01baef38e54baecbe3426d9ab816623`。
- 本合入只生效 TASK-012 的统一开发边界，不代表 API-002—007 或前端已完成，也不解锁 Stage 6/7/8。
- DEV-002（项目负责人兼 TASK-012 开发者）需明确确认开发启动；确认后在唯一 Draft PR `codex/task-012-p0-frontend-remediation` 中先更新 API 规格和失败契约测试，再开始实现。
