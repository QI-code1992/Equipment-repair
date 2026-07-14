# 变更请求台账

本文件是项目持续变更台账。已有历史不得删除，已关闭事项必须保持可追溯。

字段说明：`Level` 为变更级别，`Status` 为变更状态，`Raised By` 为提出人，`Raised At` 为提出时间，`Scope/Impact` 为影响范围，`Verification` 为验证结果。历史条目保留原始英文字段以维持追溯；新条目优先使用中文。

## 进行中

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

## 已关闭

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

### CR-006: Implement approved business notification panel

- Level: L2
- Status: Implemented / awaiting Stage 2 review
- Raised By: project owner
- Raised At: 2026-07-14
- Scope: SVG bell trigger, unread badge, all/unread tabs, in-panel business notifications, read-all, detail target and load-more simulation.
- Exclusions: no system notifications, independent notification page, deletion, mute, sound, vibration or browser push.
- Verification: 11/11 static checks, JavaScript syntax checks and `git diff --check` passed.

### CR-007: Incorporate external development and AI integration baseline

- Level: L2
- Status: Implemented / awaiting Stage 1 and Stage 4 review
- Raised By: project owner
- Raised At: 2026-07-14
- Scope: merge four external documents into canonical requirements, architecture, testing and release artifacts; register source hashes and prohibit parallel external baselines.
- Key impacts: health-score and SLA rules are reaffirmed; Python 3.13/FastAPI, PostgreSQL, MinIO/S3, Redis, independent RAGFlow, LangGraph threads/checkpoints/SSE, closed tool allowlist, citation lifecycle, security redaction and AI acceptance gates are now required.
- Evidence: `workflow/EXTERNAL_BASELINE_INPUTS.md`, `04-architecture-plan/AI_RAGFLOW_LANGGRAPH_SPEC.md`.

### CR-008: Promote notification entry to all page shells

- Level: L1
- Status: Implemented
- Raised By: project owner
- Scope: inject the approved SVG bell, unread badge and notification panel into every page containing a topbar; keep one consistent behavior instead of workbench-only behavior.
- Verification: 11/11 static checks and JavaScript syntax check passed.

### CR-009: Remove obsolete topbar refresh actions

- Level: L1
- Status: Implemented
- Raised By: project owner
- Scope: remove the `刷` refresh buttons from BI, equipment ledger and equipment detail topbars; retain global notification and user entry actions.
- Verification: 11/11 static checks and JavaScript syntax check passed.

### CR-010: Complete logout delivery flow

- Level: L1
- Status: Implemented
- Raised By: project owner
- Scope: after logout confirmation, return to `login.html`; preserve cancel behavior and close the user menu.
- Verification: static test, JavaScript syntax check and `git diff --check` passed.

### CR-011: Modal notification panel scroll and page-lock behavior

- Level: L1
- Status: Implemented
- Raised By: project owner
- Scope: add notification scrim, lock main-page scrolling while open, preserve independent notification-list scrolling and in-panel loading.
- Verification: static tests, JavaScript syntax check and `git diff --check` passed.

### CR-012: Unread-only red notification marker

- Level: L1
- Status: Implemented
- Raised By: project owner
- Scope: show a red dot only for unread notifications; read notifications have no left marker. Type colors remain on labels.
- Verification: static tests, JavaScript syntax check and `git diff --check` passed.

### CR-013: Remove workbench AI status card

- Level: L1
- Status: Implemented
- Raised By: project owner
- Scope: remove the red-boxed “AI诊断在线” sidebar card from the workbench; retain navigation and main content.
- Verification: static checks and `git diff --check` passed.

### CR-014: Remove sidebar explanation cards globally

- Level: L1
- Status: Implemented
- Raised By: project owner
- Scope: hide the shared `.sidebar-foot` explanation card on every prototype page, including page-specific variants.
- Verification: static checks and `git diff --check` passed.

### CR-015: Establish Chinese-first stage artifact language convention

- Level: L1
- Status: Implemented
- Raised By: project owner
- Scope: Chinese by default for stage artifact content and newly created document filenames; preserve English for code, identifiers, logs, API/protocol/library names and compatibility-sensitive existing paths.
- Governance source: `/Users/qiqi/.codex/skills/formal-software-delivery-workflow/SKILL.md`.
- Boundary: no mass rename of existing English files in this change; any batch rename requires explicit reference migration and change control.

### CR-016: 中文化 Stage 1 需求文档

- Level: L1
- Status: Implemented / partial batch
- Raised By: project owner
- Scope: translate Stage 1 PRD/SPEC/验收标准/需求追踪矩阵的标题、元数据、表头、章节说明和规则性文字；保留 `FR/NFR/AC/TC`、API、字段名、状态枚举和技术产品名。
- Boundary: existing English filenames remain unchanged to preserve references; remaining Given/When/Then acceptance sentences and later-stage documents are queued for subsequent batches.

### CR-017: 中文化 Stage 2–3 设计与原型文档

- Level: L1
- Status: Implemented / partial batch
- Raised By: project owner
- Scope: translate Stage 2 interaction/design and Stage 3 prototype document titles, metadata, table headers and explanatory text; preserve technical identifiers, routes, states and file paths.
- Boundary: existing English filenames remain unchanged; architecture, development, testing, acceptance and release documents remain for the next batch.

### CR-018: 中文化 Stage 4–8 架构、开发、测试、验收和交付文档

- Level: L1
- Status: Implemented / partial batch
- Raised By: project owner
- Scope: translate Stage 4–8 document titles, metadata, explanatory text, table headers and delivery statements; preserve technical identifiers, API routes, commands, states and Commit SHA.
- Boundary: existing English filenames remain unchanged; code, tests, logs, variables and technical identifiers retain English where required.

### CR-019: 中文化跨阶段入口与交接说明

- Level: L1
- Status: Implemented
- Raised By: project owner
- Scope: translate README and workflow entry/handoff/approval headings while preserving commands, paths, identifiers and technical terms.

### CR-020：中文化变更请求台账

- 级别：L1
- 状态：已实施
- 提出人：项目负责人
- 范围：将变更台账标题、说明和字段约定改为中文；历史条目保留原始字段以保证追溯。
- 边界：`CR-xxx`、Commit、路径、技术标识和历史原文不翻译。

### CR-021：创建项目文档与原型交接版本

- 级别：L1
- 状态：已实施 / 候选交接快照
- 提出人：项目负责人
- 范围：将当前阶段文档、工作流台账、静态原型和原型回归检查打包为 `handoff/candidate-v20260714-01`，推送至 GitHub 供同事拉取。
- 边界：该标签不是生产发布，不代表 Stage Gate 审批通过；后续开发应从新分支继续，禁止移动标签。
- 验证：静态测试、JavaScript 语法检查、`jq` 状态文件检查和 `git diff --check`。
