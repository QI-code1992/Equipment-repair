# TASK-013 正式前端与原型差异矩阵

- 候选分支：`codex/task-013-prototype-fidelity-remediation`。
- 当前完整候选：`aaa55274ef953c3ec6d2fcb9a4bf7cf78b9cda72`。
- 原型唯一来源：`03-ui-prototype/prototype/pages/*.html`；正式实现唯一来源：`codebase/frontend/`。
- 范围：除明确排除的 Data import 外，覆盖全部 16 个 P0 正式路由和跨页全局 Agent 抽屉。
- 判定口径：表中“代码对照完成”仅表示正式 React 结构、信息层级、交互入口和真实 API/权限边界已按原型逐页核对；不等同于浏览器视觉验收、Windows live-stack 验证、Stage 6 通过或 Stage 7 解锁。

| 页面 | 正式路由 | 原型参考 | 正式数据/操作契约 | 自动化覆盖 | 当前状态 | 尚未完成的证据 |
|---|---|---|---|---|---|---|
| 登录 | `/login` | `pages/login.html` | `/api/auth/login`、`/api/auth/me`、会话存储 | `LoginPage.test.tsx`、`App.test.tsx`、`api.test.ts` | 代码对照完成；固定桌面视口已检查 | 真实测试账号浏览器登录/退出、隔离 live-stack |
| 工作台 | `/` | `pages/workbench.html` | `/api/workbench/todos`、告警摘要、快捷入口、单设备健康查询 | `WorkbenchPage.test.tsx`、`App.test.tsx` | 代码对照完成；缺失聚合契约保留受控空态 | 认证浏览器对照、真实数据状态 |
| 驾驶舱 BI | `/bi-dashboard` | `pages/bi-dashboard.html` | `/api/bi/dashboard?organization_id=&period=day\|week\|month`、`/api/equipment` | `PortalPages.test.tsx`、后端 `test_task012_read_apis.py` | 代码对照完成；趋势粒度、四项效率模块与八列设备健康表均恢复为原型结构，缺失数据保持受控空态 | 浏览器筛选、固定视口视觉对照、完整 BI live 数据 |
| 工厂建模 | `/factory-modeling` | `pages/factory-modeling.html` | `/api/organizations` | `PortalPages.test.tsx` | 代码对照完成；树、详情、编辑和禁用边界已接入 | 认证浏览器树操作、真实写入联调 |
| 设备台账 | `/equipment` | `pages/equipment-ledger.html` | `/api/equipment`、`/api/organizations` | `PortalPages.test.tsx`、`api.test.ts` | 代码对照完成；筛选、空态、健康分不可用态已接入 | 浏览器视口对照、真实权限/数据联调 |
| 新增设备 | `/equipment/new` | `pages/equipment-add.html` | `/api/equipment`、`/api/organizations`、`/api/users` | `PortalPages.test.tsx` | 代码对照完成；组织级联、日期、图片引用和保存反馈已接入 | 浏览器表单验证、附件/组织真实联调 |
| 设备详情 | `/equipment/:id` | `pages/equipment-detail.html` | `/api/equipment/{id}`、维修历史 | `PortalPages.test.tsx`、`api.test.ts` | 代码对照完成；资产摘要、健康边界、五项 tabs 和历史空态已接入 | 认证浏览器 tabs/详情视觉对照、真实历史数据 |
| 编辑设备 | `/equipment/:id/edit` | `pages/equipment-edit.html` | `/api/equipment/{id}`、`/api/organizations`、`/api/users` | `PortalPages.test.tsx` | 代码对照完成；完整正式字段回填，未编辑字段不被清空 | 浏览器编辑保存、冲突/权限 live 验证 |
| 智能配置 | `/intelligent-config` | `pages/intelligent-config.html` | 模型、Agent、知识文档正式配置与重试入口 | `IntelligentConfigPage.test.tsx`、`PortalPages.test.tsx`、`api.test.ts` | 代码对照完成；五项一级页签和真实接口边界已接入 | 认证浏览器页签、RAGFlow/知识生命周期 |
| 智能审计 | `/intelligence-audit` | 智能配置原型审计/知识区 | 智能调用审计、知识文档状态与受控重试 | `PortalPages.test.tsx`、`api.test.ts` | 代码对照完成；审计-only 用户的重试按钮保持禁用 | 双权限点击/请求、浏览器和 live-stack |
| 故障上报 | `/fault-report` | `pages/fault-report.html` | 附件、故障创建、AI 预览、诊断和开始维修 | `FaultReportPage.test.tsx`、`PortalPages.test.tsx` | 代码对照完成；查询/列表区域和人工/AI 状态边界已接入 | 附件扫描、诊断证据和浏览器 E2E |
| AI 故障上报 | `/agent-report` | `pages/agent-report.html` | Agent Runtime、附件安全引用、正式故障提交 | `PortalPages.test.tsx`、`api.test.ts` | 代码对照完成；对话、缺失字段、确认卡和运行状态已接入 | 认证浏览器流程、真实 Agent/附件生命周期 |
| 维修记录 | `/maintenance-records` | `pages/maintenance-records.html` | `/api/maintenance-records` 查询、分页、知识状态筛选 | `PortalPages.test.tsx` | 代码对照完成；概览/列表双视图、重置、禁用导出和分页已接入 | 浏览器筛选/分页、真实数据 |
| 维修记录详情 | `/maintenance-records/:id` | `pages/maintenance-records.html` 详情状态 | `/api/maintenance-records/{id}` | `PortalPages.test.tsx` | 代码对照完成；工单、故障、根因、方案、结果和知识状态卡已接入 | 认证浏览器详情、真实记录联调 |
| 维修执行 | `/repair-execution` | `pages/repair-execution.html` | 工单、诊断、操作指引 SSE、维修结果提交 | `RepairExecutionPage.test.tsx`、`PortalPages.test.tsx`、`api.test.ts` | 代码对照完成；三栏工作区、流式状态、空证据和写入保护已接入 | 浏览器 E2E、真实 SSE/RAGFlow/附件 |
| 系统管理 | `/system-management` | `pages/system-management.html` | 用户、角色、权限目录、登录/操作日志 | `PortalPages.test.tsx`、`api.test.ts` | 代码对照完成；四个原型分区与读写权限边界已接入 | 浏览器双权限、分页与真实审计数据 |

## 跨页全局 Agent

- 入口：应用壳右下角圆形机器人悬浮图标，仅在 `intelligence:agent` 权限存在时显示。
- 原型对照：入口按原型固定右下位置、3 秒闲置半透明、悬停/聚焦恢复，打开抽屉隐藏、关闭恢复；三类快捷任务（故障上报、智能问数、操作指引）、新建任务/线程历史、运行状态、SSE 增量、错误和关闭/遮罩行为均保留。
- 当前切片提交：`d53f894f8728333e34b9dd504b3e8dcb878a40c1`；入口源码 `03-ui-prototype/prototype/assets/global-agent.js`，样式基线 `03-ui-prototype/prototype/assets/app.css`。
- 明确边界：原型拖拽和左右边缘吸附未在本切片实现；当前整改针对用户指出的悬浮入口、显隐和抽屉互斥，不扩展产品范围。
- 证据：`App.test.tsx`、`api.test.ts`、`06-testing/tests/test_agent_runtime.py`；真实浏览器和 live-stack 仍由 DEV-001 在最终候选上独立执行。

## 共享导航

- 原型主导航仅为单一“业务导航”分组及 8 项 `01`—`08`：工作台、驾驶舱 BI、工厂建模、设备台账、故障上报、维修记录、系统管理、智能配置。
- `App.test.tsx` 已覆盖全权限会话下的链接顺序、编号和隐藏项；Agent 上报、智能审计、维修执行等二级路由不可出现在主导航中，但继续由正式路由和权限守卫访问。

## 明确排除

Data import 保留在历史原型中，不在当前正式产品范围或本次验证范围内。原型源码、原型 CSS 和原型运行时未复制到正式前端。

## 总体门禁

候选代码已完成本地自动化回归，当前仍为 TASK-013 Stage 5 开发候选。需由 DEV-001 对精确 HEAD `aaa55274ef953c3ec6d2fcb9a4bf7cf78b9cda72` 统一审核；审核前不申请 Merge、不合并、不关闭 `DEF-STAGE7-001`，Stage 6/7/8 继续锁定。
## 工作台布局复核（2026-08-07）

- 发现：通用 `.data-card` 跨列样式使五张 KPI 卡片实际呈两列，且主工作区队列卡片错误跨列；与 `pages/workbench.html` 的五卡横排和队列/侧栏双栏布局不一致。
- 修复：工作台局部规则覆盖通用跨列规则；保留正式 API 数据和缺口空态，不改变业务契约。
- 自动化：工作台定向 `4 passed`；全量前端 `99 passed`；构建通过。

## 维修记录概览布局复核（2026-08-07）

- 发现：`pages/maintenance-records.html` 要求六张 KPI 横向排列、四张图表两列排列；正式页面为三列 KPI，且图表卡继承 `.data-card` 跨列规则后被错误拉成单列。
- 修复：维修记录页局部恢复六列 KPI 和两列图表网格，保持窄视口下的单列响应式布局；业务数据与受控空态未改变。
- 自动化：新增 KPI/图表结构契约；全量前端 `100 passed`、生产构建和 15 项 Node 静态回归通过。

## 驾驶舱 BI 趋势粒度复核（2026-08-07）

- 发现：正式页面将原型的日/周/月趋势粒度错误替换成“趋势/组织排行”视图切换，导致趋势区缺少原型定义的控制方式。
- 修复：恢复日、周、月三个趋势粒度按钮；每次选择均以对应 `period` 调用正式 BI API。三项趋势图继续只消费 API 返回序列；健康评分趋势缺少正式序列时保持受控空态。
- 自动化：新增日/周/月与 API 重载回归；全量前端 `101 passed`、生产构建、15 项 Node 静态回归、JSON 解析和 `git diff --check` 通过。

## 驾驶舱 BI 效率分析复核（2026-08-07）

- 发现：原型的效率分析包含计划工单完成率、平均响应时长、平均维修时长和首次修复率四项；正式页面错误替换为三项不同指标。
- 修复：恢复四项原型模块及四列布局。平均维修时长仅使用正式 API 的实际值；其余三项缺少契约时显示受控不可用状态。
- 自动化：新增四项模块回归先失败后通过；完整验证随本切片执行。
