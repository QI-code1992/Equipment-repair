# 功能/页面检查点

静态原型检查点记录在 `03-ui-prototype/PROTOTYPE_CHECKPOINTS.md`，不得自动提升为生产检查点。

## FCP-006-NDB：TASK-006 Agent 配置非数据库切片

- 状态：已验证的可恢复检查点，不构成 TASK-006 完成、集成或 Stage 6 依据。
- 范围：四个 Agent 的不可变配置领域模型、独立初始化/读取/保存、模型能力校验、配置快照和未挂载 API 契约。
- 证据：实现与安全修复提交 `33d7712`、`7cbf76b`、`f7da339`、`04e651c`；远端恢复证据 `2a7ca4e`。
- 验证：Python 3.13.14 模块/API 回归 `24 passed, 1 warning`；未执行 Docker、Compose、RAGFlow 或数据库验证。
- 后续：TASK-002 前置已解除；数据库、迁移与正式路由仍须按 TASK-006 自身范围、迁移顺序、DEV-001 审核和 PR 门禁完成。

## FCP-006-DB-R2：TASK-006 持久化事务契约复审候选

- 状态：复审候选 / 未完成 / 未集成；不构成 TASK-006 完成、依赖解锁或 Stage 6 依据。
- 范围：持久化模式、仓储事务边界、同一 `agent_id` 初始化竞争、迁移元数据注册及数据库引擎工厂契约的复审证据；本轮将工厂和 Alembic 元数据契约集中到专用集成测试，并补充不连接网络的 PostgreSQL factory 回归。
- 当前任务证据链：`c8918d6f` → `0e34bed` → `483e75a` → `61c1026` → `911a41f` → `170bccf` → `42ef6ef`；本检查点绑定该完整链及其后的复审证据提交。
- 已验证：Python 3.13.14 下 `codebase/backend/.venv/bin/python -m pytest tests/modules/test_agent_config_persistence.py tests/modules/test_agent_config_persistence_integration.py -q` 为 `13 passed, 1 known warning`；加入领域测试的 `codebase/backend/.venv/bin/python -m pytest tests/modules/test_agent_config.py tests/modules/test_agent_config_persistence.py tests/modules/test_agent_config_persistence_integration.py -q` 为 `30 passed, 1 known warning`；迁移测试 `codebase/backend/.venv/bin/python -m pytest tests/modules/test_task006_migration.py -q` 为 `5 passed, 1 known warning`。三次警告均为 Starlette TestClient 对当前 `httpx` 的弃用提示。`git diff --check` 通过。唯一竞争测试使用两个文件型 SQLite 会话，实际捕获 `agent_configs.agent_id` 唯一约束冲突后读取已提交配置；外键失败后由调用方 `rollback()`，同一会话可查询并提交有效写入。PostgreSQL factory 契约只创建引擎并检查 PostgreSQL dialect、URL 参数、预检池和无 SQLite PRAGMA 监听器，不发起连接。
- 仍待 DEV-001：PostgreSQL/Compose 真实环境的迁移升降级、并发初始化、外键与正式路由验证均未执行；SQLite 和无连接 factory 证据不得替代这些验证或 PR 门禁。

## FCP-002-R6：TASK-002 正式集成后的治理收尾

- 状态：代码正式集成、技术验证与治理收尾已完成；PR #25 已合入并解除 TASK-002 下游前置，不能作为 Stage 6 进入依据。
- 正式审核与合并：DEV-002 已批准精确任务分支 HEAD `2e89dcd8d8dff6af5b841f32ac0a7d5feb794e15`；PR #20 由集成负责人 DEV-001（`ll979053897-arch`）手动 Merge Commit 合入 `codex/stage-05-integration`，合并提交为 `904886f48061e27c775f6ee2f8ddae99f5571ead`。
- 已验证证据：Python 3.13 为 `142 passed, 5 skipped, 1 warning`；PostgreSQL 17 真实数据库专项为 `5 passed, 1 warning`；Compose 容器健康和容器内 `GET /healthz` HTTP 200 已保留为正式集成证据。
- 治理合并：PR #25 由 DEV-002（`QI-code1992`）手动 Merge Commit 合入 `codex/stage-05-integration`，Merge Commit 为 `028da42eb9ab4b55ef981ac462e09993a31e8813`。
- 有效依赖：TASK-003 与 TASK-004 可按任务书启动；TASK-005 仍等待 TASK-004；TASK-006 已解除 TASK-002 前置，包括迁移、数据库集成和共享数据模型，但仍须满足本任务自身 PR 门禁。

## FCP-001：平台运行环境基线

- 状态：已重新验证，允许工作包 B 以此作为生产工程前置。
- 范围：TASK-001；`codebase/backend/`、`codebase/frontend/`、`codebase/infra/` 目录边界，FastAPI 应用工厂与 `GET /healthz`，PostgreSQL/Redis 内部 Docker 网络。
- 修复提交：`87538b04a168cb3c11c2e65dfb976d3a206d8218`（`codex/task-001-runtime-baseline`）；推送后作为远端可恢复检查点。
- 已验证：Python 3.13.14 下 `pytest codebase/backend/tests/test_health.py -q` 为 4 passed；`docker compose ... config --quiet` 通过；独立 Compose 项目 `equipment-task1` 中 PostgreSQL、Redis 为 healthy，API 容器内实际请求 `/healthz` 返回 200。
- 接口冻结：`GET /healthz`、`codebase/backend/pyproject.toml`、`codebase/infra/docker-compose.yml`、`POSTGRES_DSN`、`REDIS_URL`。
- 限制：本检查点未发布公网端口；Nginx HTTPS 的实际公网入口与证书配置归 Task 10 部署工作处理。

## FCP-002：TASK-002 被拒候选恢复点

- 状态：Rejected / Preserved / Superseded；不是稳定检查点，不得解锁依赖。
- 范围：PR #15 的 TASK-002 身份、权限、审计、组织和设备基础候选；历史恢复点 `0b0d9cf0dc066143c0a57d4683567fadb4714c12`，交接证据 `9f162b421f4fefae4cdd69a001891c7e83d4bc13`。
- 被拒候选：`cfb8ed9b99b5e440b3c0bf4a8652f4f7d233ee77`；审核结论为 `Changes requested`。
- 历史验证：Python 3.13.14 下 38 tests passed，Compose、PostgreSQL 迁移和并发验证曾通过；该证据不能覆盖 DEV-002 后续正式审核阻断项。
- 异常集成：违规合并 `e328cec64f1aa9c7cdc383579af042692dce5679` 已由 CR-038 回滚，并通过 PR #17 合入修复提交 `d37698c6e51df1701bbdfcf12ec6fa329241e0bd`。
- 回滚后验证：Python 3.13.14 为 `4 passed, 1 warning`；Compose 构建通过；PostgreSQL、Redis、API healthy；容器内 `/healthz` 返回正常。
- 恢复性：原提交仍可从 Git 合并历史检出，本地 TASK-002 工作树继续保留；不得把该恢复点作为完成、正式集成或 Stage 6 证据。
- 后续：CR-037 合入后，DEV-001 才可继续 TASK-002 R6/R7；DEV-002 复审通过后创建新的正式 TASK-002 PR。

## FCP-002-R1：TASK-002 CR-036 复审候选

- 状态：Review Candidate / Not Integrated / Does Not Unlock Dependencies。
- 分支：`codex/task-002-identity-equipment`。
- 代码候选：R6 `35119954ba1d9ca475f03d1faa026bf6a474b18f`，R7 `11dbb226e9b77ff5185fed5fa1434b0de6749206`；正式证据提交在本轮提交后记录。
- 范围：完整设备与组织合同、固定角色和用户管理、失败审计、敏感字段脱敏、API/Data Model 契约、Alembic `0002` 和真实 PostgreSQL 并发验证。
- 验证：Python 3.13.14 全套 `125 passed, 5 skipped`；专用 PostgreSQL 17 集成 `5 passed`；`0002 -> 0001 -> 0002`；Compose 配置、PostgreSQL/Redis 健康、API `/healthz` 和 `git diff --check` 通过。
- Review：DEV-001 独立复审 Critical 0、Important 0；等待 DEV-002 正式复审。
- 恢复：可检出任务分支精确候选；尚未合入集成分支，不得替代稳定 FCP、不得解锁 TASK-003/TASK-004 或数据库依赖。
- 首轮证据：`ab67bcdff42d64ba739571515df4e6faed158d32` 已推送，但因与集成分支分叉而被后续同步候选取代。
- 集成同步：Merge Commit `0aac415d18aee256c237adb508d2ab24314a7486` 合入基线 `ac767c83128cb89ceea8e28c518be0adfbe1984c`；当前模拟合并无冲突。
- 同步验证候选：`4c111d0243d947a32d555bd48b1b72cab552bac4`；已推送并完成第二次自查，作为本治理记录所绑定的实现与验证候选。

## FCP-002-R2：TASK-002 最终审核阻断修复候选

- 状态：Review Candidate / Not Accepted / Not Integrated / Does Not Unlock Dependencies。
- 分支：`codex/task-002-identity-equipment`；修复前远端 HEAD `60c71dd5ab7588006ee16d794b03bef493fb3c72`。
- 代码候选：`73030f83638b3b063db483029591720bf65aac21`。
- 范围：固定四角色和 33 项权限迁移、系统管理员完整授权、非固定角色授权隔离、`user_management.view_all` 用户范围、敏感字段变体与附件正文脱敏、未知数据库/运行时异常回滚和独立失败审计、Alembic 程序化日志隔离。
- 验证：Python 3.13 `136 passed, 5 skipped`；5 个专用 PostgreSQL 17 测试单独 `5 passed`；`0002 -> 0001 -> 0002` 后为 `0002 (head)`；固定目录实测为 roles=4、permissions=33、system_admin_grants=33、non_fixed_roles=0。
- 运行态：Compose 配置和重建通过；PostgreSQL/Redis `healthy`，API `Up`；容器内 `/healthz` 返回 HTTP 200 与 `{"service":"equipment-operations-platform","status":"ok"}`。
- Review：DEV-001 三轮自查后 Critical 0、Important 0；DEV-002 的两个历史 Minor 已在 `CODE_REVIEW.md` 记录不可改写历史处置，不阻断本候选。
- 恢复与门禁：可从精确代码候选检出；DEV-002 尚未批准、后继正式 PR 尚未创建、尚未合入集成分支，因此本检查点不得解锁 TASK-003、TASK-004、TASK-005 或依赖 TASK-002 的数据库工作。

## FCP-002-R3：TASK-002 审计脱敏复审候选

- 状态：Review Candidate / Not Accepted / Not Integrated / Does Not Unlock Dependencies。
- 分支与代码候选：`codex/task-002-identity-equipment` / `ac6947a642f00ba48aebcb80064f87fcc4c01ea8`。
- 范围：仅修复失败审计脱敏的密码语义段和附件正文别名绕过；不修改 PRD、SPEC、迁移、TASK-003/TASK-004 或生产依赖。
- 证据：红灯为 2 failed；定向回归 `19 passed, 1 warning`；Python 3.13 全量 `138 passed, 5 skipped, 1 warning`；`compileall` 与 `git diff --check` 通过。失败请求已查询审计表，确认 `metadata_json` 不含 `newPasswordConfirmation`、`current_password_confirmation`、`raw_content` 或嵌套二进制载荷秘密。
- PostgreSQL：测试镜像 `41591e7` 在构建阶段安装 `pyproject.toml` 已声明的 dev 组，再接入 `infra_platform` 内部网络；专用 PostgreSQL 17 集成 `5 passed, 1 warning`。默认生产镜像确认不含 pytest/httpx，重建后 `/healthz` 为 HTTP 200。
- 门禁：等待 DEV-002 对推送后的最终台账 HEAD 复审；只有 DEV-002 通过并创建后继正式 PR、合入目标分支后才可解锁依赖。

## FCP-002-R5：TASK-002 语义敏感键复审候选

- 状态：Review Candidate / Not Accepted / Not Integrated / Does Not Unlock Dependencies。
- 分支与代码候选：`codex/task-002-identity-equipment` / `ea4338bad15f16048226a329801d3144b367909e`。
- 范围：仅修复 CR-036 已知敏感语义别名的审计脱敏；不修改 PRD、SPEC、迁移、API、Compose、生产依赖或 TASK-003/TASK-004。
- 证据：RED `2 failed`；定向 `23 passed, 1 warning`；Python 3.13 `142 passed, 5 skipped, 1 warning`；compileall、diff check 通过；落库审计不含附件/文件、密码、Cookie、Token 测试秘密，业务字段和 Token 统计字段保持。
- 运行态：独立 test 镜像 PostgreSQL 17 `5 passed, 1 warning`；Compose 重建成功，PostgreSQL/Redis healthy、API Up，`/healthz` HTTP 200。
- 残余风险与门禁：未知字段默认脱敏未纳入本 CR；等待 DEV-002 对推送后的最终台账 HEAD 复审。仅审核通过、后继正式 PR 创建并合入目标分支后才可解锁依赖。

## FCP-002-R4：TASK-002 审计标量脱敏复审候选

- 状态：Review Candidate / Not Accepted / Not Integrated / Does Not Unlock Dependencies。
- 分支与代码候选：`codex/task-002-identity-equipment` / `b4d451009d1deb9dbe3286f5bff4db9414ef4aee`。
- 范围：仅修复 CR-036 审计脱敏在附件标量、标量列表、混合 list/dict 与紧凑密码键上的遗漏；不修改 PRD、SPEC、迁移、API 契约、TASK-003/TASK-004 或生产依赖。
- 证据：RED `2 failed`；定向 `21 passed, 1 warning`；Python 3.13 全量 `140 passed, 5 skipped, 1 warning`；compileall、diff check 通过；失败请求的 `AuditEvent.metadata_json` 无 `newpassword`、`userpassword`、附件标量、列表或嵌套混合载荷明文。
- 运行态：独立 test 镜像 PostgreSQL 17 `5 passed, 1 warning`；Compose 重建成功，PostgreSQL/Redis healthy、API Up，`/healthz` HTTP 200。
- 门禁：等待 DEV-002 对推送后的最终台账 HEAD 复审；只有 DEV-002 通过并创建后继正式 PR、合入目标分支后才可解锁依赖。
