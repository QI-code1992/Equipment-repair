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

- 2026-07-15 复发处理：后续设计技能再次按历史默认路径创建了 `docs/superpowers/specs/2026-07-14-start-repair-agent-design.md`。该内容已被当前 PRD、SPEC、交互规格、Stage 3 原型及 Stage 4 架构基线吸收，项目负责人再次确认删除；Git 提交 `209bb3c` 保留原文恢复点，清理提交为 `abf9787c15db91f9e1b7cf9e130330c5861cad9b`。全局 `formal-software-delivery-workflow` 已新增约束，禁止正式阶段文档散落到通用 `docs/`。

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

### CR-022：明确驾驶舱 BI 与工作台的页面分工

- 级别：L1
- 状态：已确认 / 待原型实现
- 提出人：项目负责人
- 范围：驾驶舱 BI 面向管理层，聚焦管理摘要、趋势、效率、排行和历史分析；工作台聚焦当前风险、待办、超时提醒和快速处置。
- 设计基线：`02-product-interaction-design/驾驶舱BI设计细化.md`，采用单页纵向分析结构。
- 边界：本次仅确认信息架构和交互边界，尚未修改原型代码；原型实现需在该设计基线获得确认后进行。
### CR-022：GitHub 作为后续项目产物的强制远程基线

- 级别：L3
- 状态：已批准
- 提出人：项目负责人
- 提出时间：2026-07-14
- 当前阶段：Stage 3 — UI 与高保真原型
- 原始请求：后续本项目产生的任何产物都按照 `formal-software-delivery-workflow` 流程要求上传至 GitHub。
- 明确要求：`https://github.com/QI-code1992/Equipment-repair` 是本项目唯一的远程交付与可追溯基线。所有后续正式阶段产物、工作流台账、原型或功能检查点、测试与验收证据、交接材料，必须先提交并推送到该仓库；在审批、检查点或交接记录中写明精确 Commit SHA 后，才可报告该项完成。
- 影响：
  - PRD / SPEC / 原型 / 架构 / 测试 / 验收 / 发布交接：每次正式基线或阶段产物更新均需 Git 提交和远程推送。
  - 原型检查点：必须在 `03-ui-prototype/PROTOTYPE_CHECKPOINTS.md` 记录可恢复的 Commit SHA 与证据路径。
  - 开发检查点：必须在远程开发分支保留对应 Commit，并在 `05-development/CHECKPOINTS.md` 记录。
  - 阶段审批：必须引用已推送的 Commit SHA；重要门禁通过后创建不可移动的 GitHub 里程碑标签。
  - 本地工作区：仅保留当前有效文件和必要证据，不以本地副本作为历史归档。
- 决定：项目负责人已明确批准；即刻生效。
- 更新基线：`workflow/state.json`、本变更台账，以及后续所有阶段产物与交付记录。
- 实施：由工作流协调者执行提交、推送、检查点与标签记录。
- 验证：规则与工作流文件已提交并推送至 `origin/main`；Commit SHA：`919788e50175bf13bc8472ec7053385289acb051`。

### CR-023：融合外部工作台原型并隔离共享依赖

- 级别：L2
- 状态：已实施 / 等待 Stage 3 审批
- 提出人：项目负责人
- 提出时间：2026-07-14
- 当前阶段：Stage 3 — UI 与高保真原型
- 原始请求：将外部 ZIP 内的工作台页面融合到现有原型，页面和交互保持一致。
- 已批准范围：仅替换并适配工作台；其他页面不动。
- 影响：`03-ui-prototype/prototype/pages/workbench.html`、必要的工作台专用资源、工作台回归检查、`03-ui-prototype/PROTOTYPE_CHECKPOINTS.md`。
- 不影响：其他原型页面、共享 `app.js` / `app.css` / `global-agent.js` 的既有功能、全局 AI 助手、通知面板和导航。
- 决定：采用页面级移植与最小依赖适配；禁止整包覆盖输入 ZIP 的旧版共享资源。
- 设计基线：`03-ui-prototype/WORKBENCH_INTEGRATION_DESIGN.md`。
- 实施：已按 `03-ui-prototype/WORKBENCH_INTEGRATION_PLAN.md` 在 `feature/workbench-integration` 实现；工作台页面与专用静态检查已提交。
- 验证：Commit `4a5f302ffe42c972186426d5f8587cd8059adc6e` 已推送至 GitHub；工作台专用测试与现有 11 项静态回归共 12 项通过，`git diff --check` 通过；检查点见 `PCP-012`。

### CR-024：维修接单前故障诊断 Agent 原型基线

- 级别：L2
- 状态：Ready For Verification
- 提出人：项目负责人
- 提出时间：2026-07-14
- 当前阶段：Stage 1/2/3 候选基线整理
- 原始请求：将开始维修页接入智能配置中的故障诊断 Agent，实现预诊断、动态追问、历史案例与知识库依据、采纳后的结束维修预填和摘要。
- 明确需求：不同设备及不同故障必须由 Agent 根据故障上下文生成不同问题与问题建议；“有报警码”必须追问具体报码；证据不足不得生成根因采纳；直接开始维修不得保存 AI 内容；采纳后摘要应保留故障现象与关键诊断证据。
- 影响：PRD/SPEC/AC/追踪矩阵增量 v1.1；开始维修和结束维修交互、原型覆盖、原型静态测试；生产模型、历史工单、知识库、流式接口及预诊断缓存待 Stage 4 设计。
- 决策：用户授权完成文档基线、变更登记和原型检查点；本记录不构成 Stage Gate 批准。
- 实施：源代码版本 `fa8fa42ed64b1d892a701cea287f3ef69ce7a2c2`；候选基线文档提交 `25d4ba41e256b43c41fa707859801e7ea89ba3ed`。
- 验证：全部 `06-testing/tests/*.test.js` 静态检查通过；待提交后以精确 SHA 更新检查点。

- Stage 4 设计：已确认 `04-architecture-plan/维修故障诊断Agent架构设计.md` 的公网平台账号访问、本地结构化历史案例、本地 RAGFlow、受控外部 LLM API、授权隔离与降级边界；待实施计划审批。

### CR-026：Stage 4 平台级架构范围纠正与数据隔离取消

- 级别：L3
- 状态：已确认 / 已纳入获批 Stage 4 基线
- 提出人：项目负责人
- 提出时间：2026-07-14
- 当前阶段：Stage 4 — 架构与开发计划
- 原始请求：在制定 Stage 4 前先阅读整个项目的 PRD、SPEC、原型与交付材料；架构不能只覆盖维修故障诊断 Agent。
- 明确要求：覆盖完整智能运维平台；取消工厂/设备授权隔离机制；平台业务关系型数据库选用 PostgreSQL；部署在单台 Windows 主机的 Docker Desktop/WSL2 环境；保留本地 RAGFlow，并使用 Elasticsearch 8.11 作为其向量、全文与混合检索文档引擎。
- 原因：此前专项架构遗漏身份权限、组织设备、故障维修闭环、健康分与指标、工作台/BI、智能配置、通知审计、附件和平台运维等 P0 能力。
- 影响：PRD/SPEC 删除设备或工厂数据行级隔离规则，保留角色、菜单和操作权限；交互/原型清理“授权设备范围”“未授权设备隐藏”等文案；数据模型不使用 `EquipmentGrant`；API/测试移除设备/工厂过滤断言，保留账号、角色、操作权限、线程隔离和审计验证。
- 决定：项目负责人已确认上述范围与技术选型；待书面架构基线评审后编写详细实施计划。
- 更新基线：`04-architecture-plan/平台级架构设计.md`；`04-architecture-plan/维修故障诊断Agent架构设计.md`。
- 实施：架构文档已提交；生产实现进入 Stage 5。
- 验证：项目负责人已书面评审通过；Stage 5–6 继续验证对应实现。

### CR-027：四个 Agent 独立配置与真实深度思考执行

- 级别：L2
- 状态：已确认 / 已纳入获批 Stage 4 基线
- 提出人：项目负责人
- 提出时间：2026-07-15
- 当前阶段：Stage 4 — 架构与开发计划
- 原始请求：四个 Agent 必须按各自配置运行，不能被统一默认值强制设置为相同模型、流式、问题建议、引用、上下文轮数与深度思考等级；深度思考必须真实参与模型与工具执行，不能只作为页面配置。
- 决定：每个 `agent_id` 保存独立当前有效配置；页面加载不得覆盖所有 Agent。后端按 Agent 类型固化工作流与工具策略；运行保存配置快照但不提供 Agent 版本、发布或回滚能力。深度思考要求推理模型与真实“思考—行动—核验”图执行，只展示安全过程事件，不输出或保存原始思维链。
- 影响：`04-architecture-plan/平台级架构设计.md`；后续数据模型、API、配置中心、Agent 运行时、SSE 与测试契约。
- 验证：项目负责人已书面评审通过；Stage 5–6 验证独立配置、推理参数和安全过程事件。

### CR-028：RAGFlow 由开发工作实际部署与联调

- 级别：L2
- 状态：已确认 / 已纳入获批 Stage 4 基线
- 提出人：项目负责人
- 提出时间：2026-07-15
- 当前阶段：Stage 4 — 架构与开发计划
- 原始请求：RAGFlow 需要由开发负责下载、部署、调试并对接系统，而非假定已有可用服务。
- 决定：Stage 5 必须在单台 Windows 的 Docker Desktop/WSL2 中部署独立 RAGFlow + Elasticsearch 8.11 依赖栈，并真实验证文档生命周期、混合检索、引用、健康检查、超时降级、重启恢复和交付运行手册；禁止以 mock 或静态案例替代。
- 影响：平台级架构、系统架构、实施计划、Stage 5 部署与测试证据、Stage 8 运行手册。
- 验证：待 Stage 5 实际部署和 Stage 6 集成/恢复测试。

### CR-029：补齐 Stage 5 准入与编码约束材料

- 级别：L2
- 状态：Done
- 提出人：项目负责人
- 提出时间：2026-07-15
- 当前阶段：Stage 4 — 架构与开发计划
- 原始请求：补齐进入 Stage 5 前缺失的材料，由项目负责人决定是否进入 Stage 5。
- 影响：新增 `04-architecture-plan/AGENTS.md`；更新 `workflow/state.json` 与 `workflow/PM_TO_DEV_HANDOFF.md`，不改变产品需求、交互、原型、架构、API 或业务代码。
- 决策：项目负责人已审核编码约束并明确解除 `Hold-001`，允许进入 Stage 5。
- 验证：`workflow/state.json` 可解析；文档路径与 Stage 5 实施计划一致；不创建开发分支或生产代码。

### CR-030：已批准基线状态同步

- 级别：L0
- 状态：Done
- 提出人：项目负责人
- 提出时间：2026-07-15
- 当前阶段：Stage 5 — 开发实施
- 原始请求：同步 Stage 5 进入前的文档状态，消除已批准门禁与候选状态标记的冲突。
- 影响：仅更新 Stage 1 至 Stage 4 文档页首状态、原型检查点总状态与 PM→开发交接状态；不改变需求、交互、原型、架构、API 或代码内容。
- 验证：状态文件可解析；文档状态引用 Gate-002 至 Gate-006；`git diff --check` 通过。

### CR-031：Stage 5 双团队工作包划分

- 级别：L0
- 状态：Done
- 提出人：项目负责人
- 提出时间：2026-07-15
- 当前阶段：Stage 5 — 开发实施
- 原始请求：将项目文件中的 Stage 5 工作按功能关联性划分为两份，供团队并行开发。
- 决策：工作包 A 负责业务平台内核与事务事实；工作包 B 负责 AI、知识与交互；Task 1 为共同前置，按 FCP-001 解锁并行。
- 影响：新增团队分工文档，不改变产品、架构、API 或实现范围。
- 验证：工作包覆盖实施计划 Task 1 至 Task 10，且依赖与禁止交叉修改范围明确。

### CR-032：建立统一代码库目录并固定 Stage 3 原型归档边界

- 级别：L3
- 状态：Implemented / Verification constrained
- 提出人：项目负责人
- 提出时间：2026-07-15
- 当前阶段：Stage 5 — 开发实施；本变更返回 Stage 4 更新工程目录基线
- 原始请求：将 `backend/`、`frontend/`、`infra/` 和工程测试等非阶段工程文件统一归入“代码库”，并把该规则同步到 `formal-software-delivery-workflow` 技能。
- 明确要求：统一目录使用 `codebase/`；Stage 3 原型及原型专用资源继续位于 `03-ui-prototype/`，作为该阶段正式交付物，不进入或复制到 `codebase/`。
- 原因：区分阶段档案、跨阶段治理材料和长期演进的正式工程文件，避免原型与正式前端形成两个事实来源。
- 影响：
  - PRD / SPEC / Prototype：不改变产品范围、交互或原型内容；仅固定原型归档边界。
  - Architecture：新增 `04-architecture-plan/代码库目录归档设计.md`，更新工程目录和路径约束。
  - Implementation Plan / AGENTS：实施时更新所有 `backend/`、`frontend/`、`infra/` 路径。
  - Tests：服务测试随代码迁移；当前 Stage 3 原型静态检查继续保留在 `06-testing/tests/`。
  - Acceptance Criteria：不改变产品验收标准；增加目录与路径迁移验证。
  - Workflow Skill：书面设计复核后更新 `/Users/qiqi/.codex/skills/formal-software-delivery-workflow/SKILL.md` 及必要的工件目录参考。
- 决定：采用根级 `codebase/`；不采用把正式代码放进 `05-development/`，不创建 `codebase/prototype/`。
- 更新基线：`04-architecture-plan/代码库目录归档设计.md`；实施后更新受影响的 Stage 4—8 文档和工作流状态。
- 实施：项目负责人已复核并明确确认；`backend/`、`frontend/`、`infra/` 已迁移到 `codebase/`，Stage 3 原型保持原位；当前有效路径和正式工作流技能约束已同步，无旧目录兼容副本。迁移提交：`20fc10f9e0af3e420283814a3eb02ab744aaf869`。
- 验证：目录断言、原型静态回归 14/14、技能规则扫描和 `git diff --check` 通过。后端测试被迁移前已有的重复定义冲突阻断，记录为 `DEF-003`；当前环境缺少 Docker，Compose 未验证。待提交后回填精确 Commit SHA。

### CR-033：删除未跟踪的 `* 2.md` 重复副本

- 级别：L0
- 状态：Done
- 提出人：项目负责人
- 提出时间：2026-07-15
- 当前阶段：跨阶段工作区卫生清理
- 原始请求：删除工作区中 12 个文件名以 ` 2.md` 结尾的未跟踪副本。
- 核对结论：8 个副本与正式文件字节完全一致；4 个副本是 `DEV_NOTES.md`、`CHECKPOINTS.md`、`SELF_TEST.md`、`DEFECTS.md` 的较旧子集，没有独有的新内容。
- 决定：删除全部 12 个副本；保留不带 ` 2` 的当前正式文件作为唯一事实来源，历史由 Git 保留。
- 影响：不改变 PRD、SPEC、原型、架构、代码、测试契约或验收标准。
- 验证：删除后不得存在 `* 2.md`；正式对应文件必须全部存在；`git diff --check` 与原型静态回归必须通过。

### CR-034：补齐两人制 Stage 5 开发任务书

- 级别：L2
- 状态：Done / 任务书已批准
- 提出人：项目负责人
- 提出时间：2026-07-15
- 当前阶段：Stage 4 补充整改
- 原始请求：继续完成 Stage 5 正式准入所需的下一步。
- 人员确认：Stage 5 共 2 名开发人员；`DEV-001` 负责最终集成且具备 Docker/Compose 校验环境；`DEV-002` 不具备 Docker 环境。
- 决定：创建 `04-architecture-plan/DEVELOPMENT_TASK_BOOK.md` 候选 v1.0；DEV-001 负责平台事实、基础设施、容器验证和最终集成，DEV-002 负责 AI、知识适配与正式前端；所有容器相关证据必须由 DEV-001 提供。
- 候选提交：`8272a8ed161b787098660f61ebb86fa5ccada564`。
- 审批记录提交：`20261a80f01de8d18e18a2acf9c97e07087e04bc`。
- 审批证据：项目负责人于 2026-07-15 明确回复“批准任务书”，批准候选提交对应的任务书 v1.0 及两人制任务分配。
- 影响：补齐 Stage 4 开发任务分配与集成基线，不改变 PRD、SPEC、AC、原型、架构/API/数据契约或产品范围。
- 审批边界：任务书已获书面批准，但不构成更新后的 Stage 4 → Stage 5 门禁批准，也不单独授权 TASK-001；其余准入阻塞关闭后仍须绑定精确 Commit SHA 重新批准门禁。
- 验证：检查人员数量、任务 ID、追踪关系、负责人、依赖、共享契约、Docker 边界、验证命令、集成顺序和回滚策略均无缺项。

### CR-035：纠正 TASK-001 与 Stage 5 门禁顺序

- 级别：L2
- 状态：Done / Gate-007 approved
- 提出人：项目负责人
- 提出时间：2026-07-15
- 当前阶段：Stage 4 补充整改
- 原始请求：确认 TASK-001 应在 Stage 4 → Stage 5 门禁批准后执行，并指令继续修订。
- 原因：任务书 v1.0 同时把 TASK-001 定义为 Stage 5 开发任务和门禁前置修复，形成循环依赖并违反 Stage-Gate 顺序。
- 决定：TASK-001 改为门禁后的首个阻塞任务；`DEF-003`、`DEF-004` 作为 Stage 5 已知风险，由 DEV-001 在 TASK-001 中修复和真实验证；门禁前不得修改相关代码或 Compose 配置。
- 影响：更新 DEVELOPMENT_TASK_BOOK、IMPLEMENTATION_PLAN、AGENTS、缺陷台账、PM→开发交接、阶段评审和状态记录；不改变 PRD、SPEC、AC、原型、架构/API/数据契约或产品范围。
- 审批结果：项目负责人已明确批准任务书 v1.1 所在候选 Commit `25e15709a3f1d92f661d37acdb8aa3e1e0e41346` 作为更新后的 Stage 4 基线，并通过 Stage 4 → Stage 5 门禁。
- 后续边界：DEV-001 可开始 TASK-001；TASK-001 通过前不得启动下游任务，本批准不构成 Stage 6/7/8 批准。
- 实施提交：`25e15709a3f1d92f661d37acdb8aa3e1e0e41346`。
- 门禁审批记录提交：`c9eb206c6517b9c3afd7f33a86e3c383d84d12aa`。
- 验证：检查所有 TASK-001 开始条件均位于门禁之后；Stage 5 准入清单不再要求先修复 TASK-001；JSON 可解析；`git diff --check` 通过。

### CR-036：修复 TASK-002 正式审核阻断项

- Level: L2
- Status: In Development
- Raised By: DEV-002 独立审核
- Raised At: 2026-07-16
- Current Stage: Stage 5 — 开发实施 / TASK-002 修复周期
- Original Request: DEV-002 对 PR #15 的精确提交 `cfb8ed9b99b5e440b3c0bf4a8652f4f7d233ee77` 提交 `Changes requested`，指出公开 API 契约未同步、受保护写操作失败审计不完整，以及设备字段、组织层级、用户/固定角色/菜单操作权限和附件敏感内容脱敏未完整实现。
- Clarified Requirement: 采用“契约完整、定向补齐”方案，在现有 FastAPI、SQLAlchemy、Alembic 架构内完成 TASK-002；不提前实现 TASK-003 的活动故障停用保护，也不提前实现附件存储、扫描和生命周期。
- Reason: 当前实现缩减了已批准的 FR-001、FR-010、FR-011 和任务书范围，且未满足 `API_SPEC` 对写操作审计与 `audit_event_id` 的统一要求，PR #15 当前不得合并。
- Impact:
  - PRD: 不修改，继续作为权威需求基线。
  - SPEC: 不修改，继续作为字段、角色和组织规则基线。
  - Prototype: 不修改，继续作为系统管理、工厂建模和设备台账交互基线。
  - Architecture: 同步 `API_SPEC.md`；必要时同步 `DATA_MODEL.md`，不改变技术栈或部署拓扑。
  - Implementation Plan: 新增 TASK-002 修复设计与实施计划，保持 TASK-003/TASK-004 依赖边界。
  - Development Task Book: 修复完成后更新 TASK-002 状态和远端候选 Commit。
  - Test Cases: 增加设备完整字段、组织层级、用户/角色权限、失败审计、幂等、脱敏和迁移测试。
  - Acceptance Criteria: 不降低或改写现有 AC；新增评审阻断项的可复现验证证据。
- Decision: 项目负责人于 2026-07-16 明确确认方案 1、数据模型、API/失败审计、迁移/测试和交付设计，授权 DEV-001 进入修复周期。
- Updated Baselines: 设计阶段仅新增 `05-development/TASK-002_REMEDIATION_DESIGN.md`；代码和契约基线待实施、Review 和新 Commit 后更新。
- Implementation:
  - Commit: 待生成新的修复候选 Commit；不得复用被拒绝的 `cfb8ed9b99b5e440b3c0bf4a8652f4f7d233ee77`。
  - Owner: DEV-001
- Verification:
  - Status: 设计已获确认，待书面设计复核、实施计划、TDD 实现、完整回归和 DEV-002 复审。
  - Evidence: PR #15 的 DEV-002 `Changes requested` 审核；`05-development/TASK-002_REMEDIATION_DESIGN.md`。

### CR-037：补齐 Stage 5 交叉审核与正式 PR 集成控制

- Level: L1
- Status: Done / PR #18 Merged
- Raised By: 工作流一致性审计
- Raised At: 2026-07-16
- Current Stage: Stage 5 — 开发实施 / TASK-002 修复暂停点
- Original Request: 项目负责人授权先修正任务书协作基线，保持既有 TASK-002 代码和未提交契约草稿不变，再继续开发与验证。
- Clarified Requirement: 将 `DEVELOPMENT_TASK_BOOK.md` 修订为 v1.2 候选，为每个正式任务明确任务开发者、指定审核者、正式 PR 创建者、任务分支/目标分支、PR 审核请求与正式 PR 的边界、正式 PR 创建条件、集成触发条件、自动化边界和集成后检查点时机。
- Reason: 任务书 v1.1 未覆盖当前 `formal-software-delivery-workflow` 的交叉审核和 reviewer-created PR 约束；同时 PR #15、FCP-002、CODE_REVIEW 和交接记录仍含被拒绝前的过期状态，已与 `workflow/state.json`、CR-036 冲突。
- Impact:
  - PRD / SPEC / Prototype / Acceptance Criteria: 不修改。
  - Architecture / API / Data Model: 不修改业务或技术契约；仅修订 Stage 5 协作和集成控制。
  - Development Task Book: v1.1 -> v1.2 候选；任务范围、负责人和依赖顺序不变。
  - Stage 5: TASK-002 后续整改暂停到 v1.2 候选获项目负责人针对精确 SHA 批准；现有代码与未提交文件保留。
  - Effective Boundary: v1.2 从尚未完成的 TASK-002 起生效；不追溯撤销已完成的 TASK-001、FCP-001 或其历史 Review/集成记录。
  - PR #15: 保留为被拒绝候选的审核历史和 Review Request 载体，不作为 v1.2 下的正式集成触发源。
  - Checkpoints / Review / Handoff: 旧记录保留并追加 `Changes Requested` / `Superseded` 状态，不删除历史。
- Decision: 项目负责人已针对精确 Commit `cd9c9b5d9d0f0a695c30881e2594e76a9f36c20b` 明确批准任务书 v1.2 协作基线并授权推送隔离治理分支。该批准不等同于 TASK-002 完成、正式 PR、集成或 Stage 6 准入；治理记录与任务书合入 `codex/stage-05-integration` 前，TASK-002 R6/R7 继续暂停。
- Updated Baselines: `04-architecture-plan/DEVELOPMENT_TASK_BOOK.md` v1.2 获批候选 Commit `cd9c9b5d9d0f0a695c30881e2594e76a9f36c20b`，远端分支 `codex/taskbook-v1-2-governance`；后续已通过 PR #18 合入并成为 Stage 5 当前协作基线。
- Implementation:
  - Owner: DEV-001（工作流协调与集成责任）
  - Candidate Commit: `cd9c9b5d9d0f0a695c30881e2594e76a9f36c20b`
  - Remote Branch: `codex/taskbook-v1-2-governance`
  - Integration Base: `d37698c6e51df1701bbdfcf12ec6fa329241e0bd`
  - Historical Wrong-Target PR: [#16](https://github.com/QI-code1992/Equipment-repair/pull/16) 曾以 `main` 为目标并显示合并，但当前远端 `main` 为 `e0a69bfb3854d9280218d01415d2f5377f1dc181`，任务书 Blob `6ba993881159f6faabfba96e45da33aabde51e06` 不等于获批 v1.2 Blob `132aa80e06ffd31154440056ab18618689738761`；PR #16 不构成当前有效基线或 CR-037 完成依据。
  - Correct Pull Request: [#18](https://github.com/QI-code1992/Equipment-repair/pull/18)（Merged），目标 `codex/stage-05-integration`
  - Review Correction: 正式审查发现任务书正文仍保留“v1.2 候选 / 等待批准”措辞，与 `STAGE_APPROVALS.md` 已批准状态冲突；已退回治理分支修正。该修正只同步状态，不改变任务内容、人员、范围、依赖或契约。
  - Merge Approval: 项目负责人于 2026-07-16T15:25:08+08:00 明确批准精确 HEAD `1d4405e1ff6066df25c896deb57248353d8695b7` 转为 Ready 并手动合入；批准后的新增提交仅允许记录该批准。
  - Merged Head: `e6b571d16192fb4462b7c118ef977df8f6ce186a`
  - Merge Commit: `18485653a94cd033cfc82e8d6c7e40c35fcfbe33`
  - Merged At: 2026-07-16T15:27:01+08:00
- Verification:
  - Status: Done。PR #18 Merge Commit 树与合并前 HEAD `e6b571d16192fb4462b7c118ef977df8f6ce186a` 一致；Python 3.13.14 为 `4 passed, 1 warning`；`compileall`、Compose 配置、治理 JSON 和 `git diff --check` 通过；相对第一父提交无 `codebase/` 修改。
  - Evidence: 当前技能 `references/stage-gate.md`、`references/development-task-book.md`；任务书 v1.1 缺口审计；PR #15 `Changes requested`；PR #16 错误目标审计；CR-036；CR-038 Merge Commit `d37698c6e51df1701bbdfcf12ec6fa329241e0bd`；PR #18 Merge Commit `18485653a94cd033cfc82e8d6c7e40c35fcfbe33`。

### CR-038：回滚未经审核门禁批准的 PR #15 集成结果

- Level: L2
- Status: Done / PR #17 Merged
- Raised By: 项目负责人
- Raised At: 2026-07-16T14:48:01+08:00
- Current Stage: Stage 5 — Development Implementation
- Original Request: PR #15 未满足指定审核人批准、任务边界验证和正式集成门禁即被合入 `codex/stage-05-integration`，不能仅记录异常，必须恢复合规的集成状态。
- Clarified Requirement: 保留 TASK-002 开发分支、提交和审计历史；通过独立补救分支对合并提交 `e328cec64f1aa9c7cdc383579af042692dce5679` 执行非破坏性 `git revert -m 1`，经补救 PR 合入后再继续 CR-037 和 TASK-002 整改。
- Reason: PR #15 的审核结论仍为 `Changes requested`，被拒绝候选 `cfb8ed9b99b5e440b3c0bf4a8652f4f7d233ee77` 不得因误合并而成为 TASK-002 完成、依赖解锁或 Stage 6 准入依据。
- Impact:
  - PRD / SPEC / Prototype / Acceptance Criteria: 不变。
  - Architecture / API / Data Model: 不变；仅撤销未经批准的集成结果。
  - Development Task Book: TASK-002 继续处于 `Changes requested`；TASK-003、TASK-004 和所有依赖 TASK-002 的数据库集成继续阻塞。
  - Code: 从集成分支有效树撤销 PR #15 引入内容，但原提交继续由 Git 历史和本地任务工作树保存。
- Decision: 项目负责人于 2026-07-16 明确批准“保留开发成果、回滚不合规集成、不改写历史”的补救方案。
- Implementation:
  - Owner: DEV-001 / Stage 5 integration owner
  - Source Branch: `codex/cr-038-revert-pr-15-gate-violation`
  - Target Branch: `codex/stage-05-integration`
  - Pull Request: [#17](https://github.com/QI-code1992/Equipment-repair/pull/17)（Merged）
  - Merge Approval: 项目负责人于 2026-07-16T15:00:35+08:00 明确批准审查候选 `3f02ac1021ffb2f189ee53120d4b3523415bff60` 转为 Ready 并手动合入；批准后的唯一允许变更是记录本批准的治理文档提交，且必须重新验证无代码或回滚边界变化。
  - Merge Commit To Revert: `e328cec64f1aa9c7cdc383579af042692dce5679`
  - Approval Record Commit: `6650f615e48d88b9a54179c27a7f03d1bf48f391`
  - Revert Commit: `5d91e83679acefa5486a25bf5b921e9c12fd52d6`
  - Merge Commit: `d37698c6e51df1701bbdfcf12ec6fa329241e0bd`
- Verification:
  - Status: Done
  - Evidence: Merge Commit 树与获批 PR 头一致；Python 3.13.14 `4 passed, 1 warning`；`compileall`、Compose 构建、PostgreSQL/Redis/API 健康和容器内 `/healthz` 通过；验证容器与网络已清理。
  - Remaining Gate: CR-037 尚未合入；TASK-002、R6/R7 和依赖任务继续暂停。

### CR-036 R6-R7 实施更新（2026-07-16）

- Status: Ready For Verification / Awaiting DEV-002 Re-review
- Implementation:
  - R6 Commit: `35119954ba1d9ca475f03d1faa026bf6a474b18f`
  - R7 Commit: `11dbb226e9b77ff5185fed5fa1434b0de6749206`
  - Branch: `codex/task-002-identity-equipment`
  - Owner: DEV-001
- Verification:
  - Python 3.13.14：`125 passed, 5 skipped`；PostgreSQL 专用集成：`5 passed`。
  - PostgreSQL 17：`0002 -> 0001 -> 0002`，最终 `0002 (head)`。
  - Compose：配置和构建通过；PostgreSQL/Redis healthy；`/healthz` 正常。
  - Review：内部独立复审 Critical 0、Important 0；历史 `.superpowers` 证据已迁入正式 `CODE_REVIEW.md` 并删除重复工作文件。
- Scope Result:
  - 已关闭 DEV-002 提出的 API 契约、失败审计、设备字段、组织层级、用户/固定角色/权限和附件引用脱敏阻断。
  - 未进入 TASK-003 活跃故障停用保护、TASK-004 RAGFlow 或后续业务范围。
- Remaining Gate:
  - 正式证据提交和远端精确 HEAD 完成后，由 DEV-001 发送书面审核请求。
  - DEV-002 审核通过后创建后继正式 PR；在正式合入前 TASK-002 不算接受，依赖不解锁。

#### 集成基线同步修正

- Finding: 首轮远端证据 `ab67bcdff42d64ba739571515df4e6faed158d32` 与当前集成分支分叉，不能直接形成无冲突的后继正式 PR。
- Correction: 通过 Merge Commit `0aac415d18aee256c237adb508d2ab24314a7486` 合入当前集成基线 `ac767c83128cb89ceea8e28c518be0adfbe1984c`。
- Boundary: TASK-002 代码与证据保留；CR-037、CR-038 和 Stage Approval 采用当前集成历史；不改写或删除既有远端提交。
- Verification: 集成分支已成为任务分支祖先；模拟合并无冲突；完整后端 `125 passed, 5 skipped`；PostgreSQL `5 passed`；迁移、Compose 实际状态和 `/healthz` 通过。
- Synchronized Candidate: `4c111d0243d947a32d555bd48b1b72cab552bac4`，已推送并完成第二次自查。
- Status: 修正与台账证据完成，等待 DEV-002 对最终远端分支 HEAD 正式复审；依赖不解锁。
