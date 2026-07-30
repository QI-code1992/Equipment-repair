# Stage 7 P0 正式前端偏离修复实施计划

- 状态：设计已获项目负责人确认；本计划待项目负责人授权后执行。
- 关联缺陷：`DEF-STAGE7-001`。
- 关联变更：`CR-047`。
- 当前修复基线：`a334afd1b8cb4eeb139d78b7f5f1b5617bb2cd32`。
- 受影响的验收候选：`89fbd2129169fb6ece42094b17907885637f3c48`。
- 设计依据：`05-development/STAGE7_P0_FRONTEND_REMEDIATION_DESIGN.md`、`02-product-interaction-design/PAGE_FUNCTION_MATRIX.md`、`03-ui-prototype/`。

## 1. 目标与完成判定

本计划修复“正式 React 前端没有落实已批准原型的全部 P0 页面”的实现偏离。正式页面必须以批准原型的信息架构、版式层次、导航、关键交互状态为视觉基线；业务内容只读取正式 API 和登录态，不能运行、复制或导入原型源码，不能保留演示业务数据。

完成的最低判定为：

1. 页面矩阵中的除“数据导入”外全部 P0 页面可从正式路由到达；未认证访问被导向登录，权限不足显示明确的无权限状态。
2. 每个页面都有真实 API 的加载、空、错误和禁用/权限状态；写入操作携带 Bearer Token 与 `Idempotency-Key`。
3. 每项原型可见功能都有“已用正式契约实现 / 明确不在 P0 / 后端契约待批准”的记录；不得用静态数值、假数据或永远成功的占位 UI 填充空缺。
4. 自动化前端交互测试、生产构建、原型差异检查和浏览器逐页对照均通过，并由新的精确候选重新执行受影响的 Stage 6、Stage 7 验证。

## 2. 约束与实施顺序

- 这是 Stage 7 发现并回流的 Stage 5 代码修复。实施期间适用 `04-architecture-plan/AGENTS.md` 和任务书的 Draft PR、交叉审核、非作者 Merge、精确 HEAD 授权规则。
- 先建立并获确认的任务书修订，再创建任何业务代码 PR。每个开发任务由 DEV-002 创建和维护一个指向 `codex/stage-05-integration` 的 Draft PR，DEV-001 审核与集成；每次 Merge 均须项目负责人对 PR 编号和精确 HEAD 单独授权。
- 不新增生产依赖；沿用 React、React Router、现有测试栈和现有图标/样式能力。任何例外另行走变更确认。
- 公开 API、数据模型、权限或部署配置缺口，不得由前端自行猜测或 mock；先登记为 P1 契约缺口，更新 API 规格、任务书和 CR，并取得项目负责人对精确范围的确认后，才可由相应所有者实现。
- 后端、迁移或基础设施缺口由 DEV-001 负责；前端功能由 DEV-002 负责。Docker/live-stack 验证只由具备环境的 DEV-001 执行。

## 3. 执行任务

### 任务 0：治理准入与契约可用性盘点

1. 在一个含 Stage 5 设计、计划和缺陷记录的治理/实施规划 Draft PR 中更新 `04-architecture-plan/DEVELOPMENT_TASK_BOOK.md`：新增本修复工作包、开发者/审核者/合并矩阵、依赖、回滚边界和 `DEF-STAGE7-001` 引用；同步 `workflow/state.json`、`workflow/PM_TO_DEV_HANDOFF.md`、`workflow/DEV_TO_PM_HANDOFF.md` 的“Stage 7 被阻断、回流 Stage 5”状态。该 PR 不符合纯治理 PR 的窄定义，必须由 DEV-001 对精确 HEAD 正式审核。
2. 创建 `05-development/P0_FRONTEND_API_AVAILABILITY_MATRIX.md`。逐行对应 `PAGE_FUNCTION_MATRIX.md` 的 P0 页面，并记录：正式路由、现有 API 路由和权限、字段/状态、前端测试文件、原型参考页，以及缺失契约。
3. 用 `codebase/backend/app/main.py` 中注册的 Router 和 `04-architecture-plan/API_SPEC.md` 交叉验证矩阵；特别检查工作台待办/告警、BI 汇总/趋势/排行、维修工单列表与详情、设备历史、审计列表等未在当前路由中直接提供的内容。
4. 对每个缺口输出最小 API 提案（资源、权限、查询参数、成功/空/错误响应、是否需迁移）。在项目负责人对该公开 API 范围确认前，该行保持 `BLOCKED_API_GAP`，不进入页面实现，也不填充演示数据。
5. 验证：`python3 -m json.tool workflow/state.json`、`git diff --check`、矩阵中的路由/权限链接人工复核。

### 任务 1：应用壳、登录、路由保护与全局 Agent

1. 先在 `codebase/frontend/src/App.test.tsx` 与新增的 `codebase/frontend/src/AppShell.test.tsx` 写失败用例：未登录访问受保护页面跳转 `/login`；登录后只显示拥有权限的菜单；当前导航高亮；页面提供原型对应的侧栏、顶栏、面包屑和内容容器。
2. 扩展 `codebase/frontend/src/api.ts` 的类型化 API 边界：统一读取会话 Token、请求错误标准化、写请求生成并传递 `Idempotency-Key`；保留现有 JSON/SSE Bearer 回归并为登出添加测试。
3. 在 `codebase/frontend/src/` 实现最小共享 `AppShell`、`RequireSession`、`PermissionBoundary`、导航定义和全局错误/加载/空态组件。组件只承载真实共享行为；页面专属 UI 留在页面文件内。
4. 调整 `LoginPage.tsx` 与新增测试：调用 `/api/auth/login`，只在成功后写入会话并转至工作台；错误、提交中和禁用状态与原型层级一致。实现 `/api/auth/me` 校验和登出动作。
5. 以现有 `/api/agent/threads`、`/api/agent/threads/{thread_id}/messages`、`/api/agent/runs/{run_id}/events`、`/api/agent/threads/{thread_id}/resume`、`/api/agent/threads/{thread_id}` 契约实现 `GlobalAgentDrawer.tsx`，覆盖关闭/打开、收集、预览、错误状态；SSE 使用现有受认证客户端，不能展示原始思维链。
6. 验证：`npm --prefix codebase/frontend test -- --run`、`npm --prefix codebase/frontend run build`、`git diff --check`。

### 任务 2：工作台、BI 与数据展示契约

1. 为 `WorkbenchPage.test.tsx` 和新增 `BiDashboardPage.test.tsx` 写失败用例，覆盖真实数据加载、空态、错误、筛选/图表切换和权限拒绝；断言不渲染原型的静态指标。
2. 若任务 0 证明现有健康分、指标目录/批量查询接口足以满足某项展示，直接通过 `api.ts` 接入；待办/告警、趋势、效率、排行或历史对比没有已批准 API 时，只允许在开发中显示明确阻断状态，且不得将该页面、TASK-012 或 `DEF-STAGE7-001` 标记完成。对应 `TASK-012-API-*` 前置任务集成后，必须重新实现并验证真实功能；不伪造卡片、曲线或排行。
3. 实现 `WorkbenchPage.tsx` 和新建 `BiDashboardPage.tsx`：还原原型的标题区、摘要卡、筛选栏、列表/图表区域和快捷入口的视觉层级；仅在有正式数据时渲染数值、趋势和排行榜。
4. 将路由 `/` 与 `/bi-dashboard` 接入应用壳，并为过滤条件与 URL 状态增加交互测试。
5. 验证：前端测试、构建、无静态业务数据扫描、浏览器人工对照工作台与 BI 原型；需要 Docker 的真实数据验证由 DEV-001 后续执行。

### 任务 3：组织、设备台账与系统管理

1. 先写 `FactoryModelingPage.test.tsx`、`EquipmentLedgerPage.test.tsx`、`EquipmentFormPage.test.tsx`、`EquipmentDetailPage.test.tsx`、`SystemManagementPage.test.tsx` 的失败用例，覆盖列表/树、搜索、展开、编辑校验、保存中、冲突/错误、禁用、权限拒绝和 self-only 用户可见性。
2. 用现有组织接口、设备接口、`/api/users`、`/api/roles`、`/api/permissions` 等正式契约实现以下页面：
   - `/factory-modeling`：组织树、搜索、展开/收起、新增/编辑/删除与启停；删除受阻时显示 API 返回原因。
   - `/equipment`、`/equipment/new`、`/equipment/:id/edit`、`/equipment/:id`：设备列表/筛选、详情入口、表单校验、保存、健康信息与可用历史数据。
   - `/system-management`：用户、角色/权限、审计标签页；仅显示当前 API 返回的字段与权限允许的动作。
3. 所有 POST/PATCH/DELETE 操作通过 `api.ts` 生成并测试幂等键；服务端返回的 401/403/409/422 显示为用户可理解、可恢复的页面状态。
4. 对设备历史、审计列表等尚无读取契约的原型区域，按相应 `TASK-012-API-*` 的审批和集成结果实现；没有批准/集成前不加入假历史表，也不得将页面矩阵行标为完成。
5. 验证：前端测试、构建、原型页面逐项对照；DEV-001 对实际权限、幂等及数据库副作用运行 API/容器验证。

### 任务 4：故障上报、Agent 上报、维修记录与维修执行

1. 扩展 `FaultReportPage.test.tsx`、`RepairExecutionPage.test.tsx`，新增 `AgentReportPage.test.tsx`、`MaintenanceRecordsPage.test.tsx`，先覆盖：人工上报、附件上传进度/失败、AI 草稿人工确认、诊断 `QUESTIONING`/`NO_EVIDENCE`/`UNAVAILABLE`、引用、采纳/直接开始边界、维修结果提交和禁用/权限状态。
2. 使用现有 `/api/attachments`、`/api/fault-reports`、`/api/agent/fault-reports/submit`、`/api/agent/fault-diagnosis`、`/api/agent/operation-guidance`、`/api/work-orders/{id}/repair-result`、`/api/repair-cases/similar` 与 Agent Runtime 契约实现真实流程。附件不在浏览器保留敏感正文；错误信息不泄露对象存储或扫描内部细节。
3. 实现 `/fault-report`、`/agent-report`、`/maintenance-records`、`/repair-execution` 页面，使双栏诊断、引用、问题收集、预填/人工最终字段、状态提示和操作边界符合批准原型。
4. 工单分配/列表/详情、维修记录/知识状态等如缺少读取或写入 API，受对应 `TASK-012-API-*` 阻断；只能暂停对应交互，不将原型样例写入代码，也不得据此关闭受影响 P0 行。
5. 验证：前端交互测试、API 契约测试；由 DEV-001 在隔离 live-stack 验证上传扫描、真实 RAGFlow 引用、`NO_EVIDENCE`/`UNAVAILABLE` 降级和事务状态。

### 任务 5：智能配置与整体验收封口

1. 为 `IntelligentConfigPage.tsx` 补齐 `IntelligentConfigPage.test.tsx`：模型提供商/绑定、四 Agent 独立配置、知识文档生命周期、失败重试、调用记录、Token 使用和只读指标的加载、空、错误、权限与禁用状态。
2. 仅消费现有 `/api/model-providers*`、`/api/model-bindings*`、`/api/agent-configs*`、`/api/knowledge/documents*`、`/api/metrics/*` 与 `/api/agent/*` 契约；调用记录、Token 使用和知识重试/只读指标由 `TASK-012-API-007` 补齐。该前置未集成前不能展示静态仪表盘数值，也不得标记本页面完成。
3. 新建 `06-testing/FRONTEND_PROTOTYPE_DIFFERENCE_MATRIX.md` 与适用的 `06-testing/tests/*.test.js` 静态规则：逐页确认正式路由、原型参考、真实接口、权限、状态测试和浏览器证据；明确排除“数据导入”。
4. 更新 `06-testing/TEST_CASES.md`、`06-testing/TEST_REPORT.md`、`06-testing/DEFECTS.md`、`05-development/SELF_TEST.md`、`05-development/CHECKPOINTS.md` 与交接台账，绑定实际候选 SHA、前置 API 任务、未验证项、回退方式。只有所有 `TASK-012-API-001`—`007` 已集成且所有 P0 行均有真实 API 的可复核证据，才可关闭 `DEF-STAGE7-001`。
5. 验证：
   ```bash
   npm --prefix codebase/frontend test -- --run
   npm --prefix codebase/frontend run build
   node --test 06-testing/tests/*.test.js
   git diff --check
   ```
   并由 DEV-001 在 Windows Docker Desktop/WSL2 隔离环境执行既有 API、Compose、RAGFlow、HTTPS 与浏览器关键路径验证。当前 macOS 协调环境没有 Docker，因此不得在此计划阶段报告 live-stack 已通过。

## 4. PR、检查点与回退

1. 任务 0 的规划 PR 包含 `05-development/` 设计/计划和 `06-testing/DEFECTS.md`，不适用纯治理 PR 豁免；除项目负责人确认外，必须先由 DEV-001 对精确 HEAD 正式审核，再执行集成检查和单独 Merge 授权。
2. 任务 1 至任务 5 是同一 `TASK-012` 的顺序实施工作包，不是独立任务或独立 PR。所有前端代码、测试和 TASK-012 交接始终保留在一个由 DEV-002 创建和维护的 Draft PR；工作包间以独立 Commit 和 `CHECKPOINTS.md` 保持可回退性。新增公开 API 只能由下表定义的独立 `TASK-012-API-*` 任务各自建立 PR。
3. 每个稳定单元提交可恢复 Commit，并在 `05-development/CHECKPOINTS.md` 记录前端路由、API 契约、测试结果与回退命令。回退只撤回对应修复任务的 Merge Commit；有数据迁移时采用经验证的 downgrade 或前向修复，绝不删除运行数据。
4. DEV-002 开发的每一个代码 PR 必须由 DEV-001 对当前精确 HEAD 审核；DEV-001 完成集成检查后，项目负责人另行授权，DEV-001 执行手动 Merge Commit。HEAD、目标分支、依赖或检查结论任一变化均使授权失效。

## 5. 停止条件

出现以下任一情况立即停止受影响页面，而不是以占位数据继续：

- 需要新增公开 API、数据库迁移、权限模型、部署配置或生产依赖；
- 原型与 PRD/SPEC/API 规格互相冲突；
- 真实 API 无法表达原型声称的业务状态；
- 浏览器或隔离 live-stack 发现 P0 鉴权、数据泄露、状态迁移或附件安全问题。

停止后在 `06-testing/DEFECTS.md` 登记问题，并通过 `workflow/CHANGE_REQUESTS.md` 请求项目负责人针对精确范围的决定。
