# 代码评审

## TASK-012-API-001 合并后治理检查（2026-07-30）

- 审核与授权：DEV-002 对 `c1273fd01e5ec91b2de3af59aab371844d228cd6` 正式批准；项目负责人授权后，DEV-002 执行 Merge Commit `274673b72d5201986ffee77b038f516022cd174d`。
- 集成结论：PR 目标分支、获批 HEAD、双亲、祖先关系、merge-tree 和工作树结果一致；无 Critical、Important 或 Minor 集成阻断项。
- 边界：API-001 已集成，但本检查不批准 API-002—007、TASK-012 前端、Stage 6/7/8 或新的公开 API 范围。

## TASK-012-API-001 独立复审补充（2026-07-30）

- 复审范围：API-001 实现提交 `7ba0e5e77e6a784f0dd6a0622c91ebce691e00a1` 及测试补充提交 `44992b5b34f6a2c77378383a363bfb2a3f86fd25`。
- 独立结论：未发现 Critical、Important 或 Minor 阻断项。补充测试直接覆盖已完成故障排除活动待办，以及相同 `submitted_at` 时按 `id ASC` 的稳定次级排序。
- 验收证据：定向 `3 passed, 2 warnings`；全量后端 `319 passed, 13 skipped, 2 warnings`；Python 3.13 `compileall`、Compose `config --quiet` 和 `git diff --check` 通过。
- 正式门禁：本结论不替代 DEV-002 对 PR #71 最新精确 HEAD 的正式审核，不构成 Merge 授权、集成或下游解锁。

- 状态：TASK-001 已完成独立审查；TASK-002 已获 DEV-002 正式批准并由 DEV-001 手动合入 PR #20，技术验证完成；合并后治理收尾已通过 PR #25 合入，TASK-002 前置已解除。
- 范围：已审查 TASK-001 平台运行基线、TASK-002 CR-036 修复候选及其正式集成，以及 TASK-006 已验证的非数据库切片；后续任务仍须逐任务交叉审核。
- 评审门禁：每个有意义的实现切片都必须完成规格符合性、质量评审、测试，并具备可追溯的功能/页面检查点。

## TASK-012-API-001 自查（2026-07-30）

- 审查范围：`866875d4071a725d9c780f535d6be10e1202ba4e..7ba0e5e77e6a784f0dd6a0622c91ebce691e00a1`。
- 规格符合性：三个只读 Workbench 路由、`workbench:view` 门禁、活跃故障范围、服务器端筛选/排序、空态、快捷事项和稳定校验错误均已写入 `API_SPEC.md` 并有定向测试。
- 边界：不返回描述、附件、组织快照、提交人、维修记录、审计或凭据；无迁移、生产依赖、Compose、兼容层或无关代码变更。
- 当前结论：DEV-001 自查未发现阻断项；这不是 DEV-002 正式审核，也不构成合并或依赖解锁批准。

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

## TASK-007 PR #40 代码审核与合并后技术核查（2026-07-23）

- DEV-001 审核：对精确 HEAD `fcd643ab0b0e33a585e3be6ec0b0036a611059c4` Approved；此前 HEAD 的 Changes requested 不适用于当前 HEAD。
- 合并：PR #40 已实际合入 `codex/stage-05-integration`，Merge Commit `bf842626987148575173c6cf3f34970fc496ad7c`；第二父为审核源 HEAD，第一父为 `fdec916fad943acb8ad62a1cf5bc3ce8f770cc8d`。
- 技术核查：后端 `228 passed, 10 skipped, 2 warnings`；PostgreSQL 17 真实 PostgresSaver `1 passed, 1 warning`；compileall、Compose 配置、API 镜像构建、容器健康、`/healthz` HTTP 200、merge-tree 与 diff-check 均通过。
- 治理结论：项目负责人已正式追认 PR #40、源 HEAD、Merge Commit 及合并结果；PR #41 治理收尾已合入，TASK-007 治理闭环完成并可按依赖矩阵解锁下游；Stage 6 仍未批准。

## TASK-008 DEV-002 开发者自查（2026-07-23）

- 审查对象：`codex/task-008-fault-metric-agents` 相对 `origin/codex/stage-05-integration@78e9dfb` 的完整差异。
- Standards/Spec：故障草稿只采集字段并经人工确认后调用外部业务写入；指标仅来自固定 40 项目录且最多五项；非法维度和受控服务失败明确拒绝/降级；健康分读取器不计算、不缓存、不伪造分值。
- 安全/边界：使用现有 `equipment:read` 权限保护目录和查询 API；无直接数据库、SQL、文件系统、模型计算指标、诊断 Agent、TASK-005 或新生产依赖。
- 验证：专项 `12 passed, 2 warnings`；全量后端 `240 passed, 10 skipped, 2 warnings`；`git diff --check` 通过。Critical 0、Important 0、Minor 0（DEV-001 正式复审尚未开始）。
- 门禁：PR #43 已创建并 Ready；当前精确 HEAD 变化后旧审核请求失效。等待 DEV-001 对新精确 HEAD 复审，未请求 Merge 授权。

## TASK-008 DEV-001 P1 修复复查请求（2026-07-23）

- 原审核：PR #43 / HEAD `4e6aec342849f60fdd281c083f3a21147bc7d866`，两项 P1：故障提交未接入业务 API；健康分读取器未接入可执行 API/工具/页面边界。
- 修复候选：HEAD `24153155da11dac0579466c05c8a04c7371e8904`；同一 PR 新增业务提交 API、受控健康分 API 和 `get_health_score` 工具白名单。
- 新验证：专项 `14 passed, 2 warnings`；全量 `244 passed, 10 skipped, 2 warnings`；compileall、JSON 解析、diff-check 通过。
- 当前门禁：请求 DEV-001 绑定新精确 HEAD 复审；未批准、未集成、未申请 Merge 授权。

## TASK-008 幂等冲突 P1 修复复查请求（2026-07-24）

- 阻断修复：`POST /api/agent/fault-reports/submit` 现在映射 `IdempotencyKeyReused` 为 `409 IDEMPOTENCY_KEY_REUSED`。
- 证据：同请求重放、冲突请求、无重复故障记录和无重复成功审计回归均通过；Agent 专项 `15 passed, 2 warnings`，全量 `245 passed, 10 skipped, 2 warnings`。
- 当前门禁：同一 PR 等待 DEV-001 对本次新精确 HEAD 复审，未请求 Merge 授权。

## TASK-008 不完整草稿 P1 修复复查请求（2026-07-24）

- 阻断修复：确认提交捕获 `MissingFaultFieldsError`，稳定返回 `422 FAULT_DRAFT_INCOMPLETE` 与字段映射。
- 证据：不完整请求不产生故障记录、成功审计或成功幂等响应；补齐同 Key 请求可成功；专项 `18 passed, 2 warnings`，全量 `246 passed, 10 skipped, 2 warnings`。
- 当前门禁：等待 DEV-001 绑定新完整 HEAD 复审，未请求 Merge 授权。
- 当前门禁：等待 DEV-001 绑定新完整 HEAD 复审，未申请 Merge 授权。

## TASK-008 治理证据校准复查请求（2026-07-24）

- 复查对象：PR #43，代码与证据候选 HEAD `ad50034ccb18422ac9a9c88325b9f0c4e9cb22dc`。
- 校准内容：`workflow/state.json`、FCP、SELF_TEST、CODE_REVIEW、COMMIT_LOG、任务书约束与 `workflow/DEV_TO_PM_HANDOFF.md` 统一记录该 HEAD；专项结果统一为 `18 passed, 2 warnings`，全量后端为 `246 passed, 10 skipped, 2 warnings`，不再保留本轮 `pending commit`。
- 门禁：请求 DEV-001 在同一 PR 对最新远端精确 HEAD 重新审核；当前不得请求 Merge 授权、合并、解锁下游或进入 Stage 6。

## TASK-008 合并后集成检查（2026-07-24）

- 审核与授权：DEV-001 已批准 PR #43 精确 HEAD `19eaf1f213c50471f93b4e09e17df57bbeb1987b`；项目负责人授权手动 Merge Commit；DEV-001 作为非任务开发者执行合并。
- 结果：Merge Commit `84ac8815cab403cb71a86230b4f705944bb5f6d2` 双亲、祖先关系和 merge diff check 正确；合并后后端 `246 passed, 10 skipped, 2 warnings`，14 项原型静态回归、compileall 和 JSON 解析通过。
- 当前结论：项目负责人已确认 PR #45 精确 HEAD `883053f59890272ef1dbb311b8d47bce8aace45c`；DEV-002 已以 Merge Commit `997e50e10a7964b60fc8d9b4357c6274df8f0e97` 合入，治理闭环完成。TASK-008 可按依赖矩阵解锁下游，Stage 6 仍禁止。

## TASK-005 PR #37 合并后 DEV-001 集成验证（2026-07-24）

- 审核与授权：DEV-001 已对获批 HEAD `cac10a06d2ef48914c14fb7ad955cedb36878acd` 重新 Approved；项目负责人针对 PR #37、该 HEAD 和目标基线 `ca2a07f5f9f19620568cc75f74c97a2d10ed98d3` 授权手动 Merge Commit。
- 结果：DEV-001 以 Merge Commit `58fc0b12db1298333eef52c8720ec7d3d5e4846c` 合入；双亲、祖先关系、结果树、JSON 和差异检查通过。
- 当前结论：项目负责人已确认 PR #47 精确 HEAD `09f9701ee2ed97358b37cfd60ae79f12358acdcb`；DEV-002 已以 Merge Commit `6763f1e7199765c08303aa567c3aed40210f7cf7` 合入，TASK-005 治理闭环完成，可解锁 TASK-009，Stage 6 仍禁止。

## TASK-009 DEV-002 开发者自查与 DEV-001 复审请求（2026-07-24）

- 候选：PR #49，完整 HEAD `a5c5d20ef1936f7690e9fb32d332195561257609`；代码提交 `f78deace39fde732bcea7ec36f9a3f5eea79dfc1`，生产接入提交 `ab54e7663d0ae65205236463bcd92b3a868eec24`，分支 `codex/task-009-guidance-diagnosis`，目标 `codex/stage-05-integration`。
- 任务边界：操作指引两次定向检索/人工降级；维修前诊断报警码、证据门槛、采纳/直接开始及 8/24/4 上限；通过外部回调区分 PostgreSQL 历史案例和 RAGFlow 知识引用。
- 自查证据：Agent API 与 Runtime `8 passed, 2 warnings`；完整后端 `293 passed, 12 skipped, 2 warnings`；静态 Agent 检查、compileall、`git diff --check` 通过。
- P1 修复：新增 `/api/agent/operation-guidance` 和 `/api/agent/fault-diagnosis`；历史案例通过 TASK-003 查询，知识引用通过 TASK-005 adapter，诊断达标创建既有 `DiagnosisDraft`，后续由 `/start-repair` 采纳。
- 代码审查重点：请 DEV-001 绑定该精确 HEAD 检查生产执行边界、任务范围、权限/安全、失败降级、外部检索边界和测试证据。当前未请求 Merge 授权；任何 Critical/Important 在同一 Draft PR 修复后重新审核。
- 未验证：Docker/PostgreSQL/RAGFlow/LLM 真实联调待 DEV-001 专用环境核验；在此之前不得批准、集成、解锁下游或进入 Stage 6。

## TASK-009 DEV-001 第二轮 P1 修复复查请求（2026-07-24）

- 原审核：PR #49 / HEAD `15a5947f95d52a0044d4ee2978da09cc2509e41e`，P1 为故障诊断 API 信任客户端回传 `session`，可伪造 READY 状态、根因和方案，并在完成会话重放时重复创建草稿和成功审计。
- 修复提交：`8d4d4c48aaa4ee39d01be4cbb5cb18de374a784c`。
- Standards/Spec 自查：客户端不再提交完整诊断状态；服务端 `DiagnosisDraft` 保存受控 `_session` 和 `_owner_user_id`，后续步骤以 `diagnosis_draft_id` 读取并校验归属、故障和状态。诊断达标后仍使用既有 `DiagnosisDraft` 与 `/start-repair` 的 `ADOPTED` 路径，未新增迁移、生产依赖、兼容层或通用抽象。
- 回归证据：伪造 `session` 请求 422；越权草稿请求 403；幂等重放返回原响应、同 Key 不同体返回 409；READY 后重复请求不新增 `DiagnosisDraft` 或 `agent.fault_diagnosis.ready` 审计；最终维修采纳路径通过。
- 验证：Agent/Runtime/Maintenance 聚焦回归 `49 passed, 2 warnings`；完整后端 `293 passed, 12 skipped, 2 warnings`；14 项原型静态回归、compileall、JSON 解析和 `git diff --check` 通过。
- 当前结论：本地自查 Critical 0、Important 0；等待 DEV-001 对推送后的新完整 HEAD 复审。未请求 Merge 授权、未合并、未解锁 TASK-010/011，Stage 6 仍禁止。

## TASK-009 DEV-001 第三轮 P1 修复复查请求（2026-07-24）

- 原审核：PR #49 / HEAD `4b965715fe6fb6869c14da6b23f6b26479243595`，P1 为仅有 `intelligence:agent` 权限的用户仍可创建诊断草稿，且诊断上下文与知识数据集仍信任客户端字段，违反 AC-004/AC-037。
- 修复提交：`e0c058e182d7c29881c3de75403b2ef0eb648de7`。
- Standards/Spec 自查：故障诊断创建可采纳草稿需同时满足 `intelligence:agent` 与 `fault:repair`；`start` 请求只接受 `fault_report_id` 与报警码状态，设备型号、故障症状、描述均由服务端故障单和设备记录生成，知识数据集由 `fault_diagnosis` Agent 配置读取。未新增迁移、生产依赖、兼容层或通用抽象。
- 回归证据：仅有 `intelligence:agent` 的用户返回 403 且不创建草稿；伪造客户端上下文/数据集返回 422；成功路径检索问题与数据集绑定服务端事实和配置；READY 幂等、草稿越权、重放和最终 `ADOPTED` 采纳路径继续通过。
- 验证：故障诊断定向 `5 passed, 2 warnings`；Agent/Runtime/Maintenance 聚焦回归 `49 passed, 2 warnings`；完整后端 `293 passed, 12 skipped, 2 warnings`；14 项原型静态回归、compileall、JSON 解析和 `git diff --check` 通过。
- 当前结论：本地自查 Critical 0、Important 0；等待 DEV-001 对推送后的新完整 HEAD 复审。未请求 Merge 授权、未合并、未解锁 TASK-010/011，Stage 6 仍禁止。

## TASK-009 DEV-001 第四轮基线冲突修复复查请求（2026-07-24）

- 原审核：PR #49 / HEAD `3b8adf2f37e2490c7ec5695bd2e789dd9813fae8`，P1 为 CR-043 仅更新变更台账和 `workflow/state.json`，但 AC-037、SPEC/API 契约和需求追踪矩阵仍保留旧授权口径。
- 修复范围：同步 `01-requirements/PRD.md`、`SPEC.md`、`ACCEPTANCE_CRITERIA.md`、`REQUIREMENTS_TRACEABILITY_MATRIX.md` 与 `04-architecture-plan/API_SPEC.md`，明确当前设计不实现 `EquipmentGrant` 或设备/工厂行级授权隔离。
- Standards/Spec 自查：AC-037 现在验证授权详情保护，而不是设备对象级授权；API 契约要求故障诊断按服务端故障单、设备事实、Agent 配置和诊断草稿创建者隔离执行，且不把客户端上下文当作诊断事实源。
- 验证：`workflow/state.json` JSON 解析、`git diff --check` 与授权冲突词扫描通过；本次未修改 `codebase/`，未重跑后端测试。
- 当前结论：本地自查 Critical 0、Important 0；等待 DEV-001 对推送后的新完整 HEAD 复审。未请求 Merge 授权、未合并、未解锁 TASK-010/011，Stage 6 仍禁止。

## TASK-009 DEV-001 第五轮 P1 修复复查请求（2026-07-24）

- 原审核：PR #49 / HEAD `ef6bda4ff28147280868b4088ede72e39bebedb3`，P1 为生产应用工厂未装配 RAGFlow adapter，导致 TASK-009 API 真实部署中始终降级为知识服务不可用。
- 修复提交：`655d4a2309251fd0bd0ae874787e63b73f35effd`。
- Standards/Spec 自查：生产 `create_app()` 现在从 `RAGFLOW_BASE_URL`、`RAGFLOW_API_KEY` 和 `RAGFLOW_TIMEOUT_SECONDS` 构建 `RagflowAdapter + UrllibRagflowTransport`；操作指引与故障诊断共用 `app.state.knowledge_adapter`，继续保持 TASK-005 知识检索边界、TASK-003 历史案例边界和既有手动降级语义。
- 回归证据：应用工厂回归证明 adapter 自动装配；操作指引与故障诊断 API 回归使用真实应用工厂、真实 transport 和本地 HTTP RAGFlow stub，证明不依赖 `app.state` 手动注入或知识服务 monkeypatch。
- 验证：相关 `16 passed, 2 warnings`；Agent/Runtime/Maintenance 聚焦 `51 passed, 2 warnings`；完整后端 `296 passed, 12 skipped, 2 warnings`；14 项原型静态回归、compileall、JSON 解析和 `git diff --check` 通过。live-stack RAGFlow 用例因缺少专用环境为 `1 skipped`。
- 当前结论：本地自查 Critical 0、Important 0；等待 DEV-001 对推送后的新完整 HEAD 复审和真实 RAGFlow 联调。未请求 Merge 授权、未合并、未解锁 TASK-010/011，Stage 6 仍禁止。

## TASK-009 第六轮 P1 Compose 配置修复自查（2026-07-24）

- 审核反馈映射：PR #49 的 `a173233d39d752fe5f025d1423d2038c54b685ba` 在 Compose 环境下未将 RAGFlow 配置传入 `api`，使应用工厂 adapter 装配分支不可达。
- 修复边界：仅修改 API Compose 环境传递、安全环境模板和既有 Compose 契约测试；未改业务 API、数据库迁移、生产依赖、认证授权或 RAGFlow 服务部署。
- 回归：测试先在缺失 `api` 变量和缺失模板超时时失败；修复后相关 `18 passed, 2 warnings`、完整后端 `296 passed, 12 skipped, 2 warnings`、14 项原型静态检查、编译和差异检查通过。
- 残余风险：本机无 Docker，不能证明运行容器中的 `app.state.knowledge_adapter`、`/healthz` 或对真实 RAGFlow 的检索；DEV-001 必须在具备环境时独立验证。当前仍为 `Changes requested` 后的开发候选，未申请 Merge 授权。

## TASK-009 第七轮 P1 API 容器连通性修复自查（2026-07-24）

- 审核反馈映射：PR #49 的 `f920af89f7fbaefbb1f5547582ed4d44b44005ef` 在 Linux Docker 内缺少 `host.docker.internal` 映射，RAGFlow 地址无法解析，真实 adapter 检索不可达。
- 修复边界：仅为 API 复用已有 host 映射和 RAGFlow egress 网络，并扩展现有 TASK-005 live-stack 验证入口；未新增生产依赖、业务 API、数据迁移、权限规则或 RAGFlow 服务配置。
- 回归：静态契约覆盖 API 的 host 映射、egress 网络和容器探针；探针运行时执行 DNS 解析与有凭据的 HTTP 请求。相关 `18 passed, 2 warnings`、完整后端 `296 passed, 12 skipped, 2 warnings`、14 项原型静态检查、编译和差异检查通过。
- 残余风险：本机缺少 Docker/PowerShell，未实际运行 Linux 容器探针；DEV-001 必须重建 Compose 并验证 API 容器 `/healthz`、adapter 与真实检索。当前仍为 `Changes requested` 后的开发候选，未申请 Merge 授权。

## TASK-009 第八轮 P1 修复自查（2026-07-26）

- 审核反馈映射：PR #49 HEAD `cc643881c251bddc37bb4ae83564b7e14a79a853` 的 live-stack 探针将多行 Python 作为 `python -c` 原生参数，PowerShell/Docker 转换后引号丢失并产生 `SyntaxError`。
- 结论：旧静态测试只证明源码文字存在，未证明探针可执行；该反馈成立。修复移除源码参数传递，改为 API 镜像内可直接执行的模块入口。
- 验证证据：修复前新增用例 `2 failed, 1 passed`；修复后实际子进程探针、静态契约和 TASK-009 聚焦共 `20 passed, 2 warnings`，完整后端 `297 passed, 12 skipped, 2 warnings`，14 项静态回归、编译、JSON 与差异检查通过。
- 变更边界：仅新增一个探针模块、修改现有验证脚本和其回归测试；无依赖、迁移、兼容层、额外抽象或无关修改。
- 残余门禁：DEV-001 必须用 Windows PowerShell、Docker 和专用 RAGFlow Key 对 PR #49 新精确 HEAD 重跑完整 live-stack；在新审核前不申请 Merge 授权。

## TASK-009 第九轮 live Agent 验证自查（2026-07-27）

- 审核反馈映射：此前 live-stack 只直接验证知识服务层，未通过 TASK-009 生产 API 路由；因此不能证明 Agent 路由实际返回真实引用或在 RAGFlow 不可用时保留人工流程。
- 修复边界：扩展现有 opt-in live-stack 测试，不新增平行脚本或环境；成功路径走真实 RAGFlow、真实 PostgreSQL READY 文档与 `/api/agent/operation-guidance`，失败路径走同一路由和真实网络连接失败。
- 断言：成功路径要求 `QUESTIONING`、非空 chunk citation、引用文本包含唯一文档标记；失败路径要求 `UNAVAILABLE`、`manual_fallback=true`、无伪引用。
- 本地证据：相关 `7 passed, 1 skipped, 2 warnings`，完整后端 `297 passed, 12 skipped, 2 warnings`；live 项因缺少专用环境跳过，不误报为通过。
- 残余门禁：DEV-001 需在最终精确 HEAD 上实际运行完整 live-stack 后重新审核；当前不申请 Merge 授权。

## TASK-010 前端集成自查与复审请求（2026-07-27）

- 复审对象：PR #50，`codex/task-010-frontend-integration` → `codex/stage-05-integration`；开发者 DEV-002，审核者 DEV-001。最终复审必须绑定推送后的完整精确 HEAD。
- 范围核查：仅正式 `codebase/frontend/` 与 TASK-010 证据台账；不存在 `codebase/backend/`、迁移、部署、生产依赖、Stage 3 原型或 Agent 配置页修改。
- 契约与安全：客户端仅提交用户填写的输入和服务端签发的诊断草稿 ID；不传递或显示思维链；API 403 显示权限状态，503/运行时失败保留人工路径；采纳摘要仅显示症状、根因和关键证据。
- 交互核查：诊断按四阶段显示；操作指引引用可折叠；消息区独立滚动、输入区固定；Runtime SSE 展示服务端状态。
- 本地证据：前端 `22 passed`、生产构建和 14 项静态回归均通过，`git diff --check` 通过。真实浏览器/API 认证及 Docker/PostgreSQL/RAGFlow/LLM 联调待 DEV-001。
- 请求：请 DEV-001 对 PR #50 最终精确 HEAD 执行正式代码审核；本条不是 Merge 授权，审核通过前不得合并、解锁 TASK-011 或进入 Stage 6。

## TASK-010 Bearer 认证 P1 复审请求（2026-07-27）

- 反馈核验：API 客户端和 SSE 读取原先确实未发送 `Authorization`；后端正式业务、Agent 与运行事件路由使用 Bearer 会话认证，因此该 P1 成立。
- 修复审查：认证头只在 API 边界生成，并从现有 `sessionStorage.access_token` 登录态读取；JSON、POST 幂等键、PUT 配置保存和 SSE 都由相同函数覆盖。token 不写日志、不进入页面状态，也不在缺失时构造伪 token。
- 证据：JSON 与 SSE 均通过捕获实际 fetch 初始化参数验证 Bearer 值；API 专项 `10 passed`、前端全量 `23 passed`、构建、14 项静态回归、JSON 与 diff-check 通过。
- 请求：请 DEV-001 对本次推送后的 PR #50 完整精确 HEAD 重新审核。该请求不是 Merge 授权；审核前不得合并、解锁 TASK-011 或进入 Stage 6。

## TASK-010 登录与受保护路由 P1 复审请求（2026-07-27）

- 反馈核验：此前正式前端确实没有 token 写入点、登录入口或路由保护，`sessionStorage.access_token` 仅在测试中出现，P1 成立。
- 修复审查：`LoginPage` 仅处理用户名、密码、提交状态及通用失败提示；登录 API 成功后写 token。`RequireAuthentication` 是全局路由边界，保护除 `/login` 外的既有页面；API/SSE 使用相同会话源，登录请求显式不携带旧会话头。
- 安全与范围：没有把 token 写到 URL、日志、页面文本或全局 React 状态；不改后端认证、权限、API、依赖、迁移、部署、原型或业务页契约。
- 证据：API 专项 `11 passed`，交互测试覆盖重定向、登录写入和登录后 Bearer，前端全量 `26 passed`，构建、14 项静态回归、JSON 与 diff-check 通过。
- 请求：请 DEV-001 对本次推送后的 PR #50 新完整精确 HEAD 复审；这不是 Merge 授权，审核前不得合并、解锁 TASK-011 或进入 Stage 6。
## CR-048 治理候选合并后集成复核（2026-07-31）

- DEV-001 核验 PR #73 精确 HEAD `b4e28368c1294f30b80f4dd72187660eba06fc10`，目标 `codex/stage-05-integration`，并以 Merge Commit `8d9beaefe01baef38e54baecbe3426d9ab816623` 合入。
- 检查结论：PR 状态为 `MERGED`；双亲为 `274673b72d5201986ffee77b038f516022cd174d` 与获批 HEAD；`git diff --check`、工作流 JSON 解析和 Python 3.13 后端全量回归 `319 passed, 13 skipped, 2 warnings` 通过。
- 范围结论：差异仅为治理台账；无业务代码、测试、数据库、基础设施或部署变更。
- 剩余门禁：等待 DEV-001 向项目负责人 DEV-002 发送并获得正式 TASK-012 开发启动确认；不提前解锁 API-002—007、P0 前端或 Stage 6/7/8。
## TASK-012 DEV-001 complete defect review (2026-07-31)

- Review target: PR #75, exact HEAD `77a54a1587544374ed876e902bc132d58cf8ed9b`, branch `codex/task-012-p0-frontend-remediation`.
- Result: `Changes requested`; 37 open findings are consolidated in `06-testing/DEFECTS.md` as DEF-TASK012-001 through DEF-TASK012-037.
- Scope: fail-closed authentication, composite permission gates, API contract alignment, server-fact binding, field preservation, idempotency/in-flight state, BI filtering, Agent thread UX, and evidence reproducibility.
- Boundary: this governance branch contains no business-code fix. DEV-002 must fix all applicable findings in PR #75, rerun the complete frontend/backend/static suites, and submit a new exact HEAD for whole-candidate review.
- Gate: no Merge authorization, merge, TASK-012 closure, or Stage 6/7/8 unlock is permitted before that review and a fresh integration check.
- Second-pass additions: DEF-TASK012-038 dependency permission mismatch on equipment forms, DEF-TASK012-039 AI preview/manual-submit double-write path, and DEF-TASK012-040 buffered rather than incremental Runtime SSE consumption.

## TASK-012 third-pass review against HEAD 989e234 (2026-08-03)

- Result: `Changes requested`; new open findings are DEF-TASK012-041 through DEF-TASK012-046.
- Confirmed remaining risks: operation-guidance idempotency, two-step Global Agent orphaning/in-flight replay, unsafe manual fallback on work-order load failure, write-permission page gates blocking read-only views, incomplete SSE framing/error parsing, and missing Docker/PostgreSQL/RAGFlow/attachment/HTTPS/browser evidence.
- This is a governance-only review; no business-code fix is included. DEV-002 must remediate in PR #75, publish exact reproducible evidence, and request a new whole-candidate review.
- Gate: no Merge authorization, merge, TASK-012 closure, or Stage 6/7/8 unlock.

## TASK-012 fourth-pass review against HEAD ee149dda (2026-08-03)

- DEV-002 supplied a new exact HEAD `ee149dda2b262f9350bfe58c54d5603bcffa068c`.
- Code inspection confirms remediation direction for DEF-TASK012-041 (operation-guidance idempotency), DEF-TASK012-042 (atomic Global Agent start and in-flight guard), DEF-TASK012-043 (manual fallback only after authoritative empty order result), and DEF-TASK012-045 (incremental SSE framing with multi-line data/CRLF and stream failure handling). Page write controls were also separated from read-page access for the affected areas.
- Review status remains `Changes requested` pending reproducible execution of DEF-TASK012-046 on this exact HEAD. The reported frontend/backend unit results are not a substitute for Docker Compose, container health and `/healthz`, PostgreSQL, RAGFlow, ClamAV/MinIO, HTTPS and browser live-stack evidence.
- No Merge authorization, merge, TASK-012 closure or Stage 6/7/8 unlock is permitted before DEV-001 completes that environment verification and a final whole-candidate review.

### Environment verification update

- On exact HEAD `ee149dda2b262f9350bfe58c54d5603bcffa068c`, Windows Docker verification passed Compose config, API image build, PostgreSQL/Redis health, API startup and container-local `/healthz` HTTP 200.
- The remaining DEF-TASK012-046 scope is real authenticated RAGFlow retrieval/degradation, ClamAV/MinIO attachment scanning, HTTPS and authenticated browser E2E. Until those are executed, this is not an approval or merge authorization.
- Follow-up check found no dedicated RAGFlow, attachment, HTTPS or browser-E2E variables on the DEV-001 host and no `.env` file; only the template exists. The remaining evidence therefore requires an explicitly provisioned isolated validation environment.
- Runtime discovery corrected the boundary: healthy RAGFlow and MinIO containers are present; `127.0.0.1:19380/api/v1/datasets` responds 401 without a bearer key. No ClamAV container is running, and the available HTTPS listener belongs to the separate RAGFlow stack. Authenticated TASK-012 RAGFlow, attachment scanning and application HTTPS/browser evidence remain open.
- A temporary Key from the RAGFlow API page was then verified successfully against `127.0.0.1:19380/api/v1/datasets` (one dataset returned). This proves credential validity for the RAGFlow service only; it does not yet prove the TASK-012 API container's adapter path because the key was not persisted or exposed through repository configuration.
- Full live-stack attempt on exact HEAD `ee149dda` reached authenticated RAGFlow, PostgreSQL, Redis, MinIO, ClamAV, Nginx and the production operation-guidance route. The route returned `UNAVAILABLE` because the fixture did not provision/bind an `operation_guidance` Agent configuration; client `dataset_ids` were correctly ignored. This is recorded as DEF-TASK012-047 and remains a P1 blocker until the fixture/configuration contract is corrected and rerun.
## TASK-012 fifth-pass live evidence against HEAD a0bbfdbe (2026-08-03)

- DEV-002 supplied exact HEAD `a0bbfdbe7149a6b3a257f7456b9a6d190bec03d8`.
- The corrected disposable fixture provisions and binds a temporary `operation_guidance` Agent configuration, executes authenticated RAGFlow retrieval, operation-guidance success/degradation, attachment scanning and cleanup, then removes the temporary Agent configuration.
- Live-stack result: `2 passed, 5 warnings`; Python compilation and `git diff --check` passed. DEF-TASK012-047 is closed.
- Remaining review gate: application HTTPS ingress and authenticated browser E2E on this exact candidate. Result remains `Changes requested`; no Merge authorization, merge or Stage 6/7/8 unlock is permitted until those checks and the final whole-candidate review pass.
- DEV-001 environment probe: `https://127.0.0.1/healthz` and `/` both failed TLS handshake; Docker listed only the separate RAGFlow stack and no TASK-012 application ingress. This is an environment blocker, not passing application HTTPS evidence.
- Follow-up on exact HEAD: after installing the locked frontend dependencies, `npm ci` and `npm run build` passed. TLS certificate injection remains unavailable in the current shell, so Nginx HTTPS and browser evidence are still not collected; certificates must remain outside Git.
## TASK-012 HTTPS follow-up verification (2026-08-03)

- Temporary isolated application stack on exact HEAD `a0bbfdbe`: Nginx bound `127.0.0.1:8443`; `/healthz` returned HTTP 200; JavaScript and CSS returned `application/javascript` and `text/css`; HTTPS health E2E passed (`1 passed`).
- The supplied desktop-file Key candidate did not authenticate to RAGFlow (container probe HTTP 401); validator output was `1 passed, 1 skipped`. Authenticated RAGFlow production route and browser login E2E remain open.
