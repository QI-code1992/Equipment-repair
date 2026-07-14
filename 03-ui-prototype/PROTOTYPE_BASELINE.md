# 原型基线

- 基线：候选版 v1.0
- 状态：等待 Stage 3 审批
- 来源：`03-ui-prototype/prototype/`
- 导入源码 Commit：`c544c2d`（原始快照）；迁移 Commit：`32d1b7b`

## 包含内容

Login, workbench, BI, factory model, equipment ledger/add/edit/detail, fault report, Agent report, maintenance records, repair execution, system management and intelligent configuration. The prototype is static HTML/CSS/JavaScript and includes a local Node server and static rule checks.

## 约束

- It is design/reference evidence, not a production service.
- Static numbers, old labels and historical data-import navigation must not override Stage 1.
- `assets/health-score-service.js` is an adapter shape only; production health calculation belongs to the backend service.
- P0 state coverage still needs verification for loading, empty, error, disabled, permission and boundary cases.

## 恢复

```bash
git restore --source snapshot/legacy-import-20260714 -- prototype/prototype
git restore --source 32d1b7b -- 03-ui-prototype/prototype
```
