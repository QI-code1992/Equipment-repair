# 页面与功能矩阵

- 基线：已批准 v1.0
- 状态：Stage 2 已批准；见 `workflow/STAGE_APPROVALS.md` 的 Gate-003

| 页面 | P0 功能 | 角色 | 关键状态 | 原型 |
|---|---|---|---|---|
| Login | login/logout | all | default/error/disabled/loading | `prototype/pages/login.html` |
| Workbench | todo, alert summary, shortcut | authenticated users with menu access | default/empty/error | `prototype/pages/workbench.html`, formal route `/workbench` |
| 驾驶舱 BI | 管理摘要、趋势、效率、区域/工厂/车间排行、历史对比、全局筛选 | admin/equipment admin/repair/view | 默认/空态/错误/筛选/图表切换 | `prototype/pages/bi-dashboard.html`；详见 `驾驶舱BI设计细化.md` |
| Factory modeling | organization tree, search, expand/collapse, CRUD, enable/disable cascade | admin | tree/detail/form/blocked delete | `prototype/pages/factory-modeling.html` |
| Equipment ledger | list/filter/detail entry | admin/equipment admin/repair/operator | loading/empty/error/permission | `prototype/pages/equipment-ledger.html` |
| Equipment add/edit/detail | CRUD, owner, health, history | admin/equipment admin | validation/saving/error/forbidden | add/edit/detail pages |
| Fault report | manual submit, AI draft review | all with fault permission | draft/validation/submitted/error | `prototype/pages/fault-report.html` |
| Fault report / start repair diagnosis | prediagnosis loading, configuration-driven dialogue, citations, dynamic evidence questions, adopt/direct-start boundary, end-repair summary | repair worker / equipment admin | loading/questioning/alarm-code-required/evidence-insufficient/diagnosis-ready/unavailable/adopted/direct-start | `prototype/pages/fault-report.html` |
| Agent report | authorized-device context, structured summary, required-field completion, handoff, formal submit gate | Agent-authorized users | collecting/missing fields/disabled submit/ready | `prototype/pages/agent-report.html` |
| Global Agent | three tabs, history, drawer | all authenticated users | closed/open/collecting/preview/error | global scripts |
| Maintenance records | list/detail modal/knowledge status | admin/equipment admin/repair | empty/loading/error | `prototype/pages/maintenance-records.html` |
| Repair execution | assigned work, result, submit | repair worker | editing/submitted/forbidden | `prototype/pages/repair-execution.html` |
| System management | users, roles, menu/operation, audit; permission-scoped self-only user view | admin / granted users / ordinary users | tabs/permission/self-only/error | `prototype/pages/system-management.html` |
| Intelligent config | model resources, four Agents, KB pipeline/retry, call records, Token usage, readonly 40 metrics | admin | upload/index failure/test/readonly | `prototype/pages/intelligent-config.html` |
| Data import | historical only | none current | excluded | retained in snapshot only |

说明：独立 `/intelligence-audit` 页面取消；调用记录和知识文档状态由智能配置页承载。登录页和系统管理页的正式找回密码/修改密码流程属于账户安全增量，需覆盖请求、校验、会话失效、审计和错误状态。

## 状态覆盖缺口

The prototype shows many default and demo states. Stage 3 must add or document verified loading, empty, error, disabled, permission and boundary evidence for each P0 page before approval.
