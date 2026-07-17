# 开发到产品交接

## TASK-001 正式交接（2026-07-15）

- 已批准输入基线：`25e15709a3f1d92f661d37acdb8aa3e1e0e41346`（`baseline/stage-04-development-v1.1`）。
- 修复范围：清除 `codebase/` 中后端应用工厂、配置字段、Compose 服务和网络的重复定义；不改变 PRD、SPEC、原型或公开业务 API。
- 远端提交：修复 `87538b04a168cb3c11c2e65dfb976d3a206d8218`，验证证据 `45725ac083c98ea999492b709e9792082c3db284`，分支 `codex/task-001-runtime-baseline`。
- 验证：Python 3.13.14 下健康检查测试 4 passed（仅一个第三方弃用警告）；Compose 配置通过；PostgreSQL、Redis healthy；API 容器内 `/healthz` 返回 `200` 与 `{'status': 'ok', 'service': 'equipment-operations-platform'}`。
- 缺陷：`DEF-003`、`DEF-004` 已解决并更新台账；独立 Review 通过，无阻断、重要或次要问题。

## DEV-002 启动边界

- 可启动：TASK-006 的四 Agent 独立配置领域测试与非数据库实现。
- 禁止提前：TASK-006 的数据库迁移、数据库集成和共享数据模型，直到 TASK-002 完成并合入。
- 仍阻塞：TASK-005 必须等待 TASK-002 与 TASK-004；其他任务继续严格遵循任务书依赖矩阵。
- 容器责任：DEV-002 不得自行宣称 Docker、Compose 或 RAGFlow 验证通过；相关真实环境验证仍由 DEV-001 提供。

## TASK-002 开发交接（2026-07-15）

- 分支与恢复点：`codex/task-002-identity-equipment`，远端实现 Commit `0b0d9cf0dc066143c0a57d4683567fadb4714c12`，交接证据 Commit `9f162b421f4fefae4cdd69a001891c7e83d4bc13`，PR 目标为 `codex/stage-05-integration`。
- PR：[#15](https://github.com/QI-code1992/Equipment-repair/pull/15) 已 Ready for review，待 Review 与集成。
- 交付契约：会话认证、操作权限依赖、角色/权限查询、登录/登出/拒绝审计、全局请求指纹幂等、组织树、设备主数据和 Alembic `0001`。
- 验证：Python 3.13.14 下 38 tests passed；Compose 配置、API 镜像构建、PostgreSQL downgrade/upgrade/current、`/healthz` 200、真实并发幂等/唯一冲突/组织树竞争均通过。
- Review：最终独立复审 Critical 0、Important 0、Minor 0。
- DEV-002 消费边界：可基于冻结的认证上下文继续 TASK-006 非数据库实现；只有 TASK-002 合入集成分支后，才可开始 TASK-006 数据库迁移/集成以及其他依赖 TASK-002 的数据库工作。
- DEV-001 下一步：提交并完成 TASK-002 PR/集成；合入后按依赖矩阵启动 TASK-003，并通知 DEV-002 数据库边界已解锁。

## TASK-002 交接状态更正（2026-07-16）

- 原因：DEV-002 对 PR #15 候选 `cfb8ed9b99b5e440b3c0bf4a8652f4f7d233ee77` 提交 `Changes requested`；上节“Ready for review”不再代表当前有效交接状态。
- 当前状态：TASK-002 / CR-036 `In Development`；本地整改代码和契约草稿保持原状。任务书 v1.2 已通过 PR #18 合入 `codex/stage-05-integration`，CR-037 收尾记录合入后可恢复 R6/R7。
- 旧证据边界：`0b0d9cf`、`9f162b4` 和 PR #15 历史继续保留，但不得作为 TASK-002 完成、FCP、正式 PR 或集成依据。
- 协作分工：DEV-001 为任务开发者和集成负责人；DEV-002 为指定审核者及后继正式 PR 创建者。DEV-001 只能推送任务分支并发送书面审核请求。
- PR #15：保留为被拒绝候选的审核历史和本轮 Review Request 载体；DEV-002 审核新候选通过后创建后继正式 PR。
- 依赖边界：TASK-003、TASK-004、TASK-005 及 DEV-002 的数据库集成继续按任务书阻塞；TASK-006 仅保留已允许的非数据库范围。
- 下一次有效交接条件：任务书 v1.2 与本审批记录已通过治理 PR 合入集成分支；CR-036 R6/R7 完成；PostgreSQL/Compose 和完整回归通过；正式证据提交并推送；DEV-002 复审通过。
- PR #16 更正：历史 PR #16 错误指向 `main`，且当前远端 `main` 不包含获批任务书 v1.2；该 PR 不构成 CR-037 完成或 Stage 5 协作基线。必须重新创建目标为 `codex/stage-05-integration` 的治理 PR。
- CR-037 正确 PR：[PR #18](https://github.com/QI-code1992/Equipment-repair/pull/18)，已合入 `codex/stage-05-integration`；Merged Head 为 `e6b571d16192fb4462b7c118ef977df8f6ce186a`，Merge Commit 为 `18485653a94cd033cfc82e8d6c7e40c35fcfbe33`。合并树、Python 3.13、`compileall`、Compose 配置和治理一致性验证通过。
- CR-037 收尾边界：本收尾 PR 仅把合并结果写回治理台账；合入后 DEV-001 可恢复 TASK-002 / CR-036 R6/R7。TASK-002 仍未完成，TASK-003、TASK-004、TASK-005 及依赖 TASK-002 的数据库集成继续阻塞。

## CR-038 治理补救交接（2026-07-16）

- 事件：PR #15 在审核结论仍为 `Changes requested` 时被合入 `codex/stage-05-integration`，合并提交为 `e328cec64f1aa9c7cdc383579af042692dce5679`。
- 批准：项目负责人批准保留开发成果并通过独立 PR 非破坏性回滚该集成结果。
- 补救分支：`codex/cr-038-revert-pr-15-gate-violation`。
- 授权记录：`6650f615e48d88b9a54179c27a7f03d1bf48f391`。
- 回滚候选：`5d91e83679acefa5486a25bf5b921e9c12fd52d6`。
- 补救 PR：[PR #17](https://github.com/QI-code1992/Equipment-repair/pull/17)，已合入 `codex/stage-05-integration`。
- 合并批准：项目负责人于 2026-07-16T15:00:35+08:00 明确批准审查候选 `3f02ac1021ffb2f189ee53120d4b3523415bff60` 转为 Ready 并手动合入；批准后的治理文档提交不得修改代码或回滚边界。
- Merge Commit：`d37698c6e51df1701bbdfcf12ec6fa329241e0bd`。
- 验证：Python 3.13.14 `4 passed, 1 warning`；`compileall`、Compose 构建、PostgreSQL/Redis/API 健康和容器内 `/healthz` 通过。
- 当前边界：CR-038 已完成；TASK-002 仍为 `Changes requested`；CR-037、TASK-002 R6/R7、TASK-003、TASK-004 和依赖 TASK-002 的数据库集成继续暂停。
- 下一步：完成 CR-037 治理 PR；合入后恢复 TASK-002 R6/R7 和 DEV-002 复审。

## TASK-002 / CR-036 新候选审核请求（2026-07-16）

- 任务开发者：DEV-001。
- 指定审核者与正式 PR 创建者：DEV-002。
- 任务分支：`codex/task-002-identity-equipment`。
- 目标分支：`codex/stage-05-integration`。
- 实现提交：R6 `35119954ba1d9ca475f03d1faa026bf6a474b18f`；R7 `11dbb226e9b77ff5185fed5fa1434b0de6749206`。
- 正式证据：本轮 `docs(task-002): record review remediation handoff` 提交后，以推送后的任务分支精确 HEAD 作为审核对象，并在 GitHub 审核请求中补记。
- 需求/AC：FR-001、FR-010、FR-011、NFR-001、NFR-009；AC-001—008、AC-038、AC-039；不改写 PRD/SPEC/AC。
- 修改范围：身份、固定角色和权限目录、失败审计与脱敏、组织层级、完整设备主数据、Alembic `0002`、API/Data Model 契约和相关测试。
- 验证：Python 3.13.14 全套 `125 passed, 5 skipped`；专用 PostgreSQL 17 集成 `5 passed`；迁移 `0002 -> 0001 -> 0002`；Compose、PostgreSQL/Redis 健康、API `/healthz`、compileall 和 diff check 通过。
- Review：DEV-001 内部独立复审 Critical 0、Important 0；Minor 为未来迁移 revision/测试函数可读性提醒，不阻塞本候选。
- 未验证：DEV-002 尚未批准；后继正式 PR 尚未创建；任务尚未正式集成。
- 依赖：无新增生产依赖；TASK-003/TASK-004 未实施；TASK-003、TASK-004、TASK-005 和依赖 TASK-002 的数据库工作继续阻塞。
- 兼容与抽象：未新增兼容分支；仅保留任务所需领域 service/schema 与测试职责拆分，无通用框架。
- 风险：Alembic `0002` downgrade 会丢弃完整合同新增字段，只允许在已备份或专用验证环境执行；PostgreSQL 集成测试有专用库名、主机和显式开关三重保护。
- 回退：应用与契约按独立任务 Commit 选择性 revert；数据库按已验证 downgrade 或前向修复策略处理，不对生产数据执行未授权删除。
- 请求动作：请 DEV-002 对推送后的精确 HEAD 复审；若通过，由 DEV-002 创建后继正式 PR。PR #15 仅保留被拒绝和违规合并/回滚历史，不得再次作为正式集成触发源。

### 集成基线同步更正

- 被取代审核 HEAD：`ab67bcdff42d64ba739571515df4e6faed158d32`；原因是该分支相对当前集成分支分叉，模拟正式合并存在冲突。
- 当前集成基线：`ac767c83128cb89ceea8e28c518be0adfbe1984c`。
- 同步 Merge Commit：`0aac415d18aee256c237adb508d2ab24314a7486`。
- 修正结果：当前集成基线已成为任务分支祖先；模拟合并无冲突；CR-037/CR-038 与 `STAGE_APPROVALS.md` 保持集成分支版本。
- 复验结果：Python 3.13.14 `125 passed, 5 skipped`；PostgreSQL 17 集成 `5 passed`；迁移、Compose 实际状态、容器健康和 `/healthz` 通过。
- 同步验证候选：`4c111d0243d947a32d555bd48b1b72cab552bac4`，已推送并完成第二次自查。
- 新请求动作：首轮 PR #15 评论中的 `ab67bcd...` 请求已被取代；本治理记录提交并推送后，以新的远端分支 HEAD 重新请求 DEV-002 审核。该最终 HEAD 包含的新增内容仅为本节台账回填，不改变 `4c111d0...` 的代码、测试或运行证据。

## TASK-002 / CR-036 R8 复审交接（2026-07-17）

- 开发者：DEV-001；指定审核者与后继正式 PR 创建者：DEV-002。
- 分支/目标：`codex/task-002-identity-equipment` → `codex/stage-05-integration`。
- 被取代审核 HEAD：`60c71dd5ab7588006ee16d794b03bef493fb3c72`；R8 代码候选：`73030f83638b3b063db483029591720bf65aac21`。
- 修复：精确固定角色/权限目录和系统管理员全授权；非固定角色不得授权；用户管理执行 `user_management.view_all`；敏感字段变体和附件正文脱敏；数据库/未知异常回滚与独立失败审计。
- 验证：本机 Python 3.13 `136 passed, 5 skipped`；专用 PostgreSQL 17 `5 passed`；迁移往返和最终目录计数通过；Compose、PostgreSQL/Redis 健康、API Up、`/healthz` HTTP 200。
- Review：DEV-001 三轮复审 Critical 0、Important 0；两个历史 Minor 已按不可改写历史约束形成书面处置。
- 交付边界：无生产依赖、兼容层、通用抽象、TASK-003 或 TASK-004 修改；未创建正式 PR。
- 请求动作：正式台账提交推送后，以远端最终 HEAD 在 PR #15 请求 DEV-002 复审。若审核通过，由 DEV-002 创建后继正式 PR；在合入前 TASK-002、TASK-003、TASK-004、TASK-005 和相关数据库依赖状态不变。
