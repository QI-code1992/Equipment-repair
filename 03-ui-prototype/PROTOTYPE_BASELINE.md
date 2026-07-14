# Prototype Baseline

- Baseline: Candidate v1.0
- Status: Awaiting Stage 3 approval
- Source: `03-ui-prototype/prototype/`
- Imported source commit: `c544c2d` (original snapshot); migration commit: `32d1b7b`

## Included

Login, workbench, BI, factory model, equipment ledger/add/edit/detail, fault report, Agent report, maintenance records, repair execution, system management and intelligent configuration. The prototype is static HTML/CSS/JavaScript and includes a local Node server and static rule checks.

## Constraints

- It is design/reference evidence, not a production service.
- Static numbers, old labels and historical data-import navigation must not override Stage 1.
- `assets/health-score-service.js` is an adapter shape only; production health calculation belongs to the backend service.
- P0 state coverage still needs verification for loading, empty, error, disabled, permission and boundary cases.

## Restore

```bash
git restore --source snapshot/legacy-import-20260714 -- prototype/prototype
git restore --source 32d1b7b -- 03-ui-prototype/prototype
```
