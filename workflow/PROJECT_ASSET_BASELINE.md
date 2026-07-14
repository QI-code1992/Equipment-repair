# Project Asset Baseline

- Audit date: 2026-07-14
- Workspace: `/Users/qiqi/Documents/Equipment repair `
- Workflow: `formal-software-delivery-workflow`
- Audit conclusion: inherited prototype/design package; not yet a controlled development baseline
- Current formal state: `PRODUCT_CLARIFICATION_REQUIRED`

## Post-migration update (2026-07-14)

The original package is now recoverable from `snapshot/legacy-import-20260714`. Current canonical candidates are under `00-opportunity/` through `08-release-handoff/`; the migrated prototype is `03-ui-prototype/prototype/`; the Stage 1 four-file package is under `01-requirements/`. Historical overlay files and duplicate PDFs were removed from the effective workspace after their contents were incorporated or classified, not erased from Git history.

## 1. Executive assessment

The workspace contains substantial product material: a historical full PRD and SPEC, later current-rule overlays, business and function diagrams, a multi-page static prototype, an AI integration SPEC, implementation plans, and nine static Node checks. It does not contain production application source, dependency/build manifests, database/API implementation, CI/CD, deployment assets, Git history, formal acceptance evidence, or release artifacts.

The most recent documents define a credible candidate scope, but the canonical baseline is fragmented. The files named as “current” override parts of the full PRD/SPEC instead of replacing them, so no single internally consistent PRD/SPEC pair exists. Formal development is therefore blocked at Stage 1.

## 2. Asset inventory and formal classification

| Current asset | Formal stage | Assessment | Intended canonical destination after Git baseline |
|---|---:|---|---|
| `docs/开发交付入口.md` | 1 | Current scope and precedence overlay; candidate baseline input | `01-requirements/PRD.md` input, then retire as standalone authority |
| `docs/PRD-当前有效版.md` | 1 | Current rules overlay, not a complete PRD | Merge into `01-requirements/PRD.md` |
| `docs/今日对接结论.md` | 1 | Decision notes; current input but not a formal approval ledger | Merge decisions into canonical artifacts and record future decisions in workflow ledgers |
| `docs/开发基线说明.md` | 1 | Baseline conflict guide; correctly blocks development | Use during reconciliation, then keep only if still needed as explanatory evidence |
| `prd/*-PRD.md` | 1 | Full PRD draft v1.3; contains retired rules | Reconcile in place as `01-requirements/PRD.md` |
| `prd/*-PRD.docx` | 1 | Older PRD export (shows v1.1); not canonical | Regenerate from approved canonical PRD only if DOCX is required |
| `prd/*-SPEC.md` | 1 | SPEC v1.0 initial draft based on older PRD; contains retired rules | Reconcile as `01-requirements/SPEC.md` |
| `prd/*-SPEC.docx` | 1 | Export of initial SPEC draft; not canonical | Regenerate from approved canonical SPEC only if DOCX is required |
| `diagrams/*业务流程图*` | 2 | Historical business-flow source in JSON/XMind | Reconcile as `02-product-interaction-design/BUSINESS_FLOW.md` plus rendered evidence |
| `diagrams/*系统功能图*` | 2 | Historical function map in JSON/XMind | Reconcile into page/function matrix and rendered evidence |
| `prototype/运维Agent-产品原型方案.md` | 2 | Detailed Agent interaction and AC source; some permission language is historical | Reconcile into interaction spec and acceptance criteria |
| `prototype/prototype/` | 3 | Runnable static prototype; useful visual/interaction evidence, not production code | Preserve source; create prototype baseline and checkpoint ledger before further UI changes |
| `prototype/*handoff*.md` | 3 | Historical handoff notes dated 2026-06-30/07-01 | Evidence only; not current baseline |
| both `*产品设计方案-v2.1.pdf` files | 2/3 | Byte-identical historical PDF; one filename is mojibake | Keep one traceable copy after Git snapshot and user-approved cleanup |
| `docs/engineering/AI_RAGFLOW_LANGGRAPH_SPEC.md` | 4 | Strong partial technical SPEC for the AI boundary; not a complete system architecture | Input to Stage 4 architecture/API/data documents after Stage 1–3 approval |
| `docs/superpowers/plans/*` | 4 | Two current-looking implementation plans and one explicitly historical plan | Reconcile and replace with one approved `04-architecture-plan/IMPLEMENTATION_PLAN.md` |
| `tests/*.test.js` | 3/6 | Nine static prototype checks; eight pass, one conflicts with current rules | Keep as prototype regression evidence; production test package is still missing |
| `README.md`, `docs/运行说明.md`, `prototype/prototype/README.md` | cross-stage | Entry documents disagree and contain broken paths/references | Replace with one root entrypoint after directory migration |
| `.superpowers/brainstorm/` | working data | Local brainstorming/server state, not a formal product artifact | Exclude from version control unless a specific non-reproducible artifact is promoted |

## 3. Current baseline precedence

Until Stage 1 reconciliation is approved, use this order only for analysis, not as permission to develop:

1. `docs/开发交付入口.md`
2. `docs/PRD-当前有效版.md`
3. `docs/今日对接结论.md`
4. `docs/开发基线说明.md`
5. `docs/superpowers/specs/2026-07-13-health-score-and-permission-prototype-sync-design.md`
6. Historical full PRD/SPEC, diagrams, prototype, plans, and PDFs only where they do not conflict with items 1–5

This precedence is temporary. The formal target is one canonical file per artifact, updated in place and versioned through Git—not a permanent stack of override documents.

## 4. Confirmed conflicts and integrity issues

### Requirements conflicts

- Full PRD/SPEC use historical health-score bands (`85–100`, `70–84`, `50–69`, `0–49`); current rules require `100`, `80–99`, `60–79`, `40–59`, `0–39`.
- Full PRD/SPEC include data import as active scope; current scope explicitly excludes its menu, permissions, API, and development entry while retaining the old page only for traceability.
- Full PRD/SPEC use five legacy role concepts; current scope fixes four roles: system administrator, equipment administrator, repair worker, and production-line operator.
- Historical materials allow or imply broader data/indicator capabilities; current rules limit intelligent querying to 40 built-in metrics and allowed dimensions, with metric management read-only.
- The full PRD and SPEC still carry open matters that are partly superseded by later decisions and must be re-triaged.

### Document and runbook integrity

- Root `README.md` references three missing documents from the 2026-07-10 handoff package.
- Root `README.md` says to start `local-server-4209.js` from `prototype/prototype`, but the command is presented from an ambiguous root context.
- `docs/运行说明.md` instructs running a root-level server file and six test files that do not exist.
- `prototype/prototype/README.md` references `docs/...` as if the prototype directory were the project root; those paths do not exist relative to that location.
- The two v2.1 PDFs have the same SHA-256 (`7e0ac21f...e0df8b`); one duplicate has a garbled filename.
- macOS `.DS_Store` files and transient `.superpowers` server-state files are present and should be excluded from future version control.

### Verification status

- Runtime: Node.js `v26.5.0` detected.
- Prototype server: `prototype/prototype/local-server-4209.js` starts successfully.
- HTTP smoke check: `/pages/intelligent-config.html` and `/index.html` both returned HTTP 200.
- Static checks: 8 passed, 1 failed.
- Failing check: `tests/intelligent-config-metric-inline.test.js` expects editable/addable/deletable metrics (`新增指标`, switches, delete actions), which contradicts the current read-only metric baseline. Treat the test as stale until Stage 1 reconciliation confirms the rule.
- No dependency manifest or test runner configuration exists; tests are standalone Node scripts.

## 5. Stage-Gate completeness

| Stage | Evidence found | Gate status |
|---|---|---|
| 0 Opportunity | No formal opportunity, competitor, feasibility, or MVP validation artifacts | Not evidenced; owner confirmation or scoped waiver required |
| 1 Requirements | Multiple drafts and current overlays; no standalone complete AC or traceability matrix | Blocked by baseline conflicts |
| 2 Product/interaction | Historical diagrams and Agent interaction design | Candidate inputs only; not approved |
| 3 UI/prototype | Runnable multi-page static prototype | Candidate input only; no prototype baseline/checkpoint ledger or approval |
| 4 Architecture/plan | AI partial SPEC and implementation plans | Incomplete system-wide package; not approved |
| 5 Development | Static prototype JavaScript only | Production development not started |
| 6 Testing | Static prototype checks only | No formal test plan/cases/report; 1 current check failing |
| 7 Acceptance | None | Not started |
| 8 Release/handoff | Prototype run notes only | No production runbook, deployment, rollback, or release package |

## 6. Safe migration sequence

1. Establish a recoverable Git baseline with an intentional `.gitignore`; record the initial Commit SHA before moving files.
2. Resolve CR-001 and create the canonical Stage 1 package: PRD, SPEC, acceptance criteria, and requirements traceability matrix.
3. Record explicit Stage 1 approval and create an immutable milestone tag; do not move to Stage 2 before this gate.
4. Reconcile diagrams, page/function coverage, interaction states, and prototype against the approved requirements.
5. Create `03-ui-prototype/PROTOTYPE_BASELINE.md` and `PROTOTYPE_CHECKPOINTS.md`; protect stable screens before further prototype edits.
6. Complete the system-wide architecture, data model, APIs, ADRs, and one implementation plan; record Stage 4 approval.
7. Begin production implementation on a development branch using feature/page checkpoints with reachable remote commits.
8. Bind testing, acceptance, and release to exact Commit SHAs and milestone tags.

## 7. Actions deliberately not taken during audit

- No existing files were moved, renamed, deleted, or rewritten.
- No historical duplicate was removed.
- Git was not initialized and no remote repository was created.
- No stage was self-approved.
- No prototype or test failure was “fixed” by changing requirements.

These actions require a recoverable version baseline and, where they affect formal baselines, explicit user approval.
