# 代码评审

- 状态：TASK-001 已完成独立审查；TASK-002 已获 DEV-002 正式批准并由 DEV-001 手动合入 PR #20，技术验证完成；合并后治理收尾已通过 PR #25 合入，TASK-002 前置已解除。
- 范围：已审查 TASK-001 平台运行基线、TASK-002 CR-036 修复候选及其正式集成，以及 TASK-006 已验证的非数据库切片；后续任务仍须逐任务交叉审核。
- 评审门禁：每个有意义的实现切片都必须完成规格符合性、质量评审、测试，并具备可追溯的功能/页面检查点。

## TASK-002 正式审核、手动集成与治理收尾（2026-07-17）

- DEV-002 对精确任务分支 HEAD `2e89dcd8d8dff6af5b841f32ac0a7d5feb794e15` 的正式审核结论为批准；此前 R10 对“合并后治理台账”候选提出的 3 个 Important 不否定代码审核结论，而是要求修正交付状态和依赖表述。
- PR #20 的正式代码合并为 `904886f48061e27c775f6ee2f8ddae99f5571ead`，由集成负责人 DEV-001（`ll979053897-arch`）手动执行；不得遗漏该执行人和手动合并方式。
- 已保留技术证据：Python 3.13 `142 passed, 5 skipped, 1 warning`；PostgreSQL 17 专项 `5 passed, 1 warning`；Compose 健康与容器内 `/healthz` HTTP 200。
- 本治理 PR 关闭的台账问题：过期“等待审核/已解锁”摘要、TASK-005/006 的错误依赖状态、PR #20 缺失的 DEV-001 手动合并记录。
- 当前结论：代码审核、技术集成与合并后治理收尾均通过；TASK-003/004 可启动，TASK-005 仍等待 TASK-004，TASK-006 已解除 TASK-002 前置；未把基于字段语义的审计脱敏提升为“可识别任意命名秘密”的保证。

## TASK-006 非数据库切片（2026-07-15）

- 已验证：不可变 Agent 配置领域模型、独立仓储/模型目录端口、四 Agent 隔离、推理能力校验和未挂载 API 契约。
- 安全修复：`04e651c` 将请求校验失败统一为稳定脱敏响应；非数据库回归为 `24 passed, 1 warning`。
- 边界：数据库仓储、迁移、认证/审计接入、正式路由和真实模型验证尚未完成；后续数据库部分仍需 DEV-001 审核及真实 PostgreSQL/Compose 证据。

## Task 1 评审（2026-07-15）

- 规格符合性：已建立实施计划指定的目录、配置加载、应用工厂、`GET /healthz`、PostgreSQL/Redis Compose 健康检查和失败测试。
- 契约：健康检查仅暴露配置状态，不伪造数据库或缓存读写成功；未发布数据库、缓存或 API 宿主机端口。
- 质量：无新增兼容层或通用抽象；未新增生产外部依赖；Docker Hub 的临时网络问题由可配置镜像前缀处理。
- 已知项：测试环境存在 FastAPI/Starlette 的弃用警告；在后续依赖锁定任务中统一处理，不作为本任务阻塞。
- 独立审查：审查范围 `e0a69bf..87538b0`；结论为通过，无阻断、重要或次要问题。确认仅保留一个 `create_app`、一个 `/healthz` 契约和一个 Compose `platform` 内部网络；未发现接口漂移、依赖变更、兼容层或额外抽象。
- 审查证据：Python 3.13 测试 4 passed；Compose 配置通过；PostgreSQL、Redis healthy；容器内 `/healthz` 返回 200。工作区中未提交的 API 健康检查配置不属于 `87538b0`，未纳入本次审查或交接基线。

## TASK-002 评审（2026-07-15）

- 审查范围：`42098613ffa20faed3bb0dcb842a0121722565bd..0b0d9cf0dc066143c0a57d4683567fadb4714c12`，包含设计、实施计划、迁移、身份/权限、审计、幂等、组织与设备 API 及测试。
- 首轮：发现 1 个 Critical、8 个 Important、2 个 Minor；主要为首个管理员引导死锁、查询/更新契约缺失、审计不完整、并发幂等和唯一冲突、脱敏及时区语义问题。
- 二轮：原问题大部分关闭，新增确认 flush 阶段唯一冲突、设备组织外键、组织循环和失效会话登出等 4 个 Important、2 个 Minor；均通过新增失败测试修复。
- 三轮：发现不同键并发组织更新仍可能交叉成环，以及 camelCase 脱敏和 bootstrap actor 语义问题；加入组织树共享 PostgreSQL transaction advisory lock，并完成两项语义修正。
- 最终独立复审：Critical 0、Important 0、Minor 0，建议提交；独立执行 `python -m pytest codebase/backend/tests -q -p no:cacheprovider` 为 38 passed，`git diff --check` 无内容错误。
- 范围检查：未实现工厂/设备行级过滤；活跃故障设备停用保护仍按获批边界留给 TASK-003；无额外兼容层、无无关重构。

## TASK-002 正式交叉审核退回（2026-07-16）

- 审核对象：PR #15，精确候选 `cfb8ed9b99b5e440b3c0bf4a8652f4f7d233ee77`。
- 指定审核者：DEV-002 / GitHub 审核人 `QI-code1992`。
- 结论：`Changes requested`；该结论取代上节针对更早实现切片的“建议提交”，但不删除旧审查历史。
- 已通过证据：Python 3.13 后端测试 38 passed；`compileall` 通过；`git diff --check` 通过。
- Standards 阻断：公开 API 契约未同步；受保护写操作失败审计与失败 `audit_event_id` 不完整。
- Spec 阻断：设备字段、组织层级、用户/固定角色/菜单操作权限及附件敏感内容脱敏未完整实现。
- 处置：进入 CR-036 修复周期；被拒绝 SHA 不得复用为完成、正式 PR、FCP 或集成依据。新候选必须完成 PostgreSQL/Compose 真实验证、完整独立 Review 和 DEV-002 复审。
- PR 边界：按获批任务书 v1.2 精确候选 `cd9c9b5d9d0f0a695c30881e2594e76a9f36c20b`，PR #15 保留为被拒绝历史和 Review Request 载体，不作为后继正式集成 PR；治理 PR 合入前不恢复 TASK-002 R6/R7。

## CR-038 补救审查（2026-07-16）

- 原因：PR #15 在正式审核结论仍为 `Changes requested` 时被合入集成分支，违反任务书和 Stage 5 集成门禁。
- 审查范围：授权记录 `6650f615e48d88b9a54179c27a7f03d1bf48f391` 与回滚候选 `5d91e83679acefa5486a25bf5b921e9c12fd52d6`。
- 边界检查：使用 `git revert -m 1 e328cec` 的非破坏性反向提交；未使用 reset、force-push 或历史改写；TASK-002 原提交仍可恢复。
- 树状态：相对 PR #15 第一父提交 `42098613ffa20faed3bb0dcb842a0121722565bd`，仅保留 CR-038 治理记录。
- 验证：Python 3.13.14 后端测试 `4 passed, 1 warning`；`compileall`、Compose 配置、`git diff --check` 通过。
- 结论：回滚候选满足创建补救 PR 的条件；在补救 PR 合入前，TASK-002 仍为 `Changes requested`，所有依赖保持阻塞。
- 正式治理审查：PR #17 当前头 `3f02ac1021ffb2f189ee53120d4b3523415bff60` 的源/目标分支、36 个文件边界、4 个提交、回滚树一致性和治理证据均通过；GitHub 状态为 `clean`，无评论、无 Review、无 CI checks。
- 合并决定：项目负责人已于 2026-07-16T15:00:35+08:00 明确批准将 PR #17 转为 Ready 并手动合入。
- 合并结果：PR #17 已合入 `codex/stage-05-integration`，Merge Commit 为 `d37698c6e51df1701bbdfcf12ec6fa329241e0bd`。
- 合并后验证：Merge Commit 树与获批 PR 头 `9c1ff88a6842ffa1cb79bd63807b3d41d830d5bd` 一致；Python 3.13.14 `4 passed, 1 warning`；Compose 构建和容器健康通过；`/healthz` 返回正常。
- 结论：CR-038 技术补救通过；TASK-002 仍为 `Changes requested`，CR-037 合入前不恢复 R6/R7。

## CR-037 PR 目标审查（2026-07-16）

- 历史发现：PR #16 曾以 `main` 为目标并显示合并，不符合任务书规定的 `codex/stage-05-integration` 目标。
- 当前事实：`origin/main` 为 `e0a69bfb3854d9280218d01415d2f5377f1dc181`；其任务书 Blob 不等于获批 v1.2 Blob，因此错误目标 PR 未形成当前有效基线。
- 处置：PR #16 仅保留为错误目标历史；CR-037 已创建新的 Draft PR [#18](https://github.com/QI-code1992/Equipment-repair/pull/18)，目标严格为 `codex/stage-05-integration`。

## CR-037 PR #18 正式审查（2026-07-16）

- 审查对象：PR #18 首轮 HEAD `3231c9e191d33ee7132a5ea9dff13e29cf7af856`，目标 `codex/stage-05-integration`。
- 范围检查：9 个文件均为任务书或治理台账；相对目标分支无 `codebase/` 修改，无产品、架构、API、数据模型或业务代码变更。
- 已通过项：目标分支正确；11 个 TASK 协作字段完整；TASK-002—011 均由对方审核并创建正式 PR；依赖矩阵、集成触发、自动化边界和 PR #15 / CR-038 状态基本一致；`workflow/state.json` 可解析；`git diff --check` 通过。
- 阻断项：任务书正文仍写“v1.2 候选、等待项目负责人批准、获批前暂停”，但 `workflow/STAGE_APPROVALS.md` 与 CR-037 已记录精确 Commit `cd9c9b5d9d0f0a695c30881e2594e76a9f36c20b` 获批，形成当前基线状态矛盾。
- 首轮结论：Changes Requested；PR #18 不得转 Ready 或合并。
- 修正边界：只同步任务书和治理台账状态，不修改已批准任务内容、人员、范围、依赖、API、数据或代码；修正后重新检查完整 diff，并由项目负责人批准新的精确 HEAD 后再转 Ready。
- 修正提交：`e0f60f84d5ed31b693ad4f617b7b4c02ded0f718`。
- 修正复审：旧状态措辞已从任务书清除；11 项任务矩阵和 TASK-002—011 交叉审核规则通过；`workflow/state.json` 解析、Python 3.13 健康测试、`compileall`、Compose 配置和 `git diff --check` 通过；相对目标分支仍无 `codebase/` 修改。
- 复审结论：通过；等待项目负责人批准包含本复审证据的最终精确 HEAD，未获批准前 PR #18 保持 Draft。
- 合并批准：项目负责人于 2026-07-16T15:25:08+08:00 明确批准精确 HEAD `1d4405e1ff6066df25c896deb57248353d8695b7` 转为 Ready 并手动合入；批准记录提交后必须复核任务书和 `codebase/` 相对获批 HEAD 未变化。

## CR-037 PR #18 合并后审查（2026-07-16）

- 合并结果：PR #18 已合入 `codex/stage-05-integration`，Merge Commit 为 `18485653a94cd033cfc82e8d6c7e40c35fcfbe33`。
- 边界复核：批准记录 HEAD `e6b571d16192fb4462b7c118ef977df8f6ce186a` 相对获批 HEAD `1d4405e1ff6066df25c896deb57248353d8695b7` 只修改 4 个批准记录文件；任务书 Blob 与 `codebase/` 均未变化。
- 合并树：Merge Commit 树与 `e6b571d16192fb4462b7c118ef977df8f6ce186a` 树一致。
- 验证：Python 3.13.14 `4 passed, 1 warning`；`compileall`、Compose 配置、`workflow/state.json` 解析和 `git diff --check` 通过；相对第一父提交无 `codebase/` 修改。
- 结论：CR-037 技术与治理集成通过；本结论不代表 TASK-002 完成，也不解锁 TASK-003、TASK-004 或依赖 TASK-002 的数据库集成。

## TASK-002 / CR-036 R6-R7 独立复审（2026-07-16）

- 审查范围：拒绝前基线 `53e01e6b9f212c6965414654805979bdd59838ce..11dbb22`，并复核当前正式证据差异。
- 首轮 R7：发现 1 Critical、6 Important、2 Minor。Critical 为 PostgreSQL 测试可对任意 DSN 执行清理；Important 包括失败响应契约、真实失败事务/审计、幂等并发、最后管理员认证竞态、非规范证据文件和测试规模。
- 安全修复：PostgreSQL 集成测试仅允许 Compose 主机 `postgres`、数据库名 `equipment_task2_validation*`，且必须显式设置 `TASK002_ALLOW_DESTRUCTIVE_TESTS=1`；测试前后均清理专用数据。
- 契约修复：失败 `detail` 固定为 `code,message,fields`，受保护写失败再含真实 `audit_event_id`；稳定字段映射覆盖幂等 Key、用户名、组织 code/name 和设备 code；`AUDIT_PERSIST_FAILED` 不伪造审计 ID。
- 真实数据库修复：新增五项 PostgreSQL 17 测试，证明业务失败事务回滚后独立失败审计恰好一次、幂等并发序列化、最后系统管理员保护和组织同级冲突。
- 规模修复：拆分审计、组织冲突和 identity 回归测试；`test_identity_permissions.py` 从约 700 行降至 461 行，未改变断言行为。
- Task 3 历史 TDD 证据归档：固定角色与用户管理首次聚焦测试为 `7 failed`，实现后 `7 passed`；并发管理员保护补测首次 `3 failed, 7 passed`，加 PostgreSQL advisory transaction lock 后 `10 passed`；相关 identity 回归最终 `42 passed`，当时未验证真实 PostgreSQL 并发，本轮 R7 已补齐。
- Task 4 历史 TDD 证据归档：组织合同首次 `6 failed`，基础实现后聚焦 `41 passed`；锁顺序、唯一/外键竞态和非法环补测分别先失败后通过，审查后聚焦 `64 passed`、完整后端 `90 passed`；当时仅 recording-session/SQLite 覆盖，本轮 R7 已补齐真实 PostgreSQL 并发。
- 非规范证据处置：上述两份 `.superpowers/sdd/task-3-report.md`、`task-4-report.md` 的唯一 RED/GREEN、Review 和未验证项已完整迁入本节；文件按项目资产基线删除，Git 历史仍可追溯。
- 最终复审：Critical 0、Important 0；Minor 仅提示 `0002` 已接近规模上限，后续数据库变化必须新增 revision，以及 PostgreSQL 测试函数可在未来不损害可读性时继续缩短。
- 边界：未实现 TASK-003 的活跃故障停用保护，未进入 TASK-004/RAGFlow，未增加兼容层、通用抽象或生产依赖。
- 结论：DEV-001 内部 Review 门禁通过，可形成书面审核请求；TASK-002 是否接受仍由 DEV-002 决定。

## TASK-002 集成基线同步复审（2026-07-16）

- 自查发现：首轮证据 HEAD `ab67bcdff42d64ba739571515df4e6faed158d32` 与集成分支分叉，merge-base 仍为被拒候选 `cfb8ed9`；模拟合并产生治理台账、`main.py` 和 CR-038 删除文件的冲突，因此原审核请求不可用于创建正式 PR。
- 修正：将最新集成基线 `ac767c83128cb89ceea8e28c518be0adfbe1984c` 作为第二父提交合入。TASK-002 代码和已同步后追加的任务证据采用任务分支版本；`workflow/STAGE_APPROVALS.md` 采用集成分支版本。
- 边界检查：CR-037/CR-038 审批和回滚历史保留；`STAGE_APPROVALS.md` 不再出现在任务差异中；依赖继续阻塞。
- 合并检查：集成分支成为任务分支祖先，ahead/behind 为 `19/0`；`git merge-tree --write-tree` 只返回结果树，无冲突。
- 差异检查：相对集成分支仅恢复 TASK-002 设计、契约、迁移、后端实现、测试和本任务证据；未引入 TASK-003/TASK-004 业务实现。
- 复验：完整后端 `125 passed, 5 skipped`；真实 PostgreSQL `5 passed`；迁移、Compose 实际状态、容器健康和 `/healthz` 通过。
- 同步验证候选：`4c111d0243d947a32d555bd48b1b72cab552bac4`。
- 结论：分支同步阻断和内部 Review 门禁均已关闭；正式台账回填后可重新请求 DEV-002 审核。

## TASK-002 / CR-036 R8 三轮复审（2026-07-17）

- 审查范围：`60c71dd5ab7588006ee16d794b03bef493fb3c72..73030f83638b3b063db483029591720bf65aac21`，只含 TASK-002 契约、迁移、身份/审计实现及测试。
- Important 1：`0002` 不再生成 `LEGACY_*`；不可映射角色和目录外权限会中止迁移；升级后精确四角色/33 权限，系统管理员拥有全部 33 项，非固定角色不参与运行时授权。
- Important 2：用户查询改为认证后按 `user_management.view_all` 决定本人或全量范围；普通用户查看他人返回稳定 403。
- Important 3：脱敏规则覆盖密码确认/数字后缀、复数 Cookie 和附件载荷上下文，同时保留普通内容和 Token 统计字段。
- Important 4：`get_db` 负责异常回滚；SQLAlchemy 与未知异常处理器返回稳定正文，受保护写在独立事务持久化一条失败审计；异常原文、SQL、令牌和附件正文不进入响应或日志。
- 测试隔离：Alembic 仅在根日志器无既有 handler 时加载文件配置，程序化迁移不再删除 pytest 捕获 handler 或禁用审计 logger。
- Minor 1 处置：历史同步提交 `0aac415d18aee256c237adb508d2ab24314a7486` 使用 `merge(task-002)`，不符合现行允许类型。该提交已推送且承担双父历史，任务书禁止 force-push/历史改写；保留为治理债务并在台账明确，R8 新提交使用允许的 `fix(task-002)`，后续只使用获准类型。
- Minor 2 处置：`0001` 是已发布且远端使用的不可变基础 migration；其 `upgrade()` 仅声明创建 TASK-002 基础表，职责已在 revision 文档和本记录说明。按获批设计不得改写 `0001`，所有修复集中在 `0002`，未来数据库变化必须新增 revision。
- 三轮结论：第一轮修复旧契约和测试夹具不一致；第二轮完整 Python/编译/静态检查通过；第三轮 PostgreSQL、迁移、固定目录、Compose 和 HTTP 通过。最终 Critical 0、Important 0，无新增阻断 Minor。
- 边界：未新增生产依赖、兼容层、通用框架或 TASK-003/TASK-004 实现；测试夹具改用正式固定角色，保留非固定角色不得授权的负向用例。
- 结论：DEV-001 内部 Review 门禁通过，可向 DEV-002 提交精确远端 HEAD 复审；DEV-002 批准和后继正式 PR/合入仍是外部门禁。

## TASK-002 / CR-036 R9 脱敏复审（2026-07-17）

- 审核输入：DEV-002 对 R8 代码候选 `73030f83638b3b063db483029591720bf65aac21` 的结论为 Changes requested，Critical 0、Important 1。复现表明 `newPasswordConfirmation` 与附件 `raw_content` 可原样进入失败审计。
- 根因：R8 使用枚举、前缀和后缀匹配；归一化后的 `new_password_confirmation` 没有由独立密码语义段识别。附件上下文仅枚举 `content/body/base64`，未知正文别名默认保留。
- 修复：`ac6947a642f00ba48aebcb80064f87fcc4c01ea8` 对归一化键按独立 `password/passwd/pwd` 语义段脱敏；附件上下文改为仅保留明确文件元数据，其余键（含嵌套/list）默认脱敏。
- 漏检改进：上一轮自查只覆盖已枚举字段，且端到端失败审计未注入驼峰密码别名和附件未知别名。本轮先写 2 个红灯用例，再在审计表 `metadata_json` 断言全部秘密缺失；后续同类审查必须包含规范化变体、未知别名与持久化断言。
- 验证：RED `2 failed`；定向 `19 passed, 1 warning`；Python 3.13 全量 `138 passed, 5 skipped, 1 warning`；`compileall`、`git diff --check` 通过。新增 Docker `test` 目标后，专用 PostgreSQL 17 集成 `5 passed, 1 warning`；默认生产镜像不含 pytest/httpx。
- 深度复盘与防复发：
  1. 规则设计错误：以枚举/前后缀代替语义模型。控制：密码键必须按归一化后的独立语义段判断，附件上下文采用允许元数据白名单而非正文别名黑名单。
  2. 测试设计错误：只验证实现者列出的正例。控制：每次安全脱敏变更必须覆盖命名风格、未知别名、嵌套/list 和不应脱敏的业务字段四类矩阵。
  3. 复查方法错误：三轮复查复用了同一套字段假设，缺少对抗性输入和持久化断言。控制：最终自查必须从攻击者可提交的原始 JSON 出发，并查询 `AuditEvent.metadata_json`，不能仅测 `sanitize_audit_metadata` 返回值。
  4. 环境设计错误：在 `internal: true` 网络内临时在线安装测试依赖。控制：依赖在构建阶段通过 `--group dev` 装入独立 `test` 镜像，运行时只连内部网络；生产目标保持最小化。
- 结论：DEV-001 内部复核未发现新的 Critical/Important；仍需 DEV-002 复审，TASK-002 未验收、未集成。

## TASK-002 / CR-036 R10 审计标量脱敏复审（2026-07-17）

- 审核输入：DEV-002 的 R9 补充复现指出 `newpassword`、`attachment_payload` 标量、`attachments` 标量列表和 `uploadData` 会泄漏到失败审计；Critical 0、Important 1。
- 根因：R9 的白名单逻辑只在 `dict` 分支生效；标量/list 分支没有依据继承的附件 context 执行默认脱敏。密码检查只按分隔后语义段判断，遗漏紧凑命名。
- 修复：`b4d451009d1deb9dbe3286f5bff4db9414ef4aee` 让附件 context 在标量与列表分支生效；纯标量列表整体替换为 `[REDACTED]`，含字典的混合列表逐项处理，且仅明确元数据白名单字段保留标量。紧凑密码后缀覆盖 `newpassword` 与 `userpassword`。
- 防复发：安全复审矩阵固定包含附件标量、标量列表、混合 list/dict、驼峰别名、紧凑密码键以及 SQLite 失败响应和持久化 `AuditEvent.metadata_json` 两层断言；任何新增附件别名必须先以红灯覆盖三种载荷形态。
- 验证：RED `2 failed`；定向 `21 passed, 1 warning`；Python 3.13 `140 passed, 5 skipped, 1 warning`；compileall、diff check、真实 PostgreSQL 17 `5 passed, 1 warning`、Compose 和 HTTP `/healthz` 均通过。
- 结论：DEV-001 内部复审 Critical 0、Important 0；仅可请求 DEV-002 复审，未获得批准前不创建正式 PR、不合入、不解锁依赖。

## TASK-002 / CR-036 R11 语义敏感键复审（2026-07-17）

- 审核输入：DEV-002 R10 指出 `binaryAttachment`、`uploadedFile`、`sessionCookieValue`、`passwordvalue` 可原样进入失败审计；Critical 0、Important 1。
- 根因：`is_attachment_context()` 只接受附件语义处于键首，`is_sensitive_key()` 只覆盖不对称枚举/后缀；归一化后的键虽含独立敏感段，却没有统一分类。
- 修复：`ea4338bad15f16048226a329801d3144b367909e` 将归一化键拆为完整段，附件段可出现在键首、键中或键尾；敏感段统一处理。紧凑规则限定为已定义敏感前后缀及 `value/hash/confirmation` 复合，不使用任意子串；Token 统计字段显式保留。
- 复查：直接与持久化两层覆盖键首、键中、键尾、附件标量、列表、混合结构、紧凑密码、Cookie、Token 以及业务反例。`profile` 不会因包含 `file` 字符串而误命中。
- 边界与风险：未知额外字段默认脱敏未实施；当前结论只覆盖已知敏感语义别名，不声称识别任意秘密载荷。该残余风险已记录，需独立 CR 决定可观测性与安全取舍。
- 验证：RED `2 failed`；定向 `23 passed, 1 warning`；Python 3.13 `142 passed, 5 skipped, 1 warning`；compileall、diff check、PostgreSQL 17 `5 passed, 1 warning`、Compose 和 `/healthz` HTTP 200 通过。DEV-001 内部复审 Critical 0、Important 0；仍待 DEV-002 复审。

## TASK-004 DEV-001 三轮独立复审（2026-07-20）

- 审查对象：`codex/task-004-ragflow-infra` 相对 `origin/codex/stage-05-integration@b29c69d13c3d1c81f01023152eabf0c0f2d02741`；证据提交前功能候选 `ac8c007730d8e947c5687380e4583e8b23d2cce1`。
- 第一轮 Standards：核对 `AGENTS.md`、任务书 v1.3、确认设计和实施计划；镜像固定、回环端口、独立网络/账户/卷、健康检查、秘密样例和任务边界一致。未新增依赖、迁移、业务 API、TASK-005 代码、兼容层或通用抽象；Critical 0、Important 0、Minor 0。
- 第二轮 Spec/失败路径：逐项核对 FR-002、NFR-003/005/007、AC-009/029/033 与 CR-028；Docker 不可用、健康超时、Elasticsearch 版本错误、缺失 RepoDigest、网络成员/端口泄漏、重启重建和探针丢失均明确失败。修复了验收脚本的摘要数组显示、凭据命令参数警告、多层 SQL/JSON 引号和 PowerShell stderr 误判；完整矩阵复跑通过。Critical 0、Important 0、Minor 0。
- 第三轮完整 diff：候选只包含 TASK-004 设计/计划、`codebase/infra/ragflow/`、环境样例、运行手册及正式证据；没有后端领域代码、前端、原型、Alembic 或 TASK-005 实现；`git diff --check` 通过。Critical 0、Important 0、Minor 0。
- 真实证据：Python 3.13 `5 passed, 1 warning`；两套 Compose config 通过；5 容器 healthy；Web 200；Elasticsearch 8.11.3；内部依赖 0 宿主端口；四存储 restart 持久化通过且容器重建数为 0。
- 风险：首次拉取仍依赖外部镜像源可用性；本地端口可能冲突，须使用环境覆盖；完整灾难恢复演练按任务书延后 TASK-011。日志和证据未记录真实秘密。
- 当前结论：DEV-001 自审通过，但不等于正式批准。指定审核者 DEV-002 尚未审核 PR #27 的最终精确 HEAD；TASK-005 在 TASK-004 正式集成并完成合并后验证前继续锁定，Stage 6 禁止进入。

### TASK-004 PR #27 R1 Changes requested 与 DEV-001 修正复查

- 外部审核：DEV-002 对精确 HEAD `8b628fcfbf80fb6490d8d3dd5257feafba9d1595` 给出 Critical 0、Important 3、Minor 0；阻断为缺少 9380 API 契约、MinIO 绕过 S3 API 直接读写 `/data`、镜像只检查 RepoDigest 存在而未匹配获批 SHA-256。
- 第一轮 Standards：修正功能提交 `f87a0c309c322f9accedcaea4a80aed84483b0e7` 仅触及 TASK-004 验证、回归契约、既有计划/手册；API 使用稳定版本端点，MinIO 凭据仅在容器内展开，摘要使用已核验的 5 个精确值；Critical 0、Important 0、Minor 0。
- 第二轮 Spec/失败路径：API 同时断言 target 9380、HTTP 200、业务 code/message 与 v0.25.6；完成前矩阵发现容器 healthy 后 API 仍可能短暂关闭，已在 `ba7e13f2b585f872ca811e98b50c09e25020fba5` 增加 60 秒有限重试并以重启后立即探测复现通过；MinIO 随机 bucket/object 经 S3 写入、重启、回读、清理；摘要缺失、检查失败或不匹配均返回非零，摘要突变测试通过；Critical 0、Important 0、Minor 0。
- 第三轮完整 diff：相对基线只新增一个 TASK-004 审核回归脚本并原位修改两个验证脚本、实施计划、运行手册和正式台账；没有 TASK-005、后端领域代码、迁移、前端、生产依赖、兼容层或通用抽象；完整矩阵与 `git diff --check` 通过。Critical 0、Important 0、Minor 0。
- 结论：三项已在本地证据中关闭，但新 HEAD 会使旧审核失效；必须推送同一 PR #27 并由 DEV-002 重新审核精确 HEAD。当前不得请求 Merge 授权，不得解锁 TASK-005，Stage 6 仍禁止进入。

### TASK-004 PR #27 R2 Changes requested 与 DEV-001 修正复查

- 外部审核：DEV-002 对精确 HEAD `6c6fda004f806f8b72eddaad64aac419b78a7a6f` 给出 Critical 0、Important 4、Minor 2；阻断涉及实际 Compose/运行镜像身份未绑定、Runbook 未显式传 `EnvFile`、Web 无有限超时、缺少日志/秘密扫描与结构化执行证据；Minor 为失败探针被清理和 PR 标题不合规。
- 第一轮 Standards：修改仅位于 TASK-004 既有验证、测试、实施计划和运行手册；未增加依赖、兼容层、抽象层、业务代码或 TASK-005 实现。Runbook 改为唯一显式本地 `EnvFile`，PR 标题规则同步为 `[TASK-004] feat: ...`。Critical 0、Important 0、Minor 0。
- 第二轮 Spec/失败路径：错误 Compose 镜像覆盖、错误 digest、运行镜像 ID 不一致、Web/API 超时、依赖连接失败、日志秘密命中和持久化不一致均返回非零。注入持久化不一致后四项探针保留；历史日志假阳性通过当前执行窗口约束修复，但窗口内任何匹配仍零容忍。Critical 0、Important 0、Minor 0。
- 第三轮完整 diff/运行态：Python 3.13 `5 passed, 1 warning`，compileall、两套 Compose config、静态契约、5 容器健康、Web/API 200、网络隔离、四存储 restart、两类镜像负向测试、失败探针保留、日志/秘密扫描和 `git diff --check` 通过。仅 TASK-004 范围，无无关修改。Critical 0、Important 0、Minor 0。
- 结论：本地三轮复查通过，不等于 DEV-002 正式批准。新精确 HEAD 必须在同一 PR #27 重新审核；复审通过前不请求 Merge 授权、不解锁 TASK-005，Stage 6 仍禁止进入。

### TASK-004 PR #27 R3 Changes requested 与 DEV-001 修正复查

- 外部审核：DEV-002 对精确 HEAD `601d54d2427302999c7bc10ac5beec3ac0565501` 给出 Critical 0、Important 2、Minor 0；阻断为 Runbook 的隔离脚本参数不可执行，以及持久化探针清理失败仍可能输出 PASS。
- 第一轮 Standards：修正仅涉及 TASK-004 既有 Runbook、验证脚本、回归测试和正式证据；没有新增依赖、兼容层、抽象层、业务代码、迁移或 TASK-005 实现。Critical 0、Important 0、Minor 0。
- 第二轮 Spec/失败路径：Runbook 命令与隔离脚本 AST 参数签名一致；调用 Compose 的脚本仍绑定本地 EnvFile。持久化验证只有在四类探针及临时资源清理全部返回 0 后才输出 PASS，任一清理失败抛错且不会产生成功结论。Critical 0、Important 0、Minor 0。
- 第三轮完整 diff/运行态：功能提交 `dc909fff1c8260f2f8a50670192761572cdfb76b`；静态 RED/GREEN、PowerShell 语法、Compose 契约、5 容器健康、Web/API 200、网络隔离、四存储 restart 和严格清理通过；`git diff --check` 通过。Critical 0、Important 0、Minor 0。
- 结论：本地复查关闭本轮两个 Important，但不等于 DEV-002 正式批准。必须推送同一 PR #27 的新精确 HEAD 并重新审核；此前不请求 Merge 授权、不解锁 TASK-005，Stage 6 仍禁止进入。

### TASK-004 PR #27 R4 Changes requested 与 DEV-001 修正复查

- 外部审核：DEV-002 对精确 HEAD `6cd29f158b2c03f61c5b21a7e9bf99d30ec17a34` 给出 Critical 0、Important 2、Minor 0；阻断为真实运行环境文件契约在设计/计划中不一致，以及清理失败只做静态检查、未证明非零退出和无 PASS。
- 第一轮 Standards：设计、计划与 Runbook 统一为真实运行使用忽略的 `.env.local`；调用 Compose 的运行脚本显式传 `-EnvFile`，仅静态 `config --quiet` 使用 `.env.example`。没有生产依赖、兼容代码、业务代码、迁移或 TASK-005 实现。Critical 0、Important 0、Minor 0。
- 第二轮 Spec/失败路径：功能提交 `29180e285767cbffb9d694cd1834f04514d2cc18` 引入最小外部命令边界；四类代表性清理以子进程调用固定退出码 42 的假 Compose 命令，逐项断言非零退出且输出不含 PASS。真实持久化重启和成功清理继续通过。Critical 0、Important 0、Minor 0。
- 第三轮完整 diff/运行态：环境与清理行为契约、PowerShell 语法、Python 3.13、compileall、Compose config、5 容器健康、Web/API 200、网络隔离、四存储 restart 和 `git diff --check` 均通过；变更限制在 TASK-004 设计、计划、基础设施验证/测试和正式证据。Critical 0、Important 0、Minor 0。
- 结论：本地三轮复查关闭两项 Important，但不等于 DEV-002 正式批准。推送后必须按 PR #27 新完整 HEAD 重新审核；此前不请求 Merge 授权、不解锁 TASK-005，Stage 6 仍禁止进入。

### TASK-004 PR #27 R5 Changes requested 与 DEV-001 修正复查

- 外部审核：DEV-002 对精确 HEAD `a5ac8490bf678ea03efc702052f7f1edecff182b` 给出 Critical 0、Important 1、Minor 0；阻断为任务书 Markdown 列表中的真实运行命令未被环境契约解析。
- Standards/Spec：功能提交 `314b46d3efdc7af0d13c671fadd41be7bb3900d1` 仅修改现有审核脚本。任务书验证列表中的反引号命令与可执行代码块被检查；静态 config、普通说明及明确禁用/错误示例不误报。Windows PowerShell 5.1 兼容性、函数尺寸和修改范围通过。
- RED/GREEN：旧检查器对任务书 `.env.example` 运行变异错误 PASS；修正后非零拒绝。独立首审发现禁用示例误报 1 个 Important，补充外部行为 RED 后修复；累计复审 Critical 0、Important 0、Minor 0。
- 结论：本地复查通过不等于 DEV-002 批准。新 HEAD 推送后必须在同一 PR #27 重新审核；此前不请求 Merge 授权、不解锁 TASK-005，Stage 6 仍禁止进入。
## TASK-004 PR #27 R6 修复自查（2026-07-22）

- 外部审核：精确 HEAD `80b40182efa49033ee561f34fd6e078b3469a733` 为 Changes requested；唯一 Important 是真实验证脚本仍默认 `.env.example`。
- Standards：两个运行脚本现在默认 `.env.local`，静态 Compose 检查仍独立使用 `.env.example`；未改变 Compose 服务、镜像、端口、卷或网络。
- Spec：环境文件缺失检查位于 Docker 调用前；回归通过 AST 验证默认参数，并对子进程执行缺失文件路径，验证非零退出及明确错误。
- 范围：仅两个 TASK-004 运行脚本及既有审核回归；无依赖、兼容层、抽象层、业务代码、迁移、TASK-005 或无关修改。
- 本地结论：Critical 0、Important 0、Minor 0；该结论不替代 DEV-002 对新精确 HEAD 的正式审核。

## TASK-004 PR #27 合并后治理核查（2026-07-22）

- 开发审核：DEV-002 对精确 HEAD `76732606412d71239d302e4e9e5a0da6b364fd70` 给出 Approved；无未关闭 Critical/Important。
- Merge：项目负责人授权同一 PR/HEAD；DEV-002 作为非任务作者执行 Merge Commit `87e8e3c0aab62ee9105bf3807b23fcf44ac15137`。
- 合并关系：源 HEAD 是 Merge Commit 的第二父提交；最新集成基线仍包含该 Merge Commit。
- 合并后核查：任务边界、`.env.local` 运行契约、Compose YAML、Python 3.13、PowerShell 契约、真实 Docker 健康/隔离/持久化均通过。
- 治理 diff：仅任务书、CHECKPOINTS、SELF_TEST、CODE_REVIEW、COMMIT_LOG 与 DEV_TO_PM_HANDOFF；无代码、测试、数据库、基础设施、部署配置或产品基线修改。
- 结论：治理检查 Critical 0、Important 0、Minor 0；需项目负责人确认本治理 PR 精确 HEAD，随后由非 PR 作者合并。

## TASK-003 本地开发候选独立自查（2026-07-22）

- 审查对象：`b29c69d13c3d1c81f01023152eabf0c0f2d02741..4877dcdc301b97d884a43883a5584fdee1d28c41`，其中第二父为已正式集成的治理/基础设施基线，TASK-003 自有差异限定于 maintenance、设备停用保护、`0003_task003`、相关测试、API/Data Model 契约和实施计划。
- Spec：故障上报、DIRECT/ADOPTED 开始维修、人工最终维修结果、结构化案例查询、活跃故障停用保护均与任务书和冻结 API 契约一致；RAGFlow/Agent 生成逻辑不在范围内。
- Standards/Security：权限、幂等、成功/失败审计、附件引用边界、诊断草稿字段白名单、时区、SQL 通配符字面匹配、事务行锁和唯一约束均有直接测试。
- 数据库：单一线性 Alembic head；downgrade 只移除 TASK-003 五表并明确具有破坏性；专用 PostgreSQL 17 测试通过，未接触平台或生产数据。
- 范围：无新增生产依赖、兼容代码、通用抽象层、前端、RAGFlow 调用、TASK-005/006/008 实现或无关格式化。
- 本地结论：Critical 0、Important 0、Minor 0。该结论不替代 DEV-002 对推送后完整精确 HEAD 的正式审核。

## TASK-003 PR #32 合并后治理核查（2026-07-22）

- DEV-002 Review：对精确 HEAD `8960b5d8ab1e7073036c6151744233e26c15c9e9` 给出 Approved，Critical 0、Important 0、Minor 0；审核后 HEAD 未变化。
- 授权/Merge：项目负责人授权 PR #32 同一精确 HEAD；DEV-002 作为非任务作者执行 Merge Commit `51337db767eb94051f78a5c537a3ff48d428a742`。
- 合并关系：Merge Commit 第一父为授权时目标基线 `f135997a6ecc009de75735b673499b475615a717`，第二父为获批源 HEAD，无错误目标或替换提交。
- 合并后证据：Python 3.13、专用 PostgreSQL 17、迁移单 head、平台/RAGFlow Compose、compileall 与差异检查均通过。
- 治理边界：本收尾仅更新任务书、FCP、自测、评审、提交日志、交接与状态台账；无 `codebase/`、测试、数据库迁移、基础设施、部署或运行配置修改。
- 结论：治理核查 Critical 0、Important 0、Minor 0；等待项目负责人确认本纯治理 PR 的精确 HEAD，随后由非 PR 作者合并。
