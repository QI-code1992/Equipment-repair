# TASK-013 正式前端与原型差异矩阵

- 候选分支：`codex/task-013-prototype-fidelity-remediation`。
- 最新增量候选：`5695716`；本次修复覆盖深层路由上下文、移动端导航折叠和设备台账空态入口。
- 范围：除明确排除的数据导入外，覆盖 `PAGE_FUNCTION_MATRIX.md` 的全部 P0 页面。
- 判定：本表不替代最终审核或浏览器 live-stack 验证；`实现中候选` 表示已在 Draft PR 中接入正式契约，尚未可宣布完成。当前所有页面仍保留该状态，原因是最终浏览器/live-stack 和统一 DEV-001 审核尚未执行。

| 页面 | 正式路由 | 原型参考 | 正式数据/操作契约 | 自动化覆盖 | 当前状态 | 后续证据 |
|---|---|---|---|---|---|---|
| Login | `/login` | `pages/login.html` | `/api/auth/login`、`/me`、`/session` | `App.test.tsx`、`api.test.ts` | 实现中候选 | DEV-001 浏览器登录/登出 |
| Workbench | `/` | `pages/workbench.html` | `/api/workbench/todos`、`alert-summary`、`shortcuts`、健康分 | `WorkbenchPage.test.tsx` | 实现中候选 | 待办、空态、权限浏览器验证 |
| 驾驶舱 BI | `/bi-dashboard` | `pages/bi-dashboard.html` | `/api/bi/dashboard?organization_id=&period=day|week|month` | `PortalPages.test.tsx`、`test_task012_read_apis.py` | 实现中候选 | 筛选、日/周/月趋势和图表浏览器对照 |
| 工厂建模 | `/factory-modeling` | `pages/factory-modeling.html` | `/api/organizations` | `PortalPages.test.tsx` | 实现中候选 | 树、编辑、删除阻断浏览器验证 |
| 设备台账及表单 | `/equipment*` | 设备原型页面 | `/api/equipment`、`/organizations`、`/users`、`/api/maintenance-history/equipment/{id}` | `PortalPages.test.tsx`、`api.test.ts` | 实现中候选 | 写入幂等/冲突、历史趋势浏览器验证 |
| 故障上报 | `/fault-report` | `pages/fault-report.html` | 附件、故障、诊断、开始维修 | `FaultReportPage.test.tsx` | 实现中候选 | 附件扫描、诊断 live-stack |
| AI 故障上报 | `/agent-report` | `pages/agent-report.html` | Agent thread/message、`/api/attachments`、正式上报 | `PortalPages.test.tsx` | 实现中候选 | 收集/附件安全/确认提交浏览器验证 |
| 全局 Agent | 应用抽屉 | 原型全局脚本 | `GET /api/agent/threads`、详情、message、resume、SSE | `App.test.tsx`、`api.test.ts`、`test_agent_runtime.py` | 实现中候选 | 三类 Agent/SSE/权限浏览器验证 |
| 维修记录 | `/maintenance-records` | `pages/maintenance-records.html` | `/api/maintenance-records*`（设备/知识状态筛选、分页） | `PortalPages.test.tsx` | 实现中候选 | 详情/知识状态浏览器验证 |
| 维修执行 | `/repair-execution` | `pages/repair-execution.html` | `/api/work-orders*`（状态筛选/详情）、诊断、完工 | `RepairExecutionPage.test.tsx` | 实现中候选 | 分配范围/状态冲突浏览器验证 |
| 系统管理 | `/system-management` | `pages/system-management.html` | 用户、角色、权限、`/api/audit-events`（筛选/分页） | `PortalPages.test.tsx` | 实现中候选 | self-only/最后管理员浏览器验证 |
| 智能配置 | `/intelligent-config`、`/intelligence-audit` | `pages/intelligent-config.html` | Agent 配置、知识重试、调用统计 | `App.test.tsx`、`api.test.ts`、`PortalPages.test.tsx` | 实现中候选 | RAGFlow/重试浏览器验证 |

## 明确排除

Data import 保留在历史原型中，不在当前正式产品范围或本次验证范围内。
