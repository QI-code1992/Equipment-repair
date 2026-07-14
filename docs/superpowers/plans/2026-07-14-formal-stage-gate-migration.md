# Formal Stage-Gate Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the imported prototype package into a single, traceable Stage 0–8 candidate delivery workspace while preserving the original snapshot in GitHub.

**Architecture:** Canonical artifacts live in numbered stage folders; `workflow/` holds only cross-stage state, approvals, changes, and handoffs. The existing static prototype remains executable under Stage 3, while Stage 5–8 documents describe actual status and never invent production evidence.

**Tech Stack:** Markdown, JSON, static HTML/CSS/JavaScript, Node.js 26.x standalone checks, Git/GitHub.

## Global Constraints

- Requirements authority is the approved precedence in `docs/superpowers/specs/2026-07-14-formal-stage-gate-migration-design.md`.
- Health score uses 100/80–99/60–79/40–59/0–39 bands and starts at 100 on formal launch without pre-launch backfill.
- Intelligent querying uses 40 built-in metrics and allowed dimensions; metric management is read-only.
- Data import is excluded from the current release scope; its historical page remains traceable only in the import tag.
- No stage is marked Approved without explicit user approval recorded in `workflow/STAGE_APPROVALS.md`.
- No production implementation, test result, acceptance verdict, or release readiness may be fabricated.

---

### Task 1: Create canonical stage directories and migrate source assets

**Files:**
- Create: `00-opportunity/`, `01-requirements/`, `02-product-interaction-design/`, `03-ui-prototype/`, `04-architecture-plan/`, `05-development/`, `06-testing/`, `07-acceptance/`, `08-release-handoff/`
- Move: current stage documents and prototype assets according to the approved migration design
- Modify: root `README.md`, `workflow/PROJECT_ASSET_BASELINE.md`, `workflow/state.json`

- [ ] Create directories and move each asset exactly once.
- [ ] Preserve the original names only inside the original Git snapshot; do not create local `_old`, `v1`, `backup`, or `final2` copies.
- [ ] Update all current references to the new canonical paths.
- [ ] Run `git diff --check` and the prototype HTTP smoke check.
- [ ] Commit: `chore: organize formal stage workspace`.

### Task 2: Produce the Stage 0 opportunity package

**Files:**
- Create: `00-opportunity/OPPORTUNITY.md`
- Create: `00-opportunity/COMPETITOR_ANALYSIS.md`
- Create: `00-opportunity/FEASIBILITY.md`

- [ ] Separate evidence-backed conclusions from open validation questions.
- [ ] Record target users, business pain, value hypothesis, substitutes, technical feasibility, risks, and MVP validation.
- [ ] Mark the stage as `Candidate / Awaiting user confirmation`; do not self-approve Stage 0.
- [ ] Commit: `docs: add opportunity candidate package`.

### Task 3: Produce the Stage 1 requirements package

**Files:**
- Create: `01-requirements/PRD.md`
- Create: `01-requirements/SPEC.md`
- Create: `01-requirements/ACCEPTANCE_CRITERIA.md`
- Create: `01-requirements/REQUIREMENTS_TRACEABILITY_MATRIX.md`

- [ ] Merge the current-rule overlays and non-conflicting historical requirements into one PRD.
- [ ] Translate approved behavior into roles, permissions, pages, states, fields, validation, APIs, audit, NFRs, and AC mappings in SPEC.
- [ ] Write Given/When/Then AC covering happy, empty, loading, error, permission, boundary, and repeated-operation cases.
- [ ] Assign stable IDs (`FR-*`, `NFR-*`, `AC-*`) and close every traceability row.
- [ ] Mark all four artifacts `Candidate v1.0`, `Awaiting Stage 1 user approval`.
- [ ] Commit: `docs: establish Stage 1 requirements candidate`.

### Task 4: Produce Stage 2 interaction and Stage 3 prototype baselines

**Files:**
- Create: `02-product-interaction-design/BUSINESS_FLOW.md`
- Create: `02-product-interaction-design/USER_FLOW.md`
- Create: `02-product-interaction-design/PAGE_FUNCTION_MATRIX.md`
- Create: `02-product-interaction-design/INTERACTION_SPEC.md`
- Create: `02-product-interaction-design/PROTOTYPE_COVERAGE.md`
- Create: `03-ui-prototype/VISUAL_GUIDELINES.md`
- Create: `03-ui-prototype/DESIGN_TOKENS.json`
- Create: `03-ui-prototype/COMPONENT_SPEC.md`
- Create: `03-ui-prototype/PROTOTYPE_BASELINE.md`
- Create: `03-ui-prototype/PROTOTYPE_CHECKPOINTS.md`
- Create: `03-ui-prototype/INTERACTION_COVERAGE.md`

- [ ] Extract current pages, roles, navigation, statuses, exceptions, and state coverage from the prototype.
- [ ] Mark data-import page as historical/excluded in current coverage.
- [ ] Record visual tokens/components and prototype limitations without claiming unverified states.
- [ ] Record at least one recovery checkpoint for the imported prototype candidate with source commit and restore command.
- [ ] Commit: `docs: add interaction and prototype candidate baselines`.

### Task 5: Produce Stage 4 architecture and development plan

**Files:**
- Create: `04-architecture-plan/SYSTEM_ARCHITECTURE.md`
- Create: `04-architecture-plan/API_SPEC.md`
- Create: `04-architecture-plan/DATA_MODEL.md`
- Create: `04-architecture-plan/IMPLEMENTATION_PLAN.md`
- Create: `04-architecture-plan/ADR/ADR-001-boundary-and-source-of-truth.md`

- [ ] Consolidate software system, LangGraph, and RAGFlow boundaries.
- [ ] Define data flow, trust boundaries, API contracts, data objects, audit requirements, deployment constraints, and decision gates.
- [ ] Keep unresolved production technology choices explicit as decisions required before development.
- [ ] Commit: `docs: add architecture and development plan candidate`.

### Task 6: Produce Stage 5–8 operational documents

**Files:**
- Create/update: `05-development/DEV_NOTES.md`, `SELF_TEST.md`, `CODE_REVIEW.md`, `COMMIT_LOG.md`, `CHECKPOINTS.md`
- Create/update: `06-testing/TEST_PLAN.md`, `TEST_CASES.md`, `TEST_REPORT.md`, `DEFECTS.md`, `REGRESSION_REPORT.md`
- Create/update: `07-acceptance/ACCEPTANCE_REPORT.md`, `ACCEPTANCE_EVIDENCE.md`
- Create/update: `08-release-handoff/RUNBOOK.md`, `DEPLOYMENT_CHECKLIST.md`, `ROLLBACK_PLAN.md`, `RELEASE_NOTES.md`, `HANDOFF.md`

- [ ] Record prototype-only status separately from production implementation status.
- [ ] Record existing static test execution honestly, including the known metric-management conflict.
- [ ] Keep acceptance `BLOCKED` until an exact approved production Commit SHA exists.
- [ ] Keep release `Not Ready` until deployment and rollback evidence exists.
- [ ] Commit: `docs: add development testing acceptance and release records`.

### Task 7: Verify, update ledgers, and publish

**Files:**
- Modify: `workflow/state.json`, `workflow/STAGE_APPROVALS.md`, `workflow/CHANGE_REQUESTS.md`, `workflow/PM_TO_DEV_HANDOFF.md`, `workflow/DEV_TO_PM_HANDOFF.md`

- [ ] Run JSON, Markdown, path, traceability, stale-rule, prototype HTTP, and Node static checks.
- [ ] Update state with exact candidate Commit SHA and verification results.
- [ ] Keep stage approvals pending; do not create baseline tags.
- [ ] Push branch and open/update a draft PR against `main`.
- [ ] Commit: `chore: verify formal workspace candidate`.

## Self-review checklist

- Scope covered: Stage 0–8 candidate outputs, Stage 1 four required artifacts, original snapshot, GitHub branch/tag, and verification.
- No production implementation is implied by the plan.
- No stage approval is implied by the plan.
- No local historical duplicate is required.
- Any missing source evidence remains explicitly marked as open or blocked.
