# TASK-013：P0 正式前端原型一致性整改实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use `executing-plans` task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标：** 使 16 个正式 React 路由在布局、信息层级、关键交互和状态反馈上符合已批准的 Stage 3 原型，同时继续只消费真实 API 和权限。

**架构：** 保留 `codebase/frontend/` 作为唯一正式前端；`03-ui-prototype/prototype/` 只作为只读视觉与交互基线。先以共享应用壳和设计令牌统一页面骨架，再按资产、现场作业、智能运维和系统管理领域逐页替换当前通用表格/表单式页面；所有写操作经既有 API，发现契约不足时停止该页并登记 Stage 5 API 缺口。

**技术栈：** React、TypeScript、React Router、现有 Vitest 与既有 API 客户端；不得新增生产依赖。

## 1. 回流依据与边界

- 发现基线：`e8a28cee7515ad58e025ec81c65b460284919d75`。
- 原因：项目负责人于 2026-08-04 在本地静态 UI 演示中确认，正式页面与批准原型存在实质偏离；这属于 `DEF-STAGE7-001` 的实现偏离复开，不是新的产品偏好或原型变更。
- 当前证据：`/factory-modeling` 现为树形表格与常驻“新增组织节点”表单；批准原型为左侧组织树、右侧节点详情/编辑面板、上下级信息卡与上下文操作区的双栏操作台。
- 不得修改：PRD、SPEC、页面功能矩阵、原型源码、公开 API、权限模型、迁移、部署和依赖。
- 不得使用：mock 业务数据、静态仪表盘数值、原型运行时代码、复制的原型 HTML/CSS/JavaScript。
- 阶段：该任务是 Stage 6 未通过期间的 Stage 5 回流修复；Stage 6、Stage 7、Stage 8 均继续锁定。

## 2. 页面差异矩阵与完成定义

| 正式路由 | 原型参考 | 当前偏离 | 整改完成定义 |
| --- | --- | --- | --- |
| `/login` | `login.html` | 最小居中表单，缺少原型品牌层级、错误/禁用反馈细节 | 实现原型登录双栏/品牌信息层级、字段级校验、加载、失败与返回原路径状态。 |
| `/` | `workbench.html` | 工作台信息密度、待办/预警/快捷操作层级不足 | 以真实待办、告警、健康与快捷事项实现原型卡片和状态区域；无数据时明确空态。 |
| `/bi-dashboard` | `bi-dashboard.html` | 文本列表替代图表、筛选与历史对比控制台 | 以真实聚合数据实现全局筛选、指标卡、趋势/排行切换、效率和历史对比；数据不可用时显示错误而非伪图表。 |
| `/factory-modeling` | `factory-modeling.html` | 当前树表与常驻表单替代原型双栏详情工作区 | 实现左树右详情/编辑工作区、搜索、展开/折叠、上下级卡片、状态级联提示、删除受限提示和按上下文打开的表单。 |
| `/equipment` | `equipment-ledger.html` | 通用表格缺少原型筛选、资产摘要和操作层级 | 实现筛选栏、设备状态/健康标签、列表操作、加载/空/错误/权限状态和详情入口。 |
| `/equipment/new` | `equipment-add.html` | 表单字段、图片/日期与保存反馈未按原型组织 | 实现分组表单、必填/校验、组织与负责人选择、日期/图片字段、保存中/失败/成功跳转。 |
| `/equipment/:id` | `equipment-detail.html` | 当前仅定义列表，缺少资产概览、健康和历史视觉层级 | 实现设备身份、运行/健康摘要、关键参数、维修历史和趋势区域；真实无记录时显示空态。 |
| `/equipment/:id/edit` | `equipment-edit.html` | 当前编辑不保护完整已有字段且缺少原型布局 | 复用新增表单布局并完整回填正式字段；只提交用户变更与 API 允许字段，防止清空未编辑信息。 |
| `/intelligent-config` | `intelligent-config.html` | 配置表单未形成原型的控制面、知识流程与指标分区 | 实现模型、Agent、知识文档、调用记录/只读指标分区，明确权限、加载、失败与重试边界。 |
| `/intelligence-audit` | 智能配置原型的审计/知识状态区 | 独立页面仅为通用表格，操作与权限关系不清 | 实现审计指标、知识状态筛选和仅在双权限满足时可用的重试操作；无写权限时不可点击。 |
| `/fault-report` | `fault-report.html` | 现场报修、附件、AI 预览、诊断证据与人工路径未形成原型流程 | 实现设备上下文、附件扫描中禁用、人工提交与 AI 预览互斥、诊断问答/引用/采纳/直接维修状态。 |
| `/agent-report` | `agent-report.html` | 结构化采集、缺字段追问和确认卡层级不足 | 实现 Agent 对话、缺字段提示、正式字段确认与受控附件状态；只在完整且有权限时允许提交。 |
| `/maintenance-records` | `maintenance-records.html` | 缺少原型筛选、状态标签和详情工作流 | 实现查询/筛选/分页、知识状态、行级详情入口、空态和权限拒绝。 |
| `/maintenance-records/:id` | `maintenance-records.html` 详情状态 | 当前定义列表式详情，未呈现维修摘要层级 | 实现工单、故障、根因、方案、结果、更换件和知识状态的详情卡与返回路径。 |
| `/repair-execution` | `repair-execution.html` | 工单、诊断摘要、维修结果录入和提交边界未按原型组织 | 实现工单选择/加载、不可回退的加载失败、诊断摘要、维修结果表单、提交中保护和成功反馈。 |
| `/system-management` | `system-management.html` | 账号/角色/权限/审计由连续表格堆叠，缺少原型分区与权限边界 | 实现标签页式账号、角色、权限与审计区；读写权限分别控制入口和操作。 |

全局 Agent 抽屉不是独立页面，但属于跨页 P0：须保留原型的抽屉、三类任务入口、历史、进行中保护、SSE 增量状态与权限解释。

## 3. 文件责任与实施顺序

### 工作包 1：共享视觉骨架与跨页状态

**修改文件：** `codebase/frontend/src/App.tsx`、`codebase/frontend/src/styles.css`、`codebase/frontend/src/App.test.tsx`。

- [ ] 先为导航分组、当前页标题、权限隐藏/拒绝、全局 Agent 入口和移动端折叠写失败交互测试。
- [ ] 从 `03-ui-prototype/VISUAL_GUIDELINES.md` 和 `DESIGN_TOKENS.json` 提取颜色、间距、排版、状态标签、卡片、表格、表单和抽屉令牌，写入正式样式；不得复制原型 CSS。
- [ ] 用共享应用壳实现侧栏、顶部栏、面包屑、用户入口、通知区域和响应式布局；移除“前端基础工程已启用”等开发占位文案。
- [ ] 跑 `npm --prefix codebase/frontend test -- --run` 与 `npm --prefix codebase/frontend run build`，记录真实结果。

### 工作包 2：工作台、BI、组织与设备域

**修改文件：** `codebase/frontend/src/WorkbenchPage.tsx`、`codebase/frontend/src/WorkbenchPage.test.tsx`、`codebase/frontend/src/PortalPages.tsx`、`codebase/frontend/src/PortalPages.test.tsx`、`codebase/frontend/src/styles.css`、`codebase/frontend/src/api.ts`（仅当现有已批准 API 已有字段未被消费）。

- [ ] 为工作台、BI、工厂建模、设备台账、设备新增/详情/编辑的默认、加载、空、错误、权限和关键写操作状态逐页添加失败测试。
- [ ] 将工厂建模改为原型定义的双栏工作区；创建/编辑只在明确的上下文操作后出现，禁止在每次页面加载时展示常驻新建表单。
- [ ] 将 BI 文本列表替换为不新增依赖的语义图形/趋势呈现；图形数值只来自 API 返回的序列，空数据不画虚构曲线。
- [ ] 使设备新增/编辑按 API 完整字段回填与提交；任何无法由现有契约安全读写的字段先登记缺口，不以 `null`、空数组或推断值覆盖。
- [ ] 运行该域前端测试、相关后端契约测试、构建和 `git diff --check`。

### 工作包 3：现场作业、维修与 Agent 域

**修改文件：** `codebase/frontend/src/FaultReportPage.tsx`、`codebase/frontend/src/FaultReportPage.test.tsx`、`codebase/frontend/src/RepairExecutionPage.tsx`、`codebase/frontend/src/RepairExecutionPage.test.tsx`、`codebase/frontend/src/PortalPages.tsx`、`codebase/frontend/src/PortalPages.test.tsx`、`codebase/frontend/src/App.tsx`、`codebase/frontend/src/api.ts`、`codebase/frontend/src/styles.css`。

- [ ] 为故障上报、AI 上报、维修记录、维修详情、维修执行和全局 Agent 的加载、扫描禁用、权限、空证据、不可用、保存中、失败与成功状态补齐失败测试。
- [ ] 将诊断与操作指引的状态消息、引用、采纳/直接维修边界和附件扫描状态放在与原型一致的上下文位置；不得把 `UNAVAILABLE` 或 `NO_EVIDENCE` 渲染为空白。
- [ ] 将全局 Agent 的 SSE 事件按流式增量展示；连接失败必须在抽屉内可见，不能等待流结束后才显示运行状态。
- [ ] 运行此域前端测试、关联后端 Agent/维修测试、构建和 `git diff --check`。

### 工作包 4：智能配置、审计与系统管理域

**修改文件：** `codebase/frontend/src/IntelligentConfigPage.tsx`、`codebase/frontend/src/IntelligentConfigPage.test.tsx`、`codebase/frontend/src/PortalPages.tsx`、`codebase/frontend/src/PortalPages.test.tsx`、`codebase/frontend/src/api.ts`、`codebase/frontend/src/styles.css`。

- [ ] 为模型/Agent 配置、知识状态重试、调用指标、账号、角色、权限目录和审计事件的只读/可写双权限状态写失败测试。
- [ ] 将系统管理拆为原型对应的标签页/分区；只读用户不能看见可执行的写操作，写入成功后刷新真实数据而非提示“请刷新确认”。
- [ ] 将智能配置与审计按正式数据域呈现；没有持久化调用记录或指标时明确空态，禁止固定指标或固定知识状态。
- [ ] 运行此域前端测试、适用后端权限/审计测试、构建和 `git diff --check`。

### 工作包 5：逐页原型对照、完整回归与交接

**修改文件：** `06-testing/TEST_CASES.md`、`06-testing/TEST_REPORT.md`、`05-development/SELF_TEST.md`、`05-development/CHECKPOINTS.md`、`workflow/DEV_TO_PM_HANDOFF.md`。

- [ ] 对 16 条路由在固定桌面视口逐页对照：导航、标题/面包屑、主要布局、关键操作、默认/空/错误/权限状态。
- [ ] 将每页对照结果绑定候选 SHA、原型源文件、浏览器、视口和截图路径；截图是视觉证据，不替代真实 API 或 Stage 6 live-stack 证据。
- [ ] 运行前端全量测试、生产构建、后端受影响回归、Node 静态回归和 `git diff --check`。
- [ ] 由 DEV-001 在 Windows 隔离环境运行 Docker、RAGFlow、附件扫描、HTTPS 和认证浏览器 E2E；未执行项必须保持未验证。

## 4. 任务门禁、审核与回退

- 开发分支：`codex/task-013-prototype-fidelity-remediation`。
- 开发者：DEV-002；指定审核者和集成负责人：DEV-001；获批后的 Merge 执行者：DEV-001（非任务开发者）。
- 开始条件：本任务书和状态台账的治理候选先被确认并合入，且项目负责人单独确认“允许启动 TASK-013 业务页面代码修改”。本次对治理文档的确认不等于该编码启动确认。
- PR：单一 Draft PR，目标 `codex/stage-05-integration`；所有页面与共享组件修订都在同一 PR，页面域之间以检查点提交保持可回退。
- 审核：DEV-001 仅对完整候选精确 HEAD 进行正式审核；审核批准不等于 Merge 授权。
- 回退：只允许针对 TASK-013 的独立 Merge Commit 执行经隔离验证的 `git revert -m 1 <merge-sha>`；不得回退 TASK-012、删除数据或覆盖环境。

## 5. 完成条件

- 16 个路由及全局 Agent 均有原型对照记录，且不再存在“通用壳/表格/常驻表单替代批准工作区”的页面。
- 每页只使用真实 API、真实权限与真实运行状态；无原型运行依赖、无 mock 业务数据、无新增生产依赖。
- 前端测试、生产构建、受影响后端测试、Node 静态回归和 `git diff --check` 全部以实际结果记录。
- 浏览器对照与 Windows 隔离 live-stack 证据绑定新的精确集成 SHA；在该证据形成前不得关闭 `DEF-STAGE7-001`，不得宣称 Stage 6/7/8 通过。
