# 原型/页面检查点

## PCP-001: Imported multi-page prototype

- 状态：候选版 / 等待 Stage 3 审批
- 范围：导入静态页面、共享资源、Agent 抽屉和健康分适配器
- 关联基线：Stage 1 候选 PRD/SPEC；Stage 2 候选页面矩阵
- 来源：`03-ui-prototype/prototype/`
- Commit SHA：`32d1b7b`
- Exported evidence: source HTML and original PDF are recoverable from `snapshot/legacy-import-20260714`
- Screens/components/states: listed in `02-product-interaction-design/PAGE_FUNCTION_MATRIX.md`
- Verification: server start and HTTP 200 smoke test passed before migration; full post-migration check pending
- Restore: `git restore --source 32d1b7b -- 03-ui-prototype/prototype`
- Notes: not a formal Stage 3 baseline until user approves the visual and interaction package.

## PCP-002: Prototype-to-document consistency audit

- Status: Candidate / changes requested; not approved
- Scope: static audit of 14 current pages and shared Agent/health-score assets
- Related artifact: `03-ui-prototype/PROTOTYPE_AUDIT.md`
- Findings: factory modeling, Agent report, intelligent configuration detail, AI duration gate, and work-order label mapping were added to canonical documents.
- Limitation: no browser screenshot or production API verification was available in this audit.

## PCP-003: User entry and scoped management interaction candidate

- Status: Candidate / awaiting Stage 2 review
- Scope: global user capsule, profile/security modals, permission-scoped user management, self-only account card
- Commit SHA: `aa8a307`
- Verification: static tests and HTTP 200 smoke checks passed; browser/runtime visual approval pending.

## PCP-004: Business notification panel interaction candidate

- Status: Candidate / awaiting Stage 2 review
- Scope: topbar SVG bell, unread badge, local business notification list, read state and in-panel target navigation
- Verification: static checks and JavaScript syntax checks passed; browser/runtime visual approval pending.

## PCP-005: Global notification entry candidate

- Status: Candidate / awaiting Stage 2 review
- Scope: shared notification initialization across all topbar page shells
- Verification: static checks and JavaScript syntax checks passed; browser/runtime visual approval pending.

## PCP-006: Topbar refresh action cleanup

- Status: Candidate / awaiting Stage 2 review
- Scope: remove obsolete `刷` actions from BI and equipment topbars while retaining global bell and user entry.
- Verification: static checks and JavaScript syntax checks passed.

## PCP-007: Logout navigation candidate

- Status: Candidate / awaiting Stage 2 review
- Scope: confirmed global logout returns to `login.html`; cancellation preserves the current page.
- Verification: static regression and JavaScript syntax checks passed.

## PCP-008: Modal notification scroll candidate

- Status: Candidate / awaiting Stage 2 review
- Scope: notification scrim, body scroll lock and independently scrollable notification list.
- Verification: static regression and JavaScript syntax checks passed.

## PCP-009: Unread notification marker candidate

- Status: Candidate / awaiting Stage 2 review
- Scope: unread items show a red dot; read items show no dot.
- Verification: static regression and JavaScript syntax checks passed.

## PCP-010: Workbench sidebar status card cleanup

- Status: Candidate / awaiting Stage 2 review
- Scope: remove the “AI诊断在线” card from the workbench sidebar.
- Verification: static regression passed.

## PCP-011: Global sidebar explanation cleanup

- Status: Candidate / awaiting Stage 2 review
- Scope: remove all shared sidebar bottom explanation cards across page shells.
- Verification: static regression passed.

## PCP-012: Workbench filter and detail-link integration

- 状态：Stable / 等待 Stage 3 审批
- 范围：工作台组织范围筛选、指标/待办联动、健康概览、趋势筛选、刷新反馈与设备详情跳转
- 来源：`03-ui-prototype/prototype/pages/workbench.html`
- 分支：`feature/workbench-integration`
- Commit SHA：`4a5f302ffe42c972186426d5f8587cd8059adc6e`
- 验证：`node 06-testing/tests/workbench-integration.test.js`；全量 `06-testing/tests/*.test.js`；`git diff --check`
- 结果：12 项静态检查全部通过
- 恢复：`git restore --source 4a5f302ffe42c972186426d5f8587cd8059adc6e -- 03-ui-prototype/prototype/pages/workbench.html 06-testing/tests/workbench-integration.test.js`
- 备注：仅工作台页面和其专用测试发生变更；其他页面与共享 `app.js`、`app.css`、`global-agent.js` 未修改。
