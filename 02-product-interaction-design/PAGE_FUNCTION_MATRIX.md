# Page / Function Matrix

- Baseline: Candidate v1.0
- Status: Awaiting Stage 2 approval

| Page | P0 functions | Roles | Key states | Prototype |
|---|---|---|---|---|
| Login | login/logout | all | default/error/disabled/loading | `prototype/pages/login.html` |
| Workbench | todo, alert summary, shortcut | admin/equipment admin/repair | default/empty/error | `prototype/pages/workbench.html` |
| BI dashboard | cards, trends, Top 5, filters | admin/equipment admin/repair/view | default/empty/error/filter | `prototype/pages/bi-dashboard.html` |
| Equipment ledger | list/filter/detail entry | admin/equipment admin/repair/operator | loading/empty/error/permission | `prototype/pages/equipment-ledger.html` |
| Equipment add/edit/detail | CRUD, owner, health, history | admin/equipment admin | validation/saving/error/forbidden | add/edit/detail pages |
| Fault report | manual submit, AI draft review | all with fault permission | draft/validation/submitted/error | `prototype/pages/fault-report.html` |
| Global Agent | three tabs, history, drawer | Agent-authorized users | closed/open/collecting/preview/error | global scripts |
| Maintenance records | list/detail/knowledge status | admin/equipment admin/repair | empty/loading/error | `prototype/pages/maintenance-records.html` |
| Repair execution | assigned work, result, submit | repair worker | editing/submitted/forbidden | `prototype/pages/repair-execution.html` |
| System management | users, roles, menu/operation, audit | admin | tabs/permission/error | `prototype/pages/system-management.html` |
| Intelligent config | models, KB, Agent, readonly metrics | admin | upload/index failure/readonly | `prototype/pages/intelligent-config.html` |
| Data import | historical only | none current | excluded | retained in snapshot only |

## State coverage gap

The prototype shows many default and demo states. Stage 3 must add or document verified loading, empty, error, disabled, permission and boundary evidence for each P0 page before approval.
