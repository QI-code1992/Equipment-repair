# 原型覆盖情况

- 候选基线：`03-ui-prototype/PROTOTYPE_BASELINE.md`
- 状态：等待 Stage 2 审批

| 流程 | 原型证据 | 覆盖情况 | 缺口 |
|---|---|---|---|
| Login and navigation | login/index/sidebar | partial | production auth and forbidden states |
| Equipment CRUD | ledger/add/edit/detail | visual | API validation, duplicate and deactivation guards |
| Manual fault | fault-report | visual | backend submit/idempotency |
| AI fault report | global Agent + fault page | visual/partial | real LangGraph and permission service |
| Intelligent query | Agent/config metric view | visual | real 40-metric catalog/API |
| Diagnosis/advice | agent-report/detail | visual | RAG citations and human review backend |
| Repair execution | repair-execution/maintenance-records | visual | work-order API and closure rules |
| Health score | health-score-service adapter + pages | adapter/demo | production calculator and failure state |
| System management | system-management | visual | server authorization and audit |
| Data import | historical page only | excluded | intentionally not current |
