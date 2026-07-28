# 阶段审批记录

### Gate-Candidate-Stage-005: Stage 5 -> Stage 6

- 状态：Approved。
- 请求人：DEV-001
- 批准人：项目负责人
- 批准日期：2026-07-27
- 当前阶段：Stage 5 — Development Implementation
- 下一阶段：Stage 6 — Independent Testing and Quality Validation
- 候选集成 HEAD：`8a5e6ced473ea6219666d858ce5b751e61362871`
- 已审阅材料：`04-architecture-plan/DEVELOPMENT_TASK_BOOK.md`、`05-development/CHECKPOINTS.md`、`05-development/DEV_NOTES.md`、`06-testing/TEST_REPORT.md`、`06-testing/TEST_PLAN.md`、`workflow/state.json`、`workflow/DEV_TO_PM_HANDOFF.md`。
- 已审阅证据：全部 Stage 5 任务关闭记录与 FCP；`codex/stage-05-integration` 的已合并 PR；全量后端和前端回归；真实 RAGFlow Agent 成功与受控 `UNAVAILABLE` 降级；HTTPS、重启恢复、备份与隔离恢复。
- 决定：项目负责人明确批准候选集成 HEAD `8a5e6ced473ea6219666d858ce5b751e61362871` 通过 Stage 5 -> Stage 6 Gate，允许开始 Stage 6 独立测试。
- 边界：该批准仅授权以该候选基线开展 Stage 6 独立测试；不批准 Stage 7 验收、生产发布或直接合入 `main`。若测试基线发生实质变更，必须按变更控制重新评估受影响 Gate。
- 残余风险：外部 RAGFlow 在成功重跑前曾间歇性不可用；前端依赖审计报告 2 项既有 high-severity 发现；Stage 6 必须独立复核验收标准并记录自身证据。

No formal stage transition approval was found during the 2026-07-14 takeover audit.

## Current gate position

- Current effective state: `PRODUCT_CLARIFICATION_REQUIRED`
- Last approved stage: none recorded
- Pending approval: none; artifacts must first be reconciled
- Earliest affected stage: Stage 1 — Requirements Definition
- Stage 0 status: opportunity-validation evidence was not found; the project owner must either supply it or explicitly approve a scoped waiver before a formal Stage 1 gate is claimed

Do not add an `Approved` record unless the user explicitly approves the transition and the reviewed artifact versions or Commit SHA are exact.

### Review-005: Stage 4 平台级架构设计书面评审

- Status: Approved
- Approver: project owner
- Approved At: 2026-07-15
- Current Stage: Stage 4 — Architecture and Development Plan
- Next Stage: Stage 4 — API、数据模型与实施计划细化
- Artifacts Reviewed: `04-architecture-plan/平台级架构设计.md`
- Evidence Reviewed: 项目负责人对书面架构候选稿的明确回复“通过”。
- Version / Commit SHA: `a1f27431c9f79dbda310bd9c216e6a5ca75a72c3`
- Decision: 平台级架构设计 v2.1 获得书面评审通过。
- Conditions / Scope Exceptions: 这不是 Stage 4 -> Stage 5 门禁批准；必须继续完成并评审系统架构、数据模型、API 规格和实施计划，且不得开始生产开发。
- Notes: 四个 Agent 独立配置、真实深度思考、无 Agent 版本和无工厂/设备行级隔离是后续设计与开发的强制约束。

### Gate-005: Stage 4 -> Stage 5

- Status: Approved
- Approver: project owner
- Approved At: 2026-07-15
- Current Stage: Stage 4 — Architecture and Development Plan
- Next Stage: Stage 5 — Development Implementation
- Artifacts Reviewed: `04-architecture-plan/平台级架构设计.md`、`04-architecture-plan/SYSTEM_ARCHITECTURE.md`、`04-architecture-plan/DATA_MODEL.md`、`04-architecture-plan/API_SPEC.md`、`04-architecture-plan/AI_RAGFLOW_LANGGRAPH_SPEC.md`、`04-architecture-plan/ADR/ADR-001-boundary-and-source-of-truth.md`、`04-architecture-plan/IMPLEMENTATION_PLAN.md`
- Evidence Reviewed: 项目负责人对包含 RAGFlow 实际下载、部署、调试和联调责任的 Stage 4 文档包明确回复“通过”；`git diff --check` 通过，JSON 状态文件可解析。
- Version / Commit SHA: `d178f9c429ab401c3e264e413ccb4c1a76cc6cfa`；里程碑标签待创建 `baseline/stage-04-architecture-v2.1`
- Decision: Stage 4 架构与开发计划获得确认，可以进入 Stage 5 生产开发准备与实现。
- Conditions / Scope Exceptions: 所有生产实现只在 `codex/*` 开发分支提交和推送，禁止直接推送 `main`；RAGFlow 必须真实部署和联调，不得以 mock 替代；每个稳定功能单元须经过测试并记录开发检查点。
- Notes: Stage 5 开始前建立隔离开发工作区；Stage 6 测试与 Stage 7 验收仍需针对精确 Commit SHA 单独批准。

### Hold-001: Stage 5 启动暂缓

- Status: Active hold
- Decider: project owner
- Recorded At: 2026-07-15
- Current Stage: Stage 4 — Architecture and Development Plan
- Affected Next Stage: Stage 5 — Development Implementation
- Decision: 保留 Gate-005 的“可进入开发”资格，但暂不启动 Stage 5；未经项目负责人再次明确确认，不得创建或继续任何生产开发任务、开发分支或功能检查点。
- Reason: 项目负责人尚未做好进入开发阶段的准备。
- Scope: 不撤销已批准的 Stage 4 架构基线；不改变 PRD、SPEC、交互、原型、架构或实施计划的内容。
- Evidence: 项目负责人指令“这个开发的内容暂时不要。我还没做好进入开发的阶段”。

### Gate-006: 解除 Hold-001 并启动 Stage 5

- Status: Approved
- Approver: project owner
- Approved At: 2026-07-15
- Current Stage: Stage 4 — Architecture and Development Plan
- Next Stage: Stage 5 — Development Implementation
- Artifacts Reviewed: `04-architecture-plan/AGENTS.md`、`04-architecture-plan/IMPLEMENTATION_PLAN.md`、`workflow/state.json`、`workflow/PM_TO_DEV_HANDOFF.md`
- Evidence Reviewed: 项目负责人明确指令“解除 Hold-001，进入 Stage 5”。
- Version / Commit SHA: `185e5cc`
- Decision: 解除 Hold-001；允许从新的 `codex/*` 隔离开发分支开始 Stage 5，按实施计划的 Task 1 顺序执行。
- Conditions / Scope Exceptions: 仍禁止直接推送 `main`；每个稳定功能单元须先验证并记录远端开发检查点；所有基线变更仍须按变更控制执行。
- Notes: 本批准仅授权 Stage 5 开发，不代表 Stage 6 测试、Stage 7 验收或 Stage 8 发布批准。

### Review-006: Stage 5 开发任务书书面评审

- Status: Approved
- Approver: project owner
- Approved At: 2026-07-15
- Current Stage: Stage 4 — 补充整改
- Next Step: 关闭更新后的 Stage 5 准入阻塞并重新执行 Stage 4 → Stage 5 门禁
- Artifacts Reviewed: `04-architecture-plan/DEVELOPMENT_TASK_BOOK.md`
- Evidence Reviewed: 项目负责人对任务书候选稿明确回复“批准任务书”。
- Version / Commit SHA: `8272a8ed161b787098660f61ebb86fa5ccada564`
- Approval Record Commit SHA: `20261a80f01de8d18e18a2acf9c97e07087e04bc`
- Decision: 批准 Stage 5 开发任务书 v1.0 及两人制任务分配；`DEV-001` 负责最终集成和 Docker/Compose 验证，`DEV-002` 不具备 Docker 环境。
- Conditions / Scope Exceptions: 本记录仅批准任务分配基线，不是更新后的 Stage 4 → Stage 5 门禁批准，也不单独授权执行 TASK-001；`DEF-003`、`AGENTS.md` 命令、Compose 验证、同一精确 SHA 和新基线标签等准入项仍须关闭。
- Notes: 下游开发任务继续受 TASK-001 和最终门禁阻塞。

### Review-007: Stage 5 开发任务书门禁顺序修订

- Status: Changes Requested / Incorporated into candidate
- Requester: project owner
- Requested At: 2026-07-15
- Current Stage: Stage 4 — 补充整改
- Artifact Affected: `04-architecture-plan/DEVELOPMENT_TASK_BOOK.md`
- Evidence Reviewed: 项目负责人明确指出“DEV-001 执行 TASK-001 应该是需要 Stage 4 → Stage 5 门禁批准后才能进行”，随后指令“继续”。
- Decision: TASK-001 必须调整为 Stage 5 门禁后的首个阻塞任务；不得以修复 TASK-001 作为 Stage 4 门禁前置条件。
- Candidate Version / Commit SHA: v1.1 / `25e15709a3f1d92f661d37acdb8aa3e1e0e41346`
- Approval Boundary: 本记录批准纠正方向，不批准修订候选或 Stage 4 → Stage 5 门禁；门禁必须绑定新的精确 Commit SHA 另行明确批准。
- Notes: Review-006 对 v1.0 两人分配的历史批准保留；其中将 `DEF-003`、Compose 验证视为门禁前关闭项的表述由本记录纠正，不再作为当前门禁依据。

### Gate-007: 更新后的 Stage 4 → Stage 5

- Status: Approved
- Approver: project owner
- Approved At: 2026-07-15
- Current Stage: Stage 4 — Architecture and Development Plan
- Next Stage: Stage 5 — Development Implementation
- Artifacts Reviewed: `04-architecture-plan/平台级架构设计.md`、`SYSTEM_ARCHITECTURE.md`、`DATA_MODEL.md`、`API_SPEC.md`、`AI_RAGFLOW_LANGGRAPH_SPEC.md`、`ADR/`、`IMPLEMENTATION_PLAN.md`、`AGENTS.md`、`DEVELOPMENT_TASK_BOOK.md`、工作流台账
- Evidence Reviewed: 两人配置和 Docker 边界已确认；任务书 v1.1 已消除门禁循环；AGENTS 已列出当前命令及未验证环境；`DEF-003`、`DEF-004` 已登记为门禁后 TASK-001 风险；项目负责人明确回复“批准 Commit 25e15709a3f1d92f661d37acdb8aa3e1e0e41346 作为更新后的 Stage 4 基线，通过 Stage 4 → Stage 5 门禁”。
- Version / Commit SHA: `25e15709a3f1d92f661d37acdb8aa3e1e0e41346`
- Approval Record Commit SHA: `c9eb206c6517b9c3afd7f33a86e3c383d84d12aa`
- Milestone Tag: `baseline/stage-04-development-v1.1`
- Decision: 批准该精确 Commit 作为更新后的 Stage 4 开发基线并进入 Stage 5；批准记录完成后由 `DEV-001` 开始 TASK-001，无需额外任务级授权。
- Conditions / Scope Exceptions: `DEF-003`、`DEF-004` 尚未修复；当前协调环境缺少 Python 3.13 和 Docker，未验证后端或 Compose。它们必须由 `DEV-001` 在 TASK-001 中提供真实证据，TASK-001 通过前不得启动下游任务。
- Notes: 本批准只允许进入 Stage 5，不代表 TASK-001 已通过，也不批准 Stage 6、Stage 7 或 Stage 8。

### Review-008: Stage 5 开发任务书 v1.2 协作基线修订

- Status: Approved
- Approver: project owner
- Prepared At: 2026-07-16
- Approved At: 2026-07-16
- Current Stage: Stage 5 — Development Implementation / TASK-002 repair paused
- Next Step: 审查 Draft PR [#18](https://github.com/QI-code1992/Equipment-repair/pull/18)；通过并由项目负责人批准合并后，将获批任务书与一致性台账合入 `codex/stage-05-integration`。合入前不恢复 TASK-002 R6/R7。
- Artifacts Reviewed: `04-architecture-plan/DEVELOPMENT_TASK_BOOK.md` v1.2 候选、`workflow/CHANGE_REQUESTS.md` CR-037、PR #15 / CR-036 状态记录
- Evidence Reviewed: 当前 `formal-software-delivery-workflow` 的交叉审核、reviewer-created PR、正式 PR 集成触发和 checkpoint 约束；任务书 v1.1 缺口审计
- Version / Commit SHA: `cd9c9b5d9d0f0a695c30881e2594e76a9f36c20b`，远端分支 `codex/taskbook-v1-2-governance`
- Decision: 项目负责人明确批准该精确 Commit 作为任务书 v1.2 协作基线，并授权推送隔离治理分支。
- Conditions / Scope Exceptions: 本修订不改变产品、架构、API、数据模型、开发人数、任务负责人、任务范围或依赖矩阵；现有 TASK-002 代码和未提交契约文件保持原状。PR #15 保留为审核历史，不作为正式集成触发源。
- PR Target Correction: 历史 PR #16 错误指向 `main`，且当前 `origin/main` 不包含获批 v1.2 任务书 Blob，因此不构成有效集成；CR-037 必须重新通过目标为 `codex/stage-05-integration` 的治理 PR 完成。
- Notes: 本记录不重写 Gate-007 历史，不批准 TASK-002 完成、PR #15 合并、Stage 5 完成或进入 Stage 6。获批任务书及本审批记录合入 `codex/stage-05-integration` 后，DEV-001 才可恢复 TASK-002 R6/R7。
- PR #18 Review Correction: 首轮正式审查发现任务书正文仍保留“等待批准”状态，与本审批记录冲突。治理分支仅同步状态字段，不改变已批准协作内容；修正后的新精确 HEAD 必须由项目负责人再次明确批准合并，才可转为 Ready。
- PR #18 Merge Approval:
  - Status: Approved
  - Approver: project owner
  - Approved At: 2026-07-16T15:25:08+08:00
  - Approved Head: `1d4405e1ff6066df25c896deb57248353d8695b7`
  - Decision: 项目负责人明确回复“批准”，授权将 PR #18 当前精确 HEAD 转为 Ready，并由集成负责人手动合入 `codex/stage-05-integration`。
  - Conditions: 批准后的新增提交只能记录本次批准，不得修改任务书正文、代码、任务范围、人员、依赖或共享契约；推送后必须验证任务书 Blob 和 `codebase/` 相对获批 HEAD 均未变化。
- PR #19 Closure Merge Approval:
  - Status: Approved
  - Approver: project owner
  - Approved At: 2026-07-16T15:33:48+08:00
  - Approved Head: `df53489842e68037d3a2205b18f9e69fef903473`
  - Decision: 项目负责人明确回复“批准”，授权将 CR-037 合并后治理记录收尾 PR #19 转为 Ready，并由集成负责人手动合入 `codex/stage-05-integration`。
  - Conditions: 批准后的新增提交只能记录本次批准；不得修改 PR #19 已审核的 6 个收尾文件、任务书正文或 `codebase/`。PR #19 自身 Merge Commit 由 GitHub 历史作为证据，不再递归创建收尾 PR。

## Candidate gate recommendations

### Gate-001: Scoped waiver to enter Stage 3

- Status: Approved with scope exception
- Approver: project owner
- Approved At: 2026-07-14T12:56:30+08:00
- Current Stage: Stage 0–2 candidate package
- Next Stage: Stage 3 — UI and High-Fidelity Prototype
- Artifacts Reviewed: existing candidate package under `00-opportunity/`, `01-requirements/`, `02-product-interaction-design/`, and `03-ui-prototype/`
- Evidence Reviewed: user instruction: “直接进入到原型阶段”; current repository Commit `f80a93b42a5e86216388e1003ed9bf77780c0ab0`
- Version / Commit SHA: `f80a93b42a5e86216388e1003ed9bf77780c0ab0`
- Decision: enter Stage 3 directly
- Conditions / Scope Exceptions: this waives sequential Stage 0–2 gate entry only. It authorizes prototype and visual-baseline work; it does not approve the candidate requirements or interaction baselines, authorize production development, or permit Stage 4 entry. Before Stage 4, Stage 1 requirements and Stage 2 interaction baselines must be reconciled and explicitly approved.
- Notes: record Stage 3 prototype checkpoints and retain the current prototype baseline as recoverable evidence.

### Gate-Candidate-001: Stage 0 -> Stage 1

- Status: Pending user confirmation
- Approver: none recorded
- Current Stage: Stage 0 candidate package
- Next Stage: Stage 1 candidate requirements package
- Artifacts Reviewed: `00-opportunity/OPPORTUNITY.md`, `00-opportunity/COMPETITOR_ANALYSIS.md`, `00-opportunity/FEASIBILITY.md`
- Evidence Reviewed: source workspace materials and `snapshot/legacy-import-20260714`
- Version / Commit SHA: `1504d9f`
- Decision: AI recommendation only; not an approval
- Conditions: confirm opportunity value, feasibility assumptions and MVP entry

### Gate-Candidate-002: Stage 1 -> Stage 2

- Status: Pending user confirmation
- Approver: none recorded
- Current Stage: Stage 1 candidate requirements package
- Next Stage: Stage 2 candidate interaction package
- Artifacts Reviewed: `01-requirements/PRD.md`, `01-requirements/SPEC.md`, `01-requirements/ACCEPTANCE_CRITERIA.md`, `01-requirements/REQUIREMENTS_TRACEABILITY_MATRIX.md`
- Evidence Reviewed: `01-requirements/` and current prototype coverage
- Version / Commit SHA: `1504d9f`
- Decision: AI recommendation only; not an approval
- Conditions: confirm scope, roles, business rules, P0 pages and AC coverage

### Gate-002: Stage 1 -> Stage 2

- Status: Approved
- Approver: project owner
- Approved At: 2026-07-14
- Current Stage: Stage 1 — Requirements Definition
- Next Stage: Stage 2 — Product and Interaction Design
- Artifacts Reviewed: `01-requirements/PRD.md`、`01-requirements/SPEC.md`、`01-requirements/ACCEPTANCE_CRITERIA.md`、`01-requirements/REQUIREMENTS_TRACEABILITY_MATRIX.md`
- Evidence Reviewed: 项目负责人对当前需求基线的明确回复“确认”；候选基线文档提交 `25d4ba41e256b43c41fa707859801e7ea89ba3ed`；维修接单前故障诊断 Agent 的静态回归检查 14/14 通过。
- Version / Commit SHA: `25d4ba41e256b43c41fa707859801e7ea89ba3ed`；里程碑标签 `baseline/stage-01-requirements-v1.1`
- Decision: Stage 1 需求基线获得确认，可以开始 Stage 2 交互基线评审。
- Conditions / Scope Exceptions: 本确认不等同于 Stage 2、Stage 3 或 Stage 4 批准；不授权生产开发。后续交互或需求变化必须进入变更台账并回到受影响的最早阶段。
- Notes: Stage 0 的既有范围豁免保持不变；当前下一门禁为 Stage 2 的 P0 页面、功能、状态和异常覆盖确认。

### Gate-003: Stage 2 -> Stage 3

- Status: Approved
- Approver: project owner
- Approved At: 2026-07-14
- Current Stage: Stage 2 — Product and Interaction Design
- Next Stage: Stage 3 — UI and High-Fidelity Prototype
- Artifacts Reviewed: `02-product-interaction-design/PAGE_FUNCTION_MATRIX.md`、`02-product-interaction-design/INTERACTION_SPEC.md`、`02-product-interaction-design/PROTOTYPE_COVERAGE.md`
- Evidence Reviewed: 项目负责人对当前页面、功能、状态与异常交互覆盖的明确回复“确认”；现有原型静态回归检查 14/14 通过。
- Version / Commit SHA: `c21240bcf9b6b130f6508de5db99c4d99493d913`；里程碑标签 `baseline/stage-02-interaction-v1.0`
- Decision: Stage 2 交互基线获得确认，进入 Stage 3 原型与视觉基线工作。
- Conditions / Scope Exceptions: 本确认不等同于 Stage 3 原型视觉基线批准，也不授权 Stage 4 架构或生产开发；Stage 3 结束前需覆盖并复核 P0 页面关键状态。
- Notes: 维修接单前故障诊断 Agent 交互按 `INTERACTION_SPEC.md` 的“开始维修：故障诊断 Agent”章节作为 Stage 3 原型评审依据。

### Gate-004: Stage 3 -> Stage 4

- Status: Approved
- Approver: project owner
- Approved At: 2026-07-14
- Current Stage: Stage 3 — UI and High-Fidelity Prototype
- Next Stage: Stage 4 — Architecture and Development Plan
- Artifacts Reviewed: `03-ui-prototype/VISUAL_GUIDELINES.md`、`03-ui-prototype/COMPONENT_SPEC.md`、`03-ui-prototype/PROTOTYPE_BASELINE.md`、`03-ui-prototype/INTERACTION_COVERAGE.md`、`03-ui-prototype/prototype/`
- Evidence Reviewed: 项目负责人对 Stage 3 原型与视觉基线的明确回复“确认”；开始维修诊断 Agent 和既有 P0 页面静态回归检查 14/14 通过。
- Version / Commit SHA: `ce772957d77119a031d09a5fcbe744f5a00f9cdc`；里程碑标签 `baseline/stage-03-ui-v1.0`
- Decision: Stage 3 原型与视觉基线获得确认，进入 Stage 4 架构与开发计划。
- Conditions / Scope Exceptions: Stage 4 仅产出架构、API/数据契约、ADR、实施计划与验证策略；生产实现需等待 Stage 4 门禁批准后才可进入 Stage 5。
- Notes: 任何后续视觉或交互偏离应回到 Stage 2 或 Stage 3，走变更台账。

### Governance-Decision-002: CR-038 PR #15 门禁违规合并补救

- Status: Approved
- Approver: project owner
- Approved At: 2026-07-16T14:48:01+08:00
- Current Stage: Stage 5 — Development Implementation
- Artifacts Reviewed: PR #15 合并提交 `e328cec64f1aa9c7cdc383579af042692dce5679`、审核结论 `Changes requested`、被拒绝候选 `cfb8ed9b99b5e440b3c0bf4a8652f4f7d233ee77`
- Evidence Reviewed: 远端 `codex/stage-05-integration` 当前头为 `e328cec64f1aa9c7cdc383579af042692dce5679`；该提交直接合并 PR #15，未满足交叉审核和正式集成门禁。
- Decision: 批准创建 CR-038 隔离补救分支，以非破坏性 revert 撤销 PR #15 在集成分支上的有效内容；保留全部原始提交和历史。
- Merge Approval: 项目负责人于 2026-07-16T15:00:35+08:00 明确批准 PR #17 审查候选 `3f02ac1021ffb2f189ee53120d4b3523415bff60` 转为 Ready，并由集成负责人手动合入 `codex/stage-05-integration`；批准后的唯一允许变更是记录本批准的治理文档提交，且必须重新验证无代码或回滚边界变化。
- Conditions: 补救必须通过独立 PR；禁止 `reset`、强制推送或删除本地 TASK-002 工作内容；补救 PR 不得自动合并；回滚后 TASK-002 仍为 `Changes requested`。
- Next Step: 推送本批准记录，重新验证 PR 最新头后转为 Ready 并手动合入；合入后执行集成分支回归。
- Version / Commit SHA: merge `e328cec64f1aa9c7cdc383579af042692dce5679`; first parent `42098613ffa20faed3bb0dcb842a0121722565bd`; verified revert candidate `5d91e83679acefa5486a25bf5b921e9c12fd52d6`
- Merge Result: PR #17 已合入 `codex/stage-05-integration`，Merge Commit `d37698c6e51df1701bbdfcf12ec6fa329241e0bd`。
- Post-Merge Verification: Python 3.13.14 `4 passed, 1 warning`；`compileall`、Compose 构建、PostgreSQL/Redis/API 健康和容器内 `/healthz` 通过；验证容器与网络已清理。
- Notes: CR-038 已完成，但本批准不代表 TASK-002 完成，不解锁其下游依赖，也不批准进入 Stage 6；下一治理门禁为 CR-037。
