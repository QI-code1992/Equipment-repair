# Stage 5 开发任务书

## 1. 基线信息

- 项目：新能源装载机设备智能运维平台
- 当前阶段：Stage 5 — TASK-002 代码已通过 PR #20 合入；合并后技术验证已完成，本治理收尾 PR 合入前下游依赖继续锁定
- 任务书版本：v1.3（CR-040；PR #23 已合入 `codex/stage-05-integration`）
- 状态：当前有效 Stage 5 协作基线；CR-040 的 PR #23 Merge Commit 为 `d633308de8277c343faf3e266476b64baffcb565`。不追溯改写既有 PR、Review 或 Merge 历史
- v1.0 候选提交：`8272a8ed161b787098660f61ebb86fa5ccada564`
- v1.0 审批记录提交：`20261a80f01de8d18e18a2acf9c97e07087e04bc`
- v1.0 批准人：项目负责人
- v1.0 批准时间：2026-07-15
- v1.0 批准证据：项目负责人明确回复“批准任务书”
- 修订原因：项目负责人指出 TASK-001 属于 Stage 5，必须在 Stage 4 → Stage 5 门禁批准后执行；v1.0 的门禁顺序不再作为当前准入依据
- v1.1 候选提交：`25e15709a3f1d92f661d37acdb8aa3e1e0e41346`
- v1.1 批准人：项目负责人
- v1.1 批准时间：2026-07-15
- v1.1 批准证据：项目负责人明确批准候选 Commit 作为更新后的 Stage 4 基线并通过 Stage 4 → Stage 5 门禁
- v1.1 审批记录提交：`c9eb206c6517b9c3afd7f33a86e3c383d84d12aa`
- Stage 4 基线标签：`baseline/stage-04-development-v1.1`
- v1.2 修订原因：补齐交叉审核、PR 审核请求、指定审核者、正式 PR 创建者、集成触发条件和自动化边界；同步 PR #15 `Changes requested` 后的真实状态。该修订不改变产品、架构、API、数据、任务范围、负责人或依赖顺序。
- v1.2 原始获批候选：`cd9c9b5d9d0f0a695c30881e2594e76a9f36c20b`
- v1.2 批准人：项目负责人
- v1.2 批准时间：2026-07-16
- v1.2 批准证据：项目负责人明确批准上述精确 Commit 作为任务书 v1.2 协作基线并授权推送隔离治理分支
- PR #18 修正说明：正式审查曾发现任务书正文保留“等待批准”措辞，与审批台账冲突；修正仅同步治理状态，不改变已批准的任务内容、人员、范围、依赖或契约。项目负责人已批准修正后的精确 HEAD，PR #18 已合入并完成收尾验证。
- v1.3 修订原因：采用单 PR 协作流；任务开发者创建并维护自己的 Draft PR，另一名开发者在同一 PR 上审核并批准精确 HEAD，DEV-001 完成集成检查后逐个向项目负责人请求 Merge 授权，获明确授权后才执行合并。
- v1.3 批准人：项目负责人
- v1.3 批准时间：2026-07-17
- v1.3 批准证据：项目负责人明确回复“可以，按照这个规则和流程来”，并要求更新任务书、AGENTS、工作流台账及自动化指令。
- v1.3 边界：Stage 5 只有 DEV-001、DEV-002 两名开发者，不另设“DEV-001 Agent”或“DEV-002 Agent”角色。DEV-001 保持最终集成责任，但 Merge 执行者必须与任务开发者或治理 PR 作者不同。禁止 GitHub auto-merge 和 merge queue；项目负责人针对 PR 编号和精确 HEAD 明确批准后，由矩阵指定的另一名开发者执行一次 `gh pr merge --merge`。PR HEAD 变化后原批准失效。
- 关联基线：
  - PRD：`01-requirements/PRD.md`，已批准 v1.1
  - SPEC：`01-requirements/SPEC.md`，已批准 v1.1
  - Acceptance Criteria：`01-requirements/ACCEPTANCE_CRITERIA.md`
  - Requirements Traceability：`01-requirements/REQUIREMENTS_TRACEABILITY_MATRIX.md`
  - Product/Interaction：`02-product-interaction-design/PAGE_FUNCTION_MATRIX.md`、`02-product-interaction-design/INTERACTION_SPEC.md`
  - Prototype：`03-ui-prototype/PROTOTYPE_BASELINE.md`、`03-ui-prototype/prototype/`
  - Architecture：`04-architecture-plan/平台级架构设计.md`、`SYSTEM_ARCHITECTURE.md`、`API_SPEC.md`、`DATA_MODEL.md`、`ADR/`
  - Implementation Plan：`04-architecture-plan/IMPLEMENTATION_PLAN.md`
  - Coding Constraints：`04-architecture-plan/AGENTS.md`
- 编写人：工作流协调者
- 人员配置确认时间：2026-07-15
- 已知 Stage 5 首任务风险：`DEF-003`、`DEF-004`；后端测试和 Compose 真实运行验证由 TASK-001 在门禁后关闭
- 当前首要任务：DEV-001 创建并完成 TASK-002 合并后治理收尾 PR；该 PR 正确合入前，TASK-003、TASK-004、TASK-005、TASK-006 数据库集成及其他下游依赖继续锁定。开发任务仍由另一名开发者交叉审核；纯治理文档 PR 由项目负责人确认治理内容和精确 HEAD，不要求开发者交叉代码审核。

## 2. 开发人员配置

- Stage 5 参与开发人数：2
- 人员配置假设是否已由项目负责人确认：是
- 开发人员角色：
  - `DEV-001`：业务平台内核、共享数据库迁移、基础设施、Docker/Compose/RAGFlow 运行环境、DEV-002 开发任务审核、全部 PR 集成检查、Merge 授权请求、DEV-002 任务获批后的合并与合并后回归负责人。
  - `DEV-002`：AI、知识适配、Agent 配置与运行时、正式前端开发、DEV-001 开发任务审核，以及 DEV-001 任务获批后的 Merge 执行者。
- 最终集成负责人：`DEV-001`
- 是否启用交叉审核 PR 机制：是；仅适用于开发任务 PR。任务开发者创建自己的 Draft PR，另一名开发者在同一 PR 上独立审核。
- 默认审核轮转：`DEV-001` 开发的任务由 `DEV-002` 审核；`DEV-002` 开发的任务由 `DEV-001` 审核。
- 是否允许任务开发者创建自己的 PR：是；只能创建指向 `codex/stage-05-integration` 的 Draft PR，审核通过前不得自行批准或合并。
- 集成目标分支：`codex/stage-05-integration`
- 集成触发源：开发任务 PR 须由另一名开发者批准精确 HEAD；纯治理文档 PR 须由项目负责人确认治理内容和精确 HEAD。两类 PR 均须 DEV-001 集成检查通过，并获得项目负责人针对该 PR 和 HEAD 的明确 Merge 授权。
- 自动化级别：允许 L1 自动检查、L2 PR 规则校验、L3 通知和任务开发者创建/更新 Draft PR；禁止 GitHub auto-merge、merge queue 和自动进入 Stage 6。DEV-001 只能在逐 PR 获得项目负责人明确授权后执行手动 Merge 动作。
- Docker 能力：
  - `DEV-001` 具备 Docker 环境，负责所有 Compose、容器健康、RAGFlow、PostgreSQL、Redis、MinIO、Elasticsearch、Nginx 与恢复验证。
  - `DEV-002` 不具备 Docker 环境，不得单独将容器相关任务标记完成；其容器相关变更必须交由 `DEV-001` 执行真实验证。
- 是否允许并行开发：允许，但必须满足依赖矩阵和共享契约冻结点。
- 未确认项：两人的真实姓名、工期和可用工时不影响任务书生效；如影响排期，另行更新任务书，不改变职责边界。

## 3. 拆分原则

- 沿用已批准的工作包边界：业务事实与事务闭环归 `DEV-001`；AI、知识适配与前端归 `DEV-002`。
- 将原实施计划 Task 4 拆成“RAGFlow 容器环境”和“知识生命周期适配”两个任务，以匹配 Docker 能力差异。
- `codebase/backend/app/main.py`、`codebase/infra/`、共享 Alembic 迁移与跨任务 API 契约由 `DEV-001` 负责最终集成决策；具体 PR Merge 仍必须由非任务开发者执行。
- `DEV-002` 可以提交数据模型需求或迁移草案，但不得绕过 `DEV-001` 直接改变共享迁移顺序。
- 每项任务必须先写失败测试，再实现、验证、Review、推送远程分支并记录功能检查点。
- 原型只作为设计基线，继续位于 `03-ui-prototype/`；正式前端只位于 `codebase/frontend/`。

## 4. 分支与协作规则

- 集成分支：`codex/stage-05-integration`
- 任务分支：`codex/task-<task-id>-<short-name>`，例如 `codex/task-001-runtime-baseline`
- 每位开发人员使用独立工作区或 Git worktree，不共享未提交文件。
- PR 目标分支：`codex/stage-05-integration`；未经 Stage 6/7，不直接合入 `main`。
- Draft PR：任务开发者在任务开始或形成可审查切片后创建 Draft PR，并持续向同一任务分支 push；不得为同一 head/base 另建后继 PR 来代替正常复审。
- Ready 条件：任务范围完成；自测和必要真实环境验证完成；`workflow/DEV_TO_PM_HANDOFF.md` 已记录精确 HEAD、证据、未验证项、风险和请求动作；任务开发者将同一 PR 转为 Ready 并请求指定审核者审核。
- Review：指定审核者固定 PR HEAD，审查 Standards、Spec、任务边界、依赖和证据。有 Critical/Important 时提交 `Changes requested`；修订产生新 HEAD 后必须重新审核。通过时在同一 PR 上批准精确 HEAD。
- Merge 前置条件：开发任务 PR 由另一名开发者批准当前 HEAD；纯治理文档 PR 由项目负责人确认治理内容和当前 HEAD。Required checks 通过；依赖和目标分支正确；共享契约无未批准漂移；无未解决阻断项；PR 无冲突且 Mergeable。
- Merge 授权：DEV-001 完成集成检查后，必须向项目负责人报告 PR、TASK/CR、源/目标分支、精确 HEAD、适用的审核或治理确认结论、检查证据、依赖、冲突、风险、回滚和合并后计划，并逐 PR 请求授权。项目负责人未明确批准前不得合并。
- 授权失效：项目负责人批准后只要 PR HEAD、目标分支、依赖状态或检查结论发生变化，原批准立即失效，必须重新审核、重新检查并重新询问。
- Merge 执行：获批后由非任务开发者/非治理 PR 作者对同一 PR 执行 Merge Commit。DEV-002 开发的任务由 DEV-001 合并，DEV-001 开发的任务由 DEV-002 合并；纯治理 PR 由非 PR 作者的开发者合并。禁止自合并、auto-merge 和 merge queue。
- PR #15/#20 历史：PR #15 保留为 TASK-002 被拒绝候选的审核历史；PR #20 由 DEV-002 按 v1.2 创建并由 DEV-001 合入。v1.3 不追溯改写这两项历史。
- 生效边界：v1.3 适用于治理 PR 合入后仍 Open 的 Draft PR 和所有后续任务 PR，包括现有 TASK-006 Draft PR #14；不追溯改写 TASK-001、TASK-002 及 CR-037—CR-039 的历史角色和操作记录。
- PR 标题：`[TASK-xxx] <type>: <summary>`
- Commit：遵循 `04-architecture-plan/AGENTS.md` 的 `type(scope): summary`。
- 每个 Draft PR 必须包含任务 ID、任务开发者、指定审核者、目标分支、当前 HEAD、需求/AC 映射、修改文件、真实验证结果、未验证项、风险、回退方式、依赖/兼容/抽象层变化和共享契约影响。
- 每次 Ready 审核请求必须明确请求指定审核者审核同一 PR 的精确 HEAD；每次 Merge 授权请求必须绑定 PR 编号和审核通过的精确 HEAD。
- 纯治理文档 PR 仅限流程、任务书、AGENTS 和工作流台账，且不得包含 `codebase/`、测试代码、数据库迁移、基础设施或部署配置；该类 PR 不进入 DEV-001/DEV-002 交叉代码审核，改由项目负责人确认治理内容和精确 HEAD。
- 共享文件发生冲突时暂停合并，由 `DEV-001` 根据已批准 API、数据模型和本任务书决定；不能用后合并覆盖先合并。

## 5. 共享契约与所有权

### API 契约

- 权威文件：`04-architecture-plan/API_SPEC.md`
- 业务 API 所有者：`DEV-001`
- Agent API 与 SSE 实现所有者：`DEV-002`
- 最终契约集成：`DEV-001`
- 变更规则：改变公开路由、请求/响应、错误码、权限或幂等语义前，必须更新 API 规格和本任务书；产品行为变化进入变更台账。

### 数据模型与数据库迁移

- 权威文件：`04-architecture-plan/DATA_MODEL.md`
- 迁移顺序和共享 Alembic 目录所有者：`DEV-001`
- `DEV-002` 负责提供 `AgentConfig`、`AgentThread`、`AgentRun`、知识元数据所需字段与测试契约。
- 变更规则：禁止两人并行创建相同 revision 父节点；所有迁移先由 `DEV-001` 分配 revision 顺序再合并。

### UI 与原型

- 设计事实来源：`03-ui-prototype/`
- 正式前端事实来源：`codebase/frontend/`
- 正式前端所有者：`DEV-002`
- 原型变更必须返回 Stage 3；Stage 5 不得为适配实现而修改已批准原型或验收标准。

### 基础设施与运行环境

- 权威目录：`codebase/infra/`
- 唯一所有者和验证人：`DEV-001`
- `DEV-002` 不直接宣称 Docker、RAGFlow 或 Compose 验证通过；必须引用 `DEV-001` 提供的命令输出和环境信息。

### 权限、状态与事件

- 认证、角色、菜单/操作权限、业务状态和审计：`DEV-001`
- Agent 图状态、SSE 安全过程事件和运行快照：`DEV-002`
- 跨边界规则：模型与 Agent 不直接写业务事实；业务写入必须经 `DEV-001` 所有的业务 API。

## 6. 任务清单

### TASK-001：修复并重新验证平台运行基线

- 状态：Completed / 已审查并完成正式交接
- 优先级：P0
- 负责人：`DEV-001`
- 任务开发者：`DEV-001`
- 审核方式：历史独立审查已通过；v1.2 不追溯指定新的交叉审核者
- 正式 PR 创建者：不适用；TASK-001 在 v1.2 生效前已完成，不追溯补建正式 PR
- 开发者是否允许创建正式 PR：不适用；保留原始交接与 Review 历史
- PR 目标分支：不适用；以已形成的远端 FCP-001 和交接记录为准
- 任务类型：后端 / 基础设施 / 测试
- 并行属性：无；所有其他任务均受其阻塞
- 需求映射：NFR-003、NFR-004、NFR-005；AC-029、AC-031；实施计划 Task 1
- 范围：修复 `DEF-003`、`DEF-004` 中的重复定义冲突；确定唯一 `/healthz` 契约；执行 Python 3.13、测试、启动和 Compose 命令；验证 PostgreSQL/Redis/API 容器。
- 不包含：新增业务模块、认证、RAGFlow 或前端功能。
- 前置条件：更新后的 Stage 4 → Stage 5 门禁已针对精确 Commit SHA 获项目负责人批准并完成记录；无需另行进行任务级授权。
- 实际修改：`codebase/backend/app/main.py`、`codebase/backend/app/core/config.py`、`codebase/backend/tests/test_health.py`、`codebase/infra/docker-compose.yml`、Stage 5 自测、检查点、评审与缺陷记录。
- 禁止修改：PRD、SPEC、原型、公开业务 API。
- 实施步骤：
  1. 以当前失败堆栈建立最小回归测试，确认合并残留的两套契约。
  2. 依据已批准 Task 1 健康契约保留一套实现，删除重复定义和矛盾测试。
  3. 在 Python 3.13 与 DEV-001 Docker 环境运行后端、Compose 和 HTTP 健康检查。
  4. 关闭或更新 `DEF-003`、`DEF-004`，记录真实命令结果。
- 验收标准：测试收集成功且全部通过；Compose 配置通过；PostgreSQL/Redis healthy；API `/healthz` 返回已批准结果；无旧实现兼容副本。
- 验证：`python -m pytest codebase/backend/tests/test_health.py -q`；`docker compose --env-file codebase/infra/.env.example -f codebase/infra/docker-compose.yml config --quiet`；容器启动后的 HTTP `/healthz` 冒烟测试；`git diff --check`。
- 分支：`codex/task-001-runtime-baseline`
- 历史 Review：`DEV-002` 检查接口可消费性，`DEV-001` 自检并提交集成证据；该记录按 v1.2 生效边界保留，不重写为 v1.2 的指定审核或正式 PR 流程。
- 回滚：按本任务独立 Commit 反向恢复；不得恢复重复实现。
- 交接：修复提交 `87538b04a168cb3c11c2e65dfb976d3a206d8218`，验证证据提交 `45725ac083c98ea999492b709e9792082c3db284`，均已推送至 `codex/task-001-runtime-baseline`；独立 Review 通过。

### TASK-002：认证、权限、审计与设备基础

- 状态：PR #20 代码已合入且合并后技术验证完成；TASK-002 合并后治理收尾待本 PR 合入，未进入 Stage 6，依赖仍锁定
- 优先级：P0
- 负责人：`DEV-001`
- 任务开发者：`DEV-001`
- 指定审核者：`DEV-002`
- 正式 PR 创建者：`DEV-002`（v1.2 历史，不追溯）
- 开发者是否允许创建正式 PR：否（v1.2 历史，不追溯）
- PR 目标分支：`codex/stage-05-integration`
- 并行属性：Sequential After TASK-001
- 需求映射：FR-001、FR-010、FR-011、NFR-001、NFR-009；AC-001—008、AC-038、AC-039；实施计划 Task 2
- 范围：平台账号、角色、菜单/操作权限、会话、审计、幂等键、组织树和设备主数据；明确不实现工厂/设备行级授权。
- 不包含：Agent 编排、知识检索、维修闭环。
- 预计修改：`codebase/backend/app/modules/identity/`、`audit/`、`equipment/`、共享迁移、业务 API 注册。
- 共享契约：冻结认证依赖、`User/Role/Permission/Organization/Equipment` 模型和审计字段。
- 实施步骤：先写权限/唯一性/审计脱敏/幂等失败测试；实现迁移和 API；发布迁移 revision 与认证依赖；完成 Review。设备存在活跃故障时的停用保护因依赖 TASK-003 的故障与维修事实，改由 TASK-003 实现并验证。
- 验收标准：未登录和无操作权限请求被拒；合法用户按操作权限访问平台数据；设备编码唯一；审计不含敏感凭据。
- 验证：`python -m pytest codebase/backend/tests/modules/test_identity_permissions.py -q`；迁移升级/降级测试；API 契约测试；`git diff --check`。
- 分支：`codex/task-002-identity-equipment`
- PR 审核请求：`DEV-001` 在完成 CR-036 全部实现、PostgreSQL/Compose 真实验证、完整独立 Review 和正式证据更新后，推送任务分支并向 `DEV-002` 发送书面审核请求；请求必须绑定新候选精确 SHA。
- Review：`DEV-002` 复核 Agent 可使用的认证上下文、任务范围、共享契约和真实验证证据；任何 Critical/Important 均退回 `DEV-001` 修复。
- 正式 PR 与合并历史：DEV-002 审核通过任务分支 HEAD `2e89dcd8d8dff6af5b841f32ac0a7d5feb794e15` 后创建 PR #20；最终集成负责人 DEV-001（`ll979053897-arch`）以手动 Merge Commit 合入 `codex/stage-05-integration`，Merge Commit 为 `904886f48061e27c775f6ee2f8ddae99f5571ead`。该历史不按 v1.3 重写。
- 回滚：回退任务 Commit，并按迁移文档执行对应 downgrade；生产数据存在时不得直接删除表。
- 交接：旧恢复点 `0b0d9cf0dc066143c0a57d4683567fadb4714c12`、证据提交 `9f162b421f4fefae4cdd69a001891c7e83d4bc13` 和被拒候选 `cfb8ed9b99b5e440b3c0bf4a8652f4f7d233ee77` 仅保留历史。R8—R11 审计脱敏修复候选均保留可追溯；Python 3.13 为 `142 passed, 5 skipped, 1 warning`，内部网络 PostgreSQL 17 为 `5 passed, 1 warning`，Compose 容器健康且 `/healthz` 为 HTTP 200。未知字段默认脱敏未纳入范围，残余风险已记录。本治理 PR 合入后才解除 TASK-002 依赖并更新下游起始状态。
- PR：[#15](https://github.com/QI-code1992/Equipment-repair/pull/15) 已违规合并后由 CR-038 回滚并保留历史；DEV-002 创建的后继正式 PR #20 已合入。本 PR 仅完成合并后治理台账收尾。

### TASK-003：故障、工单、维修与结构化案例闭环

- 状态：Planned / Blocked until TASK-002 post-merge governance closeout is merged into `codex/stage-05-integration`
- 优先级：P0
- 负责人：`DEV-001`
- 任务开发者：`DEV-001`
- 指定审核者：`DEV-002`
- Draft PR 创建者：任务开发者
- 开发者是否允许创建 Draft PR：是；审核通过前不得自行批准或合并
- PR 目标分支：`codex/stage-05-integration`
- 并行属性：Sequential After TASK-002
- 需求映射：FR-003、FR-008、FR-RA-003；AC-010、AC-014、AC-026—028、AC-030、AC-043；实施计划 Task 3
- 范围：故障上报、工单、开始/结束维修、幂等状态迁移、人工最终字段、历史维修案例和相似案例查询。
- 不包含：RAGFlow 文档检索、诊断 Agent 生成逻辑。
- 预计修改：`codebase/backend/app/modules/maintenance/`、业务迁移、`codebase/backend/app/main.py`、相关测试。
- 共享契约：提供 `/api/fault-reports`、`/start-repair`、`/repair-result`、`/api/repair-cases/similar`；直接开始维修不保存 AI 摘要。
- 实施步骤：写状态/幂等/直接开始/活跃故障设备停用保护失败测试；实现事务闭环及设备停用保护；实现结构化案例沉淀与查询；向 `DEV-002` 交付已认证契约。
- 验收标准：非法状态迁移被拒；重复请求不重复写入；维修最终字段以人工提交为准；存在待处理或维修中故障的设备不可停用；结构化案例查询不调用 RAGFlow。
- 验证：`python -m pytest codebase/backend/tests/modules/test_maintenance_lifecycle.py -q`；API 契约和事务回滚测试；`git diff --check`。
- 分支：`codex/task-003-maintenance-lifecycle`
- PR 审核请求：`DEV-001` 完成本任务验收、验证和证据更新后，推送精确候选 SHA，并按第 4 节要求向 `DEV-002` 发送书面审核请求。
- Review：`DEV-002` 复核诊断上下文、采纳接口、任务范围和验证证据；任何 Critical/Important 均退回 `DEV-001` 修复。
- PR 与合并：DEV-001 创建并维护同一 Draft PR；DEV-002 批准精确 HEAD、DEV-001 完成集成检查并取得项目负责人逐 PR 明确授权后，由 DEV-002 合并至 `codex/stage-05-integration`。
- 回滚：回退应用 Commit；数据库迁移按已验证 downgrade 或前向修复策略处理。

### TASK-004：部署独立 RAGFlow 容器环境

- 状态：Planned / Blocked until TASK-002 post-merge governance closeout is merged into `codex/stage-05-integration`
- 优先级：P0
- 负责人：`DEV-001`
- 任务开发者：`DEV-001`
- 指定审核者：`DEV-002`
- Draft PR 创建者：任务开发者
- 开发者是否允许创建 Draft PR：是；审核通过前不得自行批准或合并
- PR 目标分支：`codex/stage-05-integration`
- 并行属性：Sequential After TASK-002，可与 DEV-002 的 TASK-006 并行
- 需求映射：FR-002、NFR-003、NFR-005、NFR-007；AC-009、AC-029、AC-033；实施计划 Task 4 的容器部分
- 范围：在 Windows Docker Desktop/WSL2 部署独立 RAGFlow、MySQL、Redis、MinIO、Elasticsearch 8.11，配置网络、健康检查、持久化和安全环境模板。
- 不包含：知识业务 API 和 Python 适配器。
- 预计修改：`codebase/infra/ragflow/`、`codebase/infra/.env.example`、运行手册候选内容。
- 共享契约：向 TASK-005 交付服务地址、认证引用、健康检查、数据集初始化方式和恢复步骤；不得与业务 PostgreSQL/Redis/MinIO 共用账户。
- 实施步骤：锁定镜像；编排独立网络与依赖；执行健康、重启、持久化和隔离验证；输出脱敏配置契约。
- 验收标准：全部容器 healthy；Elasticsearch 版本为 8.11；重启后数据与配置可恢复；无公网暴露的内部依赖。
- 验证：`docker compose --env-file codebase/infra/.env.example -f codebase/infra/ragflow/docker-compose.yml config --quiet`；`docker compose -p equipment-ragflow --env-file codebase/infra/.env.example -f codebase/infra/ragflow/docker-compose.yml up -d`；`docker compose -p equipment-ragflow -f codebase/infra/ragflow/docker-compose.yml ps`；执行重启和网络隔离检查并保存真实输出。
- 分支：`codex/task-004-ragflow-infra`
- PR 审核请求：`DEV-001` 完成本任务验收、Docker 真实验证和证据更新后，推送精确候选 SHA，并按第 4 节要求向 `DEV-002` 发送书面审核请求。
- Review：`DEV-002` 复核适配器所需契约、任务范围和验证证据；Docker 通过结论只能由 `DEV-001` 提供；任何 Critical/Important 均退回 `DEV-001` 修复。
- PR 与合并：DEV-001 创建并维护同一 Draft PR；DEV-002 批准精确 HEAD、DEV-001 完成集成检查并取得项目负责人逐 PR 明确授权后，由 DEV-002 合并至 `codex/stage-05-integration`。
- 回滚：停止并移除项目容器；卷删除属于数据删除，必须单独获得授权。

### TASK-005：知识文档生命周期与 RAGFlow 适配器

- 状态：Planned / 当前仍阻塞于 TASK-002 治理收尾、TASK-004；收尾合入后仅继续等待 TASK-004
- 优先级：P0
- 负责人：`DEV-002`
- 任务开发者：`DEV-002`
- 指定审核者：`DEV-001`
- Draft PR 创建者：任务开发者
- 开发者是否允许创建 Draft PR：是；审核通过前不得自行批准或合并
- PR 目标分支：`codex/stage-05-integration`
- 并行属性：当前 Blocked By TASK-002 governance closeout, TASK-004；收尾合入后为 Blocked By TASK-004
- 需求映射：FR-002、FR-007、NFR-002、NFR-007；AC-009、AC-024、AC-025、AC-033、AC-036；实施计划 Task 4 的应用部分
- 范围：知识文档元数据、对象存储引用、上传/状态/检索/删除适配器、引用映射、Worker 同步和超时降级。
- 不包含：RAGFlow 容器编排、历史维修案例查询。
- 预计修改：`codebase/backend/app/integrations/ragflow/`、`modules/knowledge/`、相关测试；共享迁移由 `DEV-001` 集成。
- 共享契约：只有 `READY` 文档可检索；每条引用包含文档和切片 ID；空检索不生成伪引用。
- 实施步骤：写生命周期和失败测试；实现适配器与同步任务；在 TASK-004 环境执行真实文档联调；提交引用和降级证据。
- 验收标准：真实文档可上传、解析、切片、索引、混合检索和引用；失败原因可追踪；结构化案例不进入 RAGFlow。
- 验证：`python -m pytest codebase/backend/tests/integrations/test_ragflow_adapter.py -q`；由 `DEV-001` 在 Docker 环境执行真实文档联调和重启验证。
- 分支：`codex/task-005-knowledge-ragflow`
- PR 审核请求：`DEV-002` 完成本任务验收、必要真实环境验证和证据更新后，推送精确候选 SHA，并按第 4 节要求向 `DEV-001` 发送书面审核请求。
- Review：`DEV-001` 复核网络、凭据、迁移、任务范围和真实环境证据；任何 Critical/Important 均退回 `DEV-002` 修复。
- PR 与合并：DEV-002 创建并维护同一 Draft PR；DEV-001 批准精确 HEAD、完成集成检查并取得项目负责人逐 PR 明确授权后，由 DEV-001 合并至 `codex/stage-05-integration`。
- 回滚：回退适配器 Commit；外部文档删除必须遵循业务删除和审计规则。

### TASK-006：四个 Agent 独立配置与模型能力校验

- 状态：Authorized to start / 仅限非数据库部分
- 优先级：P0
- 负责人：`DEV-002`
- 任务开发者：`DEV-002`
- 指定审核者：`DEV-001`
- Draft PR 创建者：任务开发者
- 开发者是否允许创建 Draft PR：是；审核通过前不得自行批准或合并
- PR 目标分支：`codex/stage-05-integration`
- 并行属性：TASK-001 正式交接后可并行启动领域测试和非数据库实现；数据库集成、迁移和共享数据模型当前仍 Blocked By TASK-002 governance closeout，收尾合入后解除该数据库边界
- 需求映射：FR-012、NFR-006；AC-032、AC-034；实施计划 Task 5
- 范围：四个 `agent_id` 独立配置、首次单独初始化、模型能力、深度思考校验和运行配置快照输入。
- 不包含：Agent 图执行、前端对话和版本/发布/回滚能力。
- 预计修改：`codebase/backend/app/modules/agent_config/`、配置测试、正式前端智能配置模块；共享迁移由 `DEV-001` 集成。
- 共享契约：更新一个 Agent 不影响其他 Agent；不使用共享默认对象批量覆盖；深度思考要求 `supports_reasoning=true`。
- 实施步骤：写四 Agent 隔离失败测试；实现模型与配置 API；实现推理能力校验；交付 `AgentRun.config_snapshot` 输入契约。
- 验收标准：四个 Agent 可独立读取和保存；错误模型配置被明确拒绝；密钥不返回前端。
- 验证：`python -m pytest codebase/backend/tests/modules/test_agent_config.py -q`；API 契约测试；智能配置相关前端测试。
- 分支：`codex/task-006-agent-config`
- PR 审核请求：`DEV-002` 完成本任务全部范围、验收、验证和证据更新后，推送精确候选 SHA，并按第 4 节要求向 `DEV-001` 发送书面审核请求；仅完成非数据库部分时不得请求完成态审核。
- Review：`DEV-001` 复核认证、迁移、审计、任务范围和验证证据；数据库部分未合并前不得标记完成；任何 Critical/Important 均退回 `DEV-002` 修复。
- PR 与合并：任务开发者创建并维护同一 Draft PR；指定审核者批准精确 HEAD 后，由 DEV-001 完成集成检查并取得项目负责人逐 PR 明确授权，方可合并至 `codex/stage-05-integration`。
- 回滚：回退模块 Commit；配置数据迁移按明确 downgrade 执行。

### TASK-007：Agent Runtime、LangGraph、SSE 与恢复

- 状态：Planned
- 优先级：P0
- 负责人：`DEV-002`
- 任务开发者：`DEV-002`
- 指定审核者：`DEV-001`
- Draft PR 创建者：任务开发者
- 开发者是否允许创建 Draft PR：是；审核通过前不得自行批准或合并
- PR 目标分支：`codex/stage-05-integration`
- 并行属性：Blocked By TASK-002, TASK-006
- 需求映射：FR-005、NFR-006、NFR-008、NFR-009；AC-003、AC-029、AC-034—038；实施计划 Task 6
- 范围：线程归属、运行快照、LangGraph checkpoint、工具审计、人工中断/恢复和安全 SSE 事件。
- 不包含：四个 Agent 的具体业务图、业务事实写入。
- 预计修改：`codebase/backend/app/modules/agent_runtime/`、Agent 运行测试、共享前端对话组件。
- 共享契约：SSE 事件类型遵循系统架构；不输出/保存原始思维链；线程仅创建者或管理员可读。
- 实施步骤：写线程隔离/SSE/恢复/脱敏失败测试；实现运行模型和 checkpoint；接入配置快照；验证异常与重启恢复。
- 验收标准：SSE 顺序稳定；刷新或重启可恢复；未授权线程不可读；错误不被吞掉；日志无敏感信息。
- 验证：`python -m pytest codebase/backend/tests/modules/test_agent_runtime.py -q`；SSE 契约测试；PostgreSQL checkpoint 集成测试由 `DEV-001` 提供环境。
- 分支：`codex/task-007-agent-runtime`
- PR 审核请求：`DEV-002` 完成本任务验收、验证和证据更新后，推送精确候选 SHA，并按第 4 节要求向 `DEV-001` 发送书面审核请求。
- Review：`DEV-001` 复核权限、审计、数据库边界、任务范围和验证证据；任何 Critical/Important 均退回 `DEV-002` 修复。
- PR 与合并：任务开发者创建并维护同一 Draft PR；指定审核者批准精确 HEAD 后，由 DEV-001 完成集成检查并取得项目负责人逐 PR 明确授权，方可合并至 `codex/stage-05-integration`。
- 回滚：回退 Runtime Commit；保留既有运行审计，不直接删除线程数据。

### TASK-008：AI 故障上报、智能问数与健康分读取

- 状态：Planned
- 优先级：P0
- 负责人：`DEV-002`
- 任务开发者：`DEV-002`
- 指定审核者：`DEV-001`
- Draft PR 创建者：任务开发者
- 开发者是否允许创建 Draft PR：是；审核通过前不得自行批准或合并
- PR 目标分支：`codex/stage-05-integration`
- 并行属性：Blocked By TASK-002, TASK-006, TASK-007
- 需求映射：FR-004、FR-006、FR-009；AC-011—023；实施计划 Task 7 与 Task 10 的健康分契约
- 范围：AI 故障字段采集、人工确认提交、固定指标目录、最多五项批量查询、健康分统一读取和失败降级。
- 不包含：故障诊断 Agent、模型直接计算指标或健康分。
- 预计修改：`codebase/backend/app/modules/agents/fault_reporting.py`、`metric_query.py`、健康分读取边界及测试。
- 共享契约：正式写入经 TASK-002/003 的业务 API；指标和健康分只来自受控服务，不由模型生成。
- 实施步骤：写缺失字段/指标限制/服务失败测试；实现两个状态机；接入批量指标和健康分读取；验证人工确认门禁。
- 验收标准：不完整草稿不能提交；一次查询最多五项；非法指标/维度被拒；服务失败不生成数值。
- 验证：`python -m pytest codebase/backend/tests/agents/test_fault_reporting.py codebase/backend/tests/agents/test_metric_query.py codebase/backend/tests/modules/test_health_score.py -q`；指标 API 契约测试；全部 `06-testing/tests/*.test.js`。
- 分支：`codex/task-008-fault-metric-agents`
- PR 审核请求：`DEV-002` 完成本任务验收、验证和证据更新后，推送精确候选 SHA，并按第 4 节要求向 `DEV-001` 发送书面审核请求。
- Review：`DEV-001` 复核业务写入、指标服务、权限边界、任务范围和验证证据；任何 Critical/Important 均退回 `DEV-002` 修复。
- PR 与合并：任务开发者创建并维护同一 Draft PR；指定审核者批准精确 HEAD 后，由 DEV-001 完成集成检查并取得项目负责人逐 PR 明确授权，方可合并至 `codex/stage-05-integration`。
- 回滚：回退 Agent Commit，不影响业务 API 已有人工流程。

### TASK-009：操作指引与维修前故障诊断 Agent

- 状态：Planned
- 优先级：P0
- 负责人：`DEV-002`
- 任务开发者：`DEV-002`
- 指定审核者：`DEV-001`
- Draft PR 创建者：任务开发者
- 开发者是否允许创建 Draft PR：是；审核通过前不得自行批准或合并
- PR 目标分支：`codex/stage-05-integration`
- 并行属性：Blocked By TASK-003, TASK-005, TASK-006, TASK-007
- 需求映射：FR-007、FR-RA-001—004、NFR-002、NFR-003；AC-024、AC-025、AC-040—044；实施计划 Task 8
- 范围：操作指引最多两次定向检索；维修前诊断的预诊断、动态追问、报警码、证据门槛、采纳/直接开始、降级与摘要。
- 不包含：直接写维修事实、修改已批准原型。
- 预计修改：`codebase/backend/app/modules/agents/operation_guidance.py`、`fault_diagnosis.py`、相关测试。
- 共享契约：历史案例来自 TASK-003；文档引用来自 TASK-005；采纳写入调用 TASK-003；直接开始清除临时诊断。
- 实施步骤：写 8/24/4 上限、报警码、否定证据、证据不足和采纳门禁测试；实现两类图；接入预诊断和受控工具；执行真实 RAGFlow/LLM 降级验证。
- 验收标准：证据不足不能产生可采纳根因；报警码问题不可跳过；直接开始不保留 AI 摘要；失败保留人工流程。
- 验证：`python -m pytest codebase/backend/tests/agents/test_operation_guidance.py codebase/backend/tests/agents/test_fault_diagnosis.py -q`；真实 RAGFlow 引用测试由 `DEV-001` 提供 Docker 环境；`node 06-testing/tests/fault-report-repair-agent.test.js`。
- 分支：`codex/task-009-guidance-diagnosis`
- PR 审核请求：`DEV-002` 完成本任务验收、真实 RAGFlow/数据库验证和证据更新后，推送精确候选 SHA，并按第 4 节要求向 `DEV-001` 发送书面审核请求。
- Review：`DEV-001` 复核业务写入、Docker/RAGFlow 证据、安全、降级、任务范围和验证证据；任何 Critical/Important 均退回 `DEV-002` 修复。
- PR 与合并：任务开发者创建并维护同一 Draft PR；指定审核者批准精确 HEAD 后，由 DEV-001 完成集成检查并取得项目负责人逐 PR 明确授权，方可合并至 `codex/stage-05-integration`。
- 回滚：回退 Agent Commit，人工开始/结束维修流程必须继续可用。

### TASK-010：正式前端与批准原型流程集成

- 状态：Planned
- 优先级：P0
- 负责人：`DEV-002`
- 任务开发者：`DEV-002`
- 指定审核者：`DEV-001`
- Draft PR 创建者：任务开发者
- 开发者是否允许创建 Draft PR：是；审核通过前不得自行批准或合并
- PR 目标分支：`codex/stage-05-integration`
- 并行属性：Blocked By TASK-003, TASK-008, TASK-009
- 需求映射：页面功能矩阵全部 P0 页面；AC-012—015、AC-031、AC-039—044；实施计划 Task 9
- 范围：建立正式 TypeScript 前端工程；以 API 替代静态数据；接入流式对话、引用、采纳/直接开始、结束维修摘要和权限状态。
- 不包含：把 Stage 3 原型复制到 `codebase/frontend/`、擅自更改原型或业务规则。
- 预计修改：`codebase/frontend/package.json`、`src/`、前端单元/交互测试；只读参考 `03-ui-prototype/`。
- 共享契约：只消费已合并 API；正式前端事实来源唯一位于 `codebase/frontend/`。
- 实施步骤：先定义并记录 package scripts；写交互失败测试；按页面/组件最小迁移批准流程；执行构建、测试和原型差异审查。
- 验收标准：关键加载/空/错/权限状态存在；SSE 与引用真实；摘要显隐符合 AC；正式代码不依赖原型运行目录。
- 验证：`npm --prefix codebase/frontend test`；`npm --prefix codebase/frontend run build`；全部 `06-testing/tests/*.test.js`；浏览器关键流程检查。
- 分支：`codex/task-010-frontend-integration`
- PR 审核请求：`DEV-002` 完成本任务验收、前端验证和证据更新后，推送精确候选 SHA，并按第 4 节要求向 `DEV-001` 发送书面审核请求。
- Review：`DEV-001` 复核 API、权限、端到端可运行性、任务范围和验证证据；任何 Critical/Important 均退回 `DEV-002` 修复。
- PR 与合并：任务开发者创建并维护同一 Draft PR；指定审核者批准精确 HEAD 后，由 DEV-001 完成集成检查并取得项目负责人逐 PR 明确授权，方可合并至 `codex/stage-05-integration`。
- 回滚：按页面/功能 Commit 回退，保持其他已集成页面不受影响。

### TASK-011：平台补齐、端到端、安全与发布准备

- 状态：Planned
- 优先级：P0
- 负责人：`DEV-001`
- 任务开发者：`DEV-001`
- 指定审核者：`DEV-002`
- Draft PR 创建者：任务开发者
- 开发者是否允许创建 Draft PR：是；审核通过前不得自行批准或合并
- PR 目标分支：`codex/stage-05-integration`
- 并行属性：Blocked By TASK-003, TASK-004, TASK-005, TASK-007, TASK-008, TASK-009, TASK-010
- 需求映射：NFR-001—009、AC-029—038、Stage 8 部署要求；实施计划 Task 10
- 范围：健康分服务最终闭环、附件安全、Nginx HTTPS、备份恢复、超时降级、全量 E2E、安全与恢复演练、开发交接。
- 不包含：Stage 6 独立测试结论、Stage 7 产品验收或生产发布批准。
- 预计修改：`codebase/backend/tests/e2e/`、`codebase/infra/nginx/`、基础设施配置、Stage 5/6/8 交付材料。
- 共享契约：汇总全部模块；`DEV-002` 必须提供 Agent 与前端回归证据，`DEV-001` 负责容器和最终集成证据。
- 实施步骤：写端到端失败测试；补齐部署与安全配置；执行全栈集成、备份恢复和降级演练；形成精确集成 SHA 与 DEV→PM 交接。
- 验收标准：全量测试和构建通过；容器重启可恢复；备份可还原；内部服务不暴露公网；无高危未关闭缺陷。
- 验证：`python -m pytest codebase/backend/tests -q`；`npm --prefix codebase/frontend test`；`npm --prefix codebase/frontend run build`；`docker compose --env-file codebase/infra/.env.example -f codebase/infra/docker-compose.yml config --quiet`；业务栈和 RAGFlow 栈真实联调；全部 `06-testing/tests/*.test.js`；备份恢复演练；`git diff --check`。
- 分支：`codex/task-011-e2e-release-readiness`
- PR 审核请求：`DEV-001` 完成本任务验收、全量验证和证据更新后，推送精确候选 SHA，并按第 4 节要求向 `DEV-002` 发送书面审核请求。
- Review：`DEV-002` 复核 Agent/前端回归、任务范围和验证证据；任何 Critical/Important 均退回 `DEV-001` 修复。
- PR 与合并：DEV-001 创建并维护同一 Draft PR；DEV-002 批准精确 HEAD、DEV-001 完成集成检查并取得项目负责人逐 PR 明确授权后，由 DEV-002 合并至 `codex/stage-05-integration`。
- 回滚：以最近稳定 FCP 和独立任务 Commit 选择性回退；不得整体回退丢失其他已接受功能。

## 7. 人员分配与交叉审核矩阵

| 开发者 | 分配开发任务 | 默认审核任务 | Draft PR 创建责任 | 主要范围 | Docker 责任 | 集成责任 |
|---|---|---|---|---|---|---|
| DEV-001 | TASK-001、002、003、004、011 | TASK-005、006、007、008、009、010 | 创建并维护自己的任务 Draft PR | 平台事实、权限、维修、基础设施、E2E | 唯一验证人 | 对全部 PR 执行集成检查和授权请求；合并 DEV-002 的 PR；负责合并后回归 |
| DEV-002 | TASK-005、006、007、008、009、010 | TASK-002、003、004、011；TASK-001 仅保留历史独立审查 | 创建并维护自己的任务 Draft PR | 知识适配、Agent、正式前端 | 无本地 Docker；提交给 DEV-001 验证 | 合并 DEV-001 的获批 PR；提供模块开发、交叉审核与回归证据 |

## 8. 依赖、并行与协作矩阵

| 任务 | 开发者 / Draft PR 创建者 | 指定审核者 | Merge 执行者 | 优先级 | 依赖模式 | 可开始条件 |
|---|---|---|---|---:|---|---|
| TASK-001 | DEV-001 | 历史独立审查（v1.3 不追溯） | 历史记录不追溯 | P0 | 无 | 已完成并形成远端 FCP-001；保留真实历史记录 |
| TASK-002 | DEV-001 | DEV-002 | 历史由 DEV-001 合并（v1.3 不追溯） | P0 | Sequential After TASK-001 | TASK-001 测试、Compose、Review、FCP 均通过 |
| TASK-003 | DEV-001 | DEV-002 | DEV-002，需项目负责人逐 PR 授权 | P0 | Sequential After TASK-002 governance closeout | TASK-002 合并后治理台账已正确集成，身份、审计和迁移基础已完成回归 |
| TASK-004 | DEV-001 | DEV-002 | DEV-002，需项目负责人逐 PR 授权 | P0 | Sequential After TASK-002 governance closeout | TASK-002 合并后治理台账已正确集成，业务容器基线与网络契约可开始实施 |
| TASK-005 | DEV-002 | DEV-001 | DEV-001，需项目负责人逐 PR 授权 | P0 | 当前 Blocked By TASK-002 governance closeout, TASK-004；随后 Blocked By TASK-004 | 收尾合入后 TASK-002 条件满足；RAGFlow 环境仍须由 TASK-004 审核、正式集成并可用 |
| TASK-006 | DEV-002 | DEV-001 | DEV-001，需项目负责人逐 PR 授权 | P0 | Parallel After TASK-001；DB 集成当前 Blocked By TASK-002 governance closeout | 可继续领域测试和非数据库实现；收尾合入后才可进行迁移、数据库集成和共享数据模型 |
| TASK-007 | DEV-002 | DEV-001 | DEV-001，需项目负责人逐 PR 授权 | P0 | Blocked By TASK-002, TASK-006 | 认证、迁移和 Agent 配置契约已审核并正式集成 |
| TASK-008 | DEV-002 | DEV-001 | DEV-001，需项目负责人逐 PR 授权 | P0 | Blocked By TASK-002, TASK-006, TASK-007 | 业务工具、配置和 Runtime 可用 |
| TASK-009 | DEV-002 | DEV-001 | DEV-001，需项目负责人逐 PR 授权 | P0 | Blocked By TASK-003, TASK-005, TASK-006, TASK-007 | 维修、案例、知识和 Runtime 全部已审核并正式集成 |
| TASK-010 | DEV-002 | DEV-001 | DEV-001，需项目负责人逐 PR 授权 | P0 | Blocked By TASK-003, TASK-008, TASK-009 | 所有正式页面所需 API 与 Agent 已审核并正式集成 |
| TASK-011 | DEV-001 | DEV-002 | DEV-002，需项目负责人逐 PR 授权 | P0 | Blocked By TASK-003—010 | 所有模块 PR 已 Review、合入集成分支并完成回归 |

## 9. 集成计划

- 集成负责人：`DEV-001`
- 集成负责人已由项目负责人确认：是。
- 集成目标分支：`codex/stage-05-integration`
- 唯一集成触发源：开发任务 PR 已由另一名开发者批准当前精确 HEAD，或纯治理文档 PR 已由项目负责人确认治理内容和当前精确 HEAD；DEV-001 集成检查通过，且项目负责人明确批准合并该 PR 和 HEAD。
- 不得作为集成触发源：任务分支 push、Draft PR 创建、单独 CI 通过、过期 approval、未绑定精确 HEAD 的口头批准、PR #15 被拒绝历史或未绑定任务书的自动化事件。
- 自动化策略：允许开发者创建/更新自己的 Draft PR、执行检查、提交 Review、发送通知和准备 Merge 授权请求；禁止 GitHub auto-merge、merge queue 和自动进入 Stage 6。矩阵指定的非任务开发者获项目负责人逐 PR 授权后执行的 Merge Commit 不属于 auto-merge。
- 推荐集成顺序：TASK-001 → TASK-002 → TASK-006 → TASK-007 → TASK-004 → TASK-005 → TASK-003 → TASK-008 → TASK-009 → TASK-010 → TASK-011。
- 顺序允许在依赖满足后微调，但必须先更新本任务书；不得仅在聊天中改变。
- 每次集成前检查：开发任务 PR 的另一名开发者已批准当前精确 HEAD且审核后无新增提交；纯治理文档 PR 的项目负责人已确认治理内容和当前精确 HEAD。目标分支正确；required checks 通过；依赖已正式集成；真实检查结果齐全；共享契约未漂移；无禁止范围修改；相关文档已更新；无未解决阻断项；PR 无冲突且 Mergeable。
- Merge 授权请求：`DEV-001` 必须向项目负责人报告 TASK/CR、PR、源/目标分支、精确 HEAD、适用的审核或治理确认结论、Critical/Important/Minor 或治理检查结果、测试与 Docker 证据（如适用）、依赖、冲突、共享契约、风险、回滚和合并后验证计划，并询问是否批准合并。
- 集成执行：只有项目负责人明确批准该 PR 和精确 HEAD 后，矩阵指定的非任务开发者/非治理 PR 作者才可执行 Merge Commit。DEV-002 开发的任务由 DEV-001 合并，DEV-001 开发的任务由 DEV-002 合并；纯治理 PR 由非 PR 作者的开发者合并。审批后 HEAD 或条件变化则重新核查和询问；开发任务 PR 还须重新审核。禁止 auto-merge 或 merge queue。合并失败或发现契约冲突时停止，不覆盖既有提交。
- 每次集成后执行：记录 Merge Commit SHA；运行最小相关测试、受影响模块回归、`git diff --check`；涉及容器时由 `DEV-001` 执行 Compose/健康检查；记录风险和回滚方式。
- 功能检查点：每个任务集成并通过回归后，在 `05-development/CHECKPOINTS.md` 新增 FCP，记录远程 Commit SHA、范围、证据和恢复命令。
- 冲突处理：
  1. 普通文件冲突由文件所有者提出解决方案，`DEV-001` 审核。
  2. API、数据、权限、状态或事件冲突暂停双方任务，回到 Stage 4 契约。
  3. 不通过复制第二套模型、服务或接口绕过冲突。
- 回滚策略：优先选择性 `git revert` 独立任务 Commit；共享迁移使用已验证 downgrade 或前向修复；任何数据删除另行授权。

## 10. 变更规则

以下情况必须先更新本任务书：开发人数、负责人、任务开发者、指定审核者、Draft PR 规则、审核轮转、PR 目标分支、Merge 执行者、授权方式、集成触发方式、自动化级别、Docker 能力、任务范围、依赖、集成顺序、共享 API/数据/权限/状态/事件、基础设施所有权发生变化。

- 仅实现细节变化且不影响契约：L0，更新任务记录并正常 Review。
- 任务或协作方式变化：更新本任务书并由项目负责人确认。
- 产品、原型、架构、API、数据、测试或验收基线变化：进入 `workflow/CHANGE_REQUESTS.md` 的 L2/L3 变更控制。
- 未获批准的任务不得开始；Blocked 任务不得只因开发人员空闲而提前实现。

## 11. 完成与交接

每个开发任务必须提交：任务 ID、任务开发者、同一 Draft/Ready PR、另一名开发者及精确 HEAD 审核结论、DEV-001 集成检查、项目负责人 Merge 授权、PR/Merge Commit、修改文件、验证命令与真实结果、未验证项、依赖变化、兼容代码、抽象层、共享契约影响、风险和回滚方式。

所有任务完成后，`DEV-001` 必须输出：

- 集成分支和精确 Commit SHA。
- 集成顺序、冲突处理和所有 FCP。
- 后端、前端、Compose、RAGFlow、E2E、安全与恢复验证结果。
- `DEV-002` 提供的 Agent/前端交接证据。
- 未关闭缺陷和残余风险。
- 更新后的 `workflow/DEV_TO_PM_HANDOFF.md`。
- 是否建议进入 Stage 6；该建议不等于 Stage 6 门禁批准。

## 12. Stage 5 准入检查

本任务书 v1.1 是对已批准 v1.0 的门禁顺序修订。只有以下条件全部满足后，项目才能进入 Stage 5；TASK-001 只能在门禁批准后开始：

- [x] Stage 5 两人配置、职责和 Docker 能力边界已确认。
- [x] `DEF-003`、`DEF-004` 已登记为 Stage 5 首任务风险，不要求在 Stage 4 门禁前修改代码或配置。
- [x] `AGENTS.md` 已更新当前 `codebase/` 命令、目标环境和已知未验证项。
- [x] 最新 Stage 4 架构、目录规范、实施计划、AGENTS、任务书和工作流台账形成精确候选 Commit `25e15709a3f1d92f661d37acdb8aa3e1e0e41346` 并推送远端。
- [x] 项目负责人确认修订后的任务书 v1.1 属于 Stage 4 开发基线。
- [x] 项目负责人对更新后的精确 SHA 明确批准 Stage 4 → Stage 5。
- [x] 门禁批准记录已提交并推送，新 Stage 4 基线标签 `baseline/stage-04-development-v1.1` 已绑定获批 SHA 且不可移动。
