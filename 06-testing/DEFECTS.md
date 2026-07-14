# Defects

### DEF-001: Legacy metric static test conflicts with current requirement

- Severity: Major baseline inconsistency
- Status: Open / Stage 1 reconciliation
- Evidence: imported `tests/intelligent-config-metric-inline.test.js`
- Expected current behavior: fixed metric catalog is readonly.
- Required action: update the test after Stage 1 approval, then rerun all checks.

### DEF-002: Prototype runbook paths were stale before migration

- Severity: Moderate documentation defect
- Status: Candidate migration repair
- Evidence: original README and run notes referenced missing files/root server paths.
- Required action: update root entry and verify migrated server path.
