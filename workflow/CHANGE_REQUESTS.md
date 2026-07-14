# Change Requests

This is the continuous change ledger for the project. Existing history must not be deleted; closed items should remain traceable.

## Open

### CR-001: Reconcile the canonical requirements baseline

- Level: L2
- Status: Needs Clarification
- Raised By: formal workflow takeover audit
- Raised At: 2026-07-14
- Current Stage: Stage 1 — Requirements Definition
- Original Request: Inventory the current project assets and prepare the project for formal software delivery and version management.
- Clarified Requirement: Consolidate the current-rule overlays and the full historical PRD/SPEC into one internally consistent PRD, SPEC, acceptance-criteria set, and traceability matrix before development.
- Reason: The full PRD/SPEC still contain retired health-score bands, data-import scope, and legacy roles, while newer overlay documents supersede those rules.
- Impact:
  - PRD: full canonical document required
  - SPEC: full canonical document required
  - Prototype: stale navigation, copy, roles, and examples require traceable reconciliation
  - Architecture: must reference the approved product baseline
  - Implementation Plan: existing plans cannot be promoted until baseline reconciliation
  - Test Cases: one current static test conflicts with the read-only metric baseline; documented test commands also reference missing files
  - Acceptance Criteria: standalone complete artifact is missing
- Decision: Pending project-owner clarification and approval
- Updated Baselines: none
- Implementation:
  - Commit: unavailable; workspace is not a Git repository
  - Owner: unassigned
- Verification:
  - Status: Blocked pending requirements baseline
  - Evidence: `workflow/PROJECT_ASSET_BASELINE.md`

## Closed

None.
