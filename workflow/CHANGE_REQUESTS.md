# Change Requests

This is the continuous change ledger for the project. Existing history must not be deleted; closed items should remain traceable.

## Open

### CR-001: Reconcile the canonical requirements baseline

- Level: L2
- Status: Approved
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
- Decision: User approved the snapshot-first formalization design on 2026-07-14. Proceed with canonical Stage 1 consolidation and candidate Stage 0–8 documentation; no stage transition is approved by this decision.
- Updated Baselines: none
- Implementation:
  - Commit: candidate changes are distributed across `08e9e13`, `f162333`, `468941c`, and `4e955b4`; verification correction pending
  - Owner: unassigned
- Verification:
  - Status: Candidate package verified; Stage 1 approval still pending
  - Evidence: `workflow/PROJECT_ASSET_BASELINE.md`

## Closed

### CR-002: Remove out-of-scope and transient workspace assets

- Level: L2
- Status: Approved
- Raised By: project owner
- Raised At: 2026-07-14
- Current Stage: Stage 3 candidate prototype
- Original Request: Delete files and folders that are not needed.
- Clarified Requirement: Remove transient metadata, the unused 4208 server and icon-option exploratory page, and the current migrated data-import page/artifact; retain all formal artifacts, evidence ledgers, current prototype pages, and the original Git snapshot.
- Reason: These assets are not part of the current effective product scope or are reproducible local noise.
- Impact:
  - PRD: none; data import remains explicitly out of scope
  - SPEC: none
  - Prototype: remove current data-import page and unused exploratory/server files
  - Architecture: none
  - Implementation Plan: none
  - Test Cases: none
  - Acceptance Criteria: none
- Decision: Approved by the project owner in the deletion request; history remains recoverable from `snapshot/legacy-import-20260714`.
- Updated Baselines: `03-ui-prototype/PROTOTYPE_BASELINE.md`, `02-product-interaction-design/PAGE_FUNCTION_MATRIX.md` remain consistent with data-import exclusion.
- Implementation:
  - Commit: `5d9b3c4`
  - Owner: workflow orchestrator
- Verification:
  - Status: Verified
  - Evidence: no stale references; 9/9 static checks; prototype index/config HTTP 200; deleted data-import HTTP 404; `git diff --check` passed

### CR-003: Remove completed process-only documentation directory

- Level: L1
- Status: Approved
- Raised By: project owner
- Raised At: 2026-07-14
- Current Stage: Cross-stage workspace hygiene
- Original Request: Keep only formal Stage directories.
- Clarified Requirement: Remove `docs/superpowers/` after its migration design and execution plan have been completed; retain formal stage artifacts, `workflow/`, source prototype, and Stage 6 tests under `06-testing/tests/`.
- Reason: The directory contains process-session design/plan files, not current product or stage deliverables.
- Impact:
  - PRD: source references updated to workflow ledgers
  - SPEC: none
  - Prototype: none
  - Architecture: none
  - Implementation Plan: formal candidate remains at `04-architecture-plan/IMPLEMENTATION_PLAN.md`
  - Test Cases: none
  - Acceptance Criteria: none
- Decision: Approved by the project owner in the cleanup request; deleted files remain recoverable through Git history.
- Updated Baselines: `01-requirements/PRD.md`, root `README.md`
- Implementation:
  - Commit: `062b4f1`
  - Owner: workflow orchestrator
- Verification:
  - Status: Verified
  - Evidence: `docs/superpowers/` and its untracked copy removed; 9/9 static checks; JSON/JavaScript checks; `git diff --check` passed

### CR-004: Reconcile documents to unfinished prototype baseline

- Level: L2
- Status: In review
- Raised By: project owner
- Raised At: 2026-07-14
- Scope: add factory modeling and Agent report pages; expand intelligent configuration; add AI report duration gate and work-order display-state mapping.
- Impacted artifacts: `01-requirements/PRD.md`, `01-requirements/SPEC.md`, `02-product-interaction-design/PAGE_FUNCTION_MATRIX.md`, `03-ui-prototype/PROTOTYPE_AUDIT.md`.
- Boundary: prototype remains unfinished; stale data-import strings are recorded as follow-up cleanup and do not restore the excluded feature.

### CR-005: Implement approved user entry and scoped user-management prototype

- Level: L2
- Status: Implemented / awaiting Stage 2 review
- Raised By: project owner
- Raised At: 2026-07-14
- Scope: implement the approved user capsule menu, profile/security modals, permission-scoped management entry, self-only user view, and `user_management.view_all` permission marker.
- Implementation: commit `aa8a307`.
- Verification: 10/10 static checks, JavaScript syntax checks, HTTP 200 smoke checks, and `git diff --check` passed.
- Boundary: static prototype behavior only; no real authentication or server-side authorization is claimed.
