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
