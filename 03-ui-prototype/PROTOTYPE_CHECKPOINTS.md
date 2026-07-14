# Prototype/Page Checkpoints

## PCP-001: Imported multi-page prototype

- Status: Candidate / awaiting Stage 3 approval
- Scope: imported static pages, shared assets, Agent drawer and health-score adapter
- Related baseline: Stage 1 candidate PRD/SPEC; Stage 2 candidate page matrix
- Source: `03-ui-prototype/prototype/`
- Commit SHA: `32d1b7b`
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
