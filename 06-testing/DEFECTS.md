# Defects

### DEF-001: Legacy metric static test conflicted with current requirement

- Severity: Major baseline inconsistency
- Status: Resolved in candidate verification; production behavior still unverified
- Evidence: imported `tests/intelligent-config-metric-inline.test.js`
- Expected current behavior: fixed metric catalog is readonly.
- Resolution: test now checks the visible readonly metric modal and the complete static suite passes; production metric API remains unimplemented.

### DEF-002: Prototype runbook paths were stale before migration

- Severity: Moderate documentation defect
- Status: Candidate migration repair
- Evidence: original README and run notes referenced missing files/root server paths.
- Required action: update root entry and verify migrated server path.
