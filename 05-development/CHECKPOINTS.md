# 功能/页面检查点

## FCP-013-UI-ROUTE-CONTEXT：TASK-013 前端增量修复（2026-08-05）

- 分支：`codex/task-013-prototype-fidelity-remediation`；提交：`5695716`。
- 范围：深层设备/维修路由保持正确的顶部导航上下文；移动端应用壳增加可关闭的侧栏与遮罩；设备台账空数组保留“新增设备”入口并显示真实空态；移除未使用的前端基础占位组件。
- 自动化验证：前端 Vitest `8 个测试文件、76 passed`；`npm run build` 通过；`node --test 06-testing/tests/*.test.js` 为 `15 passed`；`git diff --check` 通过。
- 未验证：本机未连接真实业务 API，未执行登录后的浏览器业务流程、Windows Docker/RAGFlow/HTTPS/live-stack 验证；本检查点不关闭 `DEF-STAGE7-001`，不解锁 Stage 6、Stage 7 或 Stage 8。
- 依赖与兼容：未新增生产依赖、兼容层或抽象层；未修改 API、数据库、权限、部署配置。

## FCP-012 整体开发候选本地完成（2026-07-31）

- 分支：`codex/task-012-p0-frontend-remediation`；最新精确开发提交：`08e1576`。
- 范围：API-002—007 读模型、全部除 Data import 外的 P0 正式页面、权限/会话、附件引用、Agent 线程历史与 SSE、前端回归和治理材料。
- 本地验证：前端 7 个测试文件 `53 passed`，生产构建通过；后端 `328 passed, 13 skipped, 2 warnings`；compileall、15 项 Node 静态回归、JSON 解析和 `git diff --check` 通过。
- 状态：`DEVELOPMENT_COMPLETE_PENDING_DEV001_REVIEW`。所有工作包已完成本地实现，但尚未完成 DEV-001 整体审核、Windows Docker/WSL2 live-stack、真实 RAGFlow/ClamAV/MinIO、浏览器 E2E 与最终 Stage 6/7 门禁。
- 回退：正式合入前按单一任务 PR 的 Merge Commit 进行选择性 revert；当前未合并，不执行回退或数据操作。

## FCP-012-API-001 合并后治理收尾候选（2026-07-30）

- 集成事实：PR #71 的获批 HEAD `c1273fd01e5ec91b2de3af59aab371844d228cd6` 已由 DEV-002 手动 Merge Commit `274673b72d5201986ffee77b038f516022cd174d` 合入 `codex/stage-05-integration`；双亲为 `866875d4071a725d9c780f535d6be10e1202ba4e` 与获批 HEAD。
- 合并后核验：祖先关系、merge-tree、完整 diff-check、Python 3.13 定向 `3 passed, 2 warnings`、全量 `319 passed, 13 skipped, 2 warnings`、compileall、Compose config 与 workflow JSON 解析通过。
- 状态：`POST_MERGE_GOVERNANCE_CANDIDATE_PENDING_OWNER_CONFIRMATION`。本候选合入后才可将 API-001 标记为治理闭环；API-002—007 仍未关闭，TASK-012 前端和 Stage 6/7/8 不解锁。
- 回滚：如发现回归，先在隔离环境验证 `git revert -m 1 274673b72d5201986ffee77b038f516022cd174d`；不得删除运行数据、卷或其他已接受功能。

## FCP-012-API-001 复审证据补充（2026-07-30）

- 状态：`DEVELOPMENT_CANDIDATE_PENDING_DEV002_REVIEW`；PR #71 仍未集成，不解锁 TASK-012 或 Stage 6/7/8。
- 最新测试证据提交：`44992b5b34f6a2c77378383a363bfb2a3f86fd25`。
- 证据：API-001 定向 `3 passed, 2 warnings`；后端全量 `319 passed, 13 skipped, 2 warnings`；compileall、Compose config 和 diff-check 通过。
- 回滚：如候选被拒，仅回退测试补充提交；不删除已存在的 API-001 实现候选，也不改变已确认的 API 范围。

静态原型检查点记录在 `03-ui-prototype/PROTOTYPE_CHECKPOINTS.md`，不得自动提升为生产检查点。

## FCP-012-API-001：Workbench 读取 API 开发候选（2026-07-30）

- 状态：`DEVELOPMENT_CANDIDATE_PENDING_DEV002_REVIEW`；未集成，不解锁 TASK-012 或 Stage 6/7/8。
- 分支/实现提交：`codex/task-012-api-001-workbench` / `7ba0e5e77e6a784f0dd6a0622c91ebce691e00a1`。
- 范围：`GET /api/workbench/todos`、`alert-summary`、`shortcuts` 的只读契约和最小后端实现；只读既有故障、设备及权限事实，不新增迁移、依赖、健康分聚合、任务分配、兼容层或通用抽象。
- 验证：Python 3.13 定向 `3 passed, 2 warnings`；后端全量 `319 passed, 13 skipped, 2 warnings`；`compileall`、Compose `config --quiet` 和完整差异检查通过。
- 审核与回退：等待 DEV-002 对 Draft PR 的精确 HEAD 审核；获批与项目负责人逐 PR/HEAD 授权前不得合并。可选择性回退该功能提交，不涉及数据或部署状态。

## FCP-011：TASK-011 合并后治理收尾（2026-07-27）

- 状态：`CLOSED_POST_MERGE_GOVERNANCE_COMPLETED`；治理 PR #55 已合入 `53bdf90ec8ab743165d0542099a15d3c9de598b3`，TASK-011 正式关闭，Stage 6 仍须单独获得正式门禁批准。
- 集成链：PR #52 / `b252ba27…` → `298ba147…`；PR #53 / `c55da7df…` → `22f619f…`；PR #54 / `f3150a2…` → `b1e4ea6c409946667e22e4bff427c4dccaa86f22`。三次均由 DEV-002 按绑定授权手动 Merge Commit 执行。
- 合并后验证：在 `b1e4ea6…` 执行后端 `309 passed, 13 skipped, 2 warnings`、前端 `26 passed`、生产构建、备份/Nginx 契约、Compose config、`compileall` 与双亲 `diff --check`，全部通过。
- 真实运行证据：`f3150a2…`（`b1e4ea6…` 的第二父提交）完成真实 RAGFlow Agent 成功与不可用降级路径、HTTPS E2E、API 重启恢复、备份和随机隔离恢复；临时数据集已删除并复核不存在。
- 范围与回退：本治理候选只改任务书、检查点、测试报告和交接台账；无代码、迁移、依赖、运行配置或兼容层。若需回退，按影响范围选择性 revert `b1e4ea6…`，不得删除卷或覆盖运行数据。

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

## FCP-004-R1：TASK-004 独立 RAGFlow 基础设施审核候选（已被审核驳回）

- 状态：Superseded / Changes Requested at `8b628fcfbf80fb6490d8d3dd5257feafba9d1595` / Not Accepted / Not Integrated / Does Not Unlock TASK-005。
- 分支/基线：`codex/task-004-ragflow-infra` / `b29c69d13c3d1c81f01023152eabf0c0f2d02741`；证据提交前功能候选 `ac8c007730d8e947c5687380e4583e8b23d2cce1`。
- 范围：RAGFlow v0.25.6、MySQL 8.0.39、Redis 7.4.2、MinIO 2026-03-25、Elasticsearch 8.11.3 的独立 Compose、网络、健康、命名卷、脱敏环境模板、验证脚本和运行手册。
- 验证：Python 3.13 `5 passed`；两套 Compose config 与静态契约通过；5 容器 healthy、Web 200；内部依赖 0 宿主端口；四存储重启读回探针且容器未重建；`git diff --check` 通过。
- 恢复：从本候选检出并使用本地环境文件启动；常规回退执行 Compose `down` 和选择性 revert，禁止未经授权删除命名卷。
- 门禁：DEV-002 已发现 3 个 Important，本候选不得恢复为审核对象；后续以 FCP-004-R2 为准。TASK-005 继续锁定；Stage 6 禁止进入。

## FCP-004-R2：TASK-004 PR #27 审核修正候选

- 状态：Review Candidate / Not Accepted / Not Integrated / Does Not Unlock TASK-005。
- 分支/基线：`codex/task-004-ragflow-infra` / `b29c69d13c3d1c81f01023152eabf0c0f2d02741`；修正功能提交 `f87a0c309c322f9accedcaea4a80aed84483b0e7`。
- 修正：9380 `/api/v1/system/version` 精确契约及有限启动重试；MinIO S3 bucket/object 重启持久化；5 个获批镜像 SHA-256 强制匹配及漂移失败测试。功能提交为 `f87a0c309c322f9accedcaea4a80aed84483b0e7`、`ba7e13f2b585f872ca811e98b50c09e25020fba5`。
- 验证：Python 3.13 `5 passed, 1 warning`；两套 Compose config、两个静态契约、5 容器健康、Web/API 200、网络隔离、S3 持久化和摘要突变负向测试通过；`git diff --check` 通过。
- 恢复/门禁：可检出本候选复现完整验证；不得替代稳定集成基线。等待 DEV-002 复审 PR #27 新精确 HEAD；获批、逐 PR/HEAD Merge 授权、DEV-002 Merge Commit 和 DEV-001 合并后复验完成前，TASK-005 继续锁定，Stage 6 禁止进入。

## FCP-004-R3：TASK-004 PR #27 第二轮审核修正候选

- 状态：Superseded / Changes Requested at `601d54d2427302999c7bc10ac5beec3ac0565501` / Not Accepted / Not Integrated / Does Not Unlock TASK-005；后续以 FCP-004-R4 为准。
- 分支/基线：`codex/task-004-ragflow-infra` / `b29c69d13c3d1c81f01023152eabf0c0f2d02741`；精确候选以本轮证据提交推送后的 PR #27 HEAD 为准。
- 修正：Compose 展开镜像、获批 digest、固定标签 ID 与运行容器 ID 绑定；显式本地 `EnvFile`；Web 有限超时；当前执行窗口依赖错误/秘密扫描；时间、退出码和脱敏日志摘要；失败探针保留；合规 PR 标题。
- 验证：Python 3.13 `5 passed, 1 warning`；两套 Compose config、两个静态契约、真实健康/API、网络隔离、四存储 restart、错误镜像/摘要、失败探针保留及日志扫描均通过；未记录真实秘密。
- 恢复/门禁：使用忽略的本地环境文件复现；失败探针不自动清理以保留调查证据，清理由操作者确认后限定 TASK-004 命名空间。等待 DEV-002 审核新精确 HEAD；获批、授权、合并和合并后复验前 TASK-005 继续锁定，Stage 6 禁止进入。

## FCP-004-R4：TASK-004 PR #27 第三轮审核修正候选

- 状态：Superseded / Changes Requested at `6cd29f158b2c03f61c5b21a7e9bf99d30ec17a34` / Not Accepted / Not Integrated / Does Not Unlock TASK-005；后续以 FCP-004-R5 为准。
- 分支/基线：`codex/task-004-ragflow-infra` / `b29c69d13c3d1c81f01023152eabf0c0f2d02741`；修正功能提交 `dc909fff1c8260f2f8a50670192761572cdfb76b`，精确候选以本证据提交推送后的 PR #27 HEAD 为准。
- 修正：删除 Runbook 对隔离脚本的无效 `-EnvFile` 参数并通过 AST 核对签名；MySQL、Redis、MinIO、Elasticsearch 和临时资源清理全部使用带退出码检查的 Compose 调用；清理完成后才输出 PASS。
- 验证：审核修正契约和 Compose 契约 PASS；三个 PowerShell 文件可解析；Docker 5 服务 healthy、Web/API 200、RAGFlow v0.25.6、Elasticsearch 8.11.3、网络隔离通过；四存储 restart 一致且严格清理 4 类探针；`git diff --check` 通过。
- 恢复/门禁：失败验证路径保留持久化探针，不输出 PASS；成功路径清理失败返回非零。等待 DEV-002 审核新精确 HEAD；获批、逐 PR/HEAD 授权、DEV-002 Merge Commit 和 DEV-001 合并后复验完成前，TASK-005 继续锁定，Stage 6 禁止进入。

## FCP-004-R5：TASK-004 PR #27 第四轮审核修正候选

- 状态：Review Candidate / Not Accepted / Not Integrated / Does Not Unlock TASK-005。
- 分支/基线：`codex/task-004-ragflow-infra` / `b29c69d13c3d1c81f01023152eabf0c0f2d02741`；修正功能提交 `29180e285767cbffb9d694cd1834f04514d2cc18`，精确候选以本证据提交推送后的 PR #27 HEAD 为准。
- 修正：设计、计划和 Runbook 统一真实运行 `.env.local` 契约；以最小外部命令边界和四个子进程证明 MySQL、Redis、MinIO、Elasticsearch 清理命令非零时验证整体非零且不输出 PASS。
- 验证：审核契约、清理失败行为和 Compose 契约 PASS；全部 PowerShell 文件可解析；Python 3.13 `5 passed, 1 warning`；5 服务 healthy、Web/API 200、RAGFlow v0.25.6、Elasticsearch 8.11.3、网络隔离和四存储 restart/清理通过；`git diff --check` 通过。
- 恢复/门禁：可检出本候选并使用忽略的本地环境文件复现。等待 DEV-002 审核新精确 HEAD；获批、逐 PR/HEAD 授权、DEV-002 Merge Commit 和 DEV-001 合并后复验完成前，TASK-005 继续锁定，Stage 6 禁止进入。

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

## FCP-004-R6：TASK-004 PR #27 第五轮审核修正候选

- 状态：Review Candidate / Not Accepted / Not Integrated / Does Not Unlock TASK-005。
- 分支/基线：`codex/task-004-ragflow-infra` / `b29c69d13c3d1c81f01023152eabf0c0f2d02741`；修正功能提交 `314b46d3efdc7af0d13c671fadd41be7bb3900d1`，精确候选以本证据提交推送后的 PR #27 HEAD 为准。
- 修正：审核契约现在解析任务书 `- 验证：...` 内反引号运行命令，拒绝 `.env.example` 运行回退，同时排除静态 config、说明文字和明确禁用示例。
- 验证：Windows PowerShell 语法、审核契约、四类清理失败行为、Compose 静态契约和 `git diff --check` 通过；任务书运行回退变异非零；独立复审 Critical 0、Important 0、Minor 0。
- 恢复/门禁：等待 DEV-002 审核推送后的新精确 HEAD；获批、逐 PR/HEAD 授权、DEV-002 Merge Commit 和 DEV-001 合并后复验完成前，TASK-005 继续锁定，Stage 6 禁止进入。
### FCP-TASK004-R6：真实运行脚本默认环境文件修复

- Status: Pending DEV-002 Re-review
- Branch: `codex/task-004-ragflow-infra`
- Functional Commit: `78e3132d907870f17980ade7142f7c9a7ae7562e`
- Scope: `verify.ps1`、`verify-persistence.ps1` 默认 `.env.local` 与缺失文件失败契约。
- Verification: 审核契约、清理失败行为、Compose、PowerShell、Python 3.13、真实健康/隔离/持久化均通过。
- Boundary: PR #27 新 HEAD 获 DEV-002 批准前不稳定、不解锁 TASK-005。

### FCP-004：TASK-004 独立 RAGFlow 基础设施集成检查点

- Status: Stable after governance closeout merge
- Scope: 独立 RAGFlow、MySQL、Redis、MinIO、Elasticsearch 8.11 Compose 环境；健康、隔离、持久化和运行环境契约。
- Branch / PR: `codex/task-004-ragflow-infra` / PR #27。
- Approved Head: `76732606412d71239d302e4e9e5a0da6b364fd70`。
- Merge Commit: `87e8e3c0aab62ee9105bf3807b23fcf44ac15137`。
- Verification: DEV-002 Approved；合并后 Python 3.13 `5 passed, 1 warning`；PowerShell 审核/清理失败/Compose 契约 PASS；5 容器 healthy；Web/API 200；网络隔离 PASS；四存储重启恢复 PASS，容器重建 0、探针清理 4。
- Regression Coverage: `.env.local` 默认值与缺失失败、固定镜像摘要、日志秘密扫描、内部依赖零宿主端口、四存储持久化。
- Restore Options: `git revert -m 1 87e8e3c0aab62ee9105bf3807b23fcf44ac15137` 仅作为代码回退候选；命名卷删除属于数据删除，必须另行授权。
- Notes: 历史 Pending 条目保留用于审计；本治理 PR 合并后由本条作为当前稳定检查点。TASK-005 可据此启动，Stage 6 仍未获准。

### FCP-006-FE：正式前端工程基础集成检查点

- 状态：PR #33 已正式集成并完成最小技术回归；本治理收尾 PR 合入前，不据此解锁 TASK-006 或 TASK-007 的前端子范围，也不构成 Stage 6 依据。
- 分支/审核/合并：`codex/task-006-fe-frontend-foundation`；功能提交 `800e7a43fcc6ae98f00e74d738924c236c84b118`，DEV-001 批准的最终 HEAD `a9c4fc0a2f651ed7465d8d2003342cb94d6f1629`，PR #33 由 DEV-001（`ll979053897-arch`）手动 Merge Commit 合入 `codex/stage-05-integration`，合并提交 `25737f52a7e113224606cef6dbd3de49dbf7e4f4`。
- 范围：React + Vite + TypeScript 前端工程、Vitest 测试基础、共享应用壳和非业务 `fetch` JSON 边界；原型仅作视觉参考，代码没有运行时原型引用。
- 运行基线：`package.json` 声明 Node `^20.19.0 || >=22.12.0`、npm `>=10.0.0`；本轮使用 Node `v26.5.0`、npm `11.17.0` 并执行 `npm ci`。
- 证据：前端 2 项测试通过、生产构建通过、全部现有原型静态检查通过、`git diff --check` 通过。
- 合并后证据：前端 2 项测试通过、生产构建通过、14 项原型静态回归通过、`git diff --check` 与合并树检查通过；浏览器人工视觉回归未执行。
- 恢复/门禁：可选择性回退该任务合并提交；不涉及数据或生产操作。本治理收尾 PR 合入后，TASK-006 智能配置前端子范围与 TASK-007 共享前端对话子范围可按各自任务书、PR、审核和授权门禁继续；TASK-010 仍受 TASK-003、TASK-008、TASK-009 依赖约束，Stage 6 仍未获准。

### FCP-006-R1：TASK-006 全范围审核候选

- 状态：Review Candidate / Not Approved / Not Integrated / Does Not Unlock Dependencies。
- 分支/PR：`codex/task-006-agent-config` / PR #14；候选包含最新 `codex/stage-05-integration` 同步、四 Agent 智能配置前端与单链 Alembic 修复。
- 验证：前端 7 项测试及生产构建通过；Python 3.13.14 TASK-003/006 迁移回归 `7 passed, 1 warning`、全量后端 `221 passed, 9 skipped, 1 warning`；`compileall`、单一 Alembic head 与 `git diff --check` 通过。
- 风险与恢复：该候选未执行 Docker/PostgreSQL 真实环境验证，须由具备环境的 DEV-001 核验；合并前退回该 PR 追加提交即可，不涉及数据删除。新 HEAD 会使旧审核结论失效，必须重审并重新取得逐 PR/HEAD 合并授权。

### FCP-006：TASK-006 四 Agent 独立配置集成检查点

- 状态：Stable after post-merge governance closeout。
- 分支/PR：`codex/task-006-agent-config` / PR #14；获批源 HEAD `e564b15f42492087578d03c3a1f5412c9db35f6b`；DEV-001 手动 Merge Commit `da460c64f48e1b1522979d2e5f381fb797571934`。
- 合并后验证：DEV-001 集成检查确认目标分支、祖先关系、merge-tree 与授权 HEAD 一致；前端 7 tests/build、后端 `221 passed / 9 skipped / 1 warning`、PostgreSQL 迁移往返通过。
- 范围/依赖：四 Agent 独立配置、首次单独初始化、模型能力与深度思考校验、正式智能配置前端和 `0004_task006` 单链迁移已集成；TASK-007 可按自身门禁继续，Stage 6 仍未获准。
- 回滚：应用可评估 `git revert -m 1 da460c64f48e1b1522979d2e5f381fb797571934`；迁移回退按已验证 downgrade 或前向修复策略处理，生产数据回退须另行授权。

## FCP-003-R1：TASK-003 本地开发候选

- 状态：Development Candidate / Locally Validated / Not Pushed / Not Reviewed / Not Integrated / Does Not Unlock Dependencies。
- 分支/基线：`codex/task-003-maintenance-lifecycle`；最新集成基线 `f135997a6ecc009de75735b673499b475615a717`；同步 Merge Commit `4877dcdc301b97d884a43883a5584fdee1d28c41`。
- 范围：故障上报、直接/采纳诊断开始维修、维修完成、人工最终字段、结构化历史案例与相似案例查询、活跃故障设备停用保护、Alembic `0003_task003`。
- 验证：Python 3.13.14 模块回归 `168 passed, 1 warning`；专用 PostgreSQL 17 迁移、事务、幂等及并发 `4 passed, 1 warning`；`compileall`、单一迁移 head、平台/RAGFlow Compose 配置及 `git diff --check` 通过。
- 边界：相似案例只查询 PostgreSQL，不调用 RAGFlow、Agent 或外部网络；无新增生产依赖、兼容层、通用抽象、前端、TASK-004/005/006/008 实现或无关修改。
- 恢复/门禁：本地提交完整且工作树干净；尚未推送同一 Draft PR，DEV-002 尚未审核。不得据此解锁 TASK-009/010/011，不得进入 Stage 6。

## FCP-003：TASK-003 维修闭环集成检查点

- 状态：Stable after this governance closeout is merged。
- 范围：故障上报、DIRECT/ADOPTED 开始维修、人工维修结果、结构化历史案例与相似案例查询、活跃故障设备停用保护、Alembic `0003_task003`。
- 分支/PR：`codex/task-003-maintenance-lifecycle` / PR #32。
- 获批 HEAD：`8960b5d8ab1e7073036c6151744233e26c15c9e9`。
- Merge Commit：`51337db767eb94051f78a5c537a3ff48d428a742`；第一父为 `f135997a6ecc009de75735b673499b475615a717`，第二父为获批 HEAD。
- 合并后证据：Python 3.13.14 `173 passed, 9 skipped, 1 warning`；专用 PostgreSQL 17 `4 passed, 1 warning`；Alembic 单一 `0003_task003 (head)`；平台/RAGFlow Compose、compileall、Merge diff check 均通过。
- 边界：相似案例只访问 PostgreSQL；无 RAGFlow、Agent、向量、正式前端、新生产依赖、兼容层或范围外实现。
- 恢复：应用回退可评估 `git revert -m 1 51337db767eb94051f78a5c537a3ff48d428a742`；`0003_task003` downgrade 会删除五张 TASK-003 表，生产数据回退须备份并另行授权，优先采用前向修复迁移。
- 依赖：本治理 PR 合入后，TASK-003 前置正式满足；TASK-009/010/011 仍受各自其余依赖约束，Stage 6 仍未获准。
## FCP-005-R1：TASK-005 RAGFlow 适配器契约检查点

- 状态：Development Candidate / Locally Validated / Not Reviewed / Not Integrated。
- 分支/基线：`codex/task-005-knowledge-ragflow` / `8c0087928f693674f498044b0e2dbbe96196847c`；功能提交 `b6325cdaf5a412a9b074cc215576292a1b6b1afe`。
- 范围：RAGFlow v0.25.6 文档上传后解析、状态映射、删除、仅 READY 文档检索、业务文档/切片引用映射、空检索与超时降级；不包含业务元数据/API、数据库迁移、真实对象存储或 Worker 调度。
- 证据：RED 为 `ModuleNotFoundError: app.integrations`；定向测试 `9 passed`；Python 3.13 全量 `182 passed, 9 skipped, 1 warning`；`compileall` 和 `git diff --check` 通过。
- 边界：使用 Python 标准库 HTTP 客户端，无新增生产依赖、兼容层或范围外修改。真实 RAGFlow 上传/解析/检索与重启验证仍须由具备 Docker 环境的 DEV-001 执行。
- 恢复/门禁：可回退功能提交。TASK-005 尚未完成；后续功能继续在同一 Draft PR，最终精确 HEAD 经 DEV-001 审核、集成检查和项目负责人授权后，只能由 DEV-001 合并；Stage 6 仍未获准。
## FCP-005-R2：TASK-005 知识文档生命周期检查点

- 状态：Development Candidate / Locally Validated / Not Reviewed / Not Integrated。
- 分支/功能提交：`codex/task-005-knowledge-ragflow` / `95f5d31aeb7f41864f2c0dfd860cde6cc7ff6dfa`；继续维护 Draft PR #37。
- 范围：知识数据集、业务文档和引用模型；对象存储引用、100MB 上限、Worker 上传同步、状态刷新、安全失败原因、仅 READY 文档检索以及远端优先删除。共享 Alembic 迁移仍由 DEV-001 集成。
- 证据：知识/RAGFlow 定向 `17 passed, 1 warning`；Python 3.13 全量 `190 passed, 9 skipped, 1 warning`；`compileall` 与 `git diff --check` 通过。
- 边界：未新增生产依赖、公开 API、迁移、对象存储客户端、扫描器、兼容层或范围外修改。真实 MinIO/RAGFlow/Worker 联调仍未执行。
- 恢复/门禁：可回退本功能提交。TASK-005 仍处于 Draft 开发；最终精确 HEAD 经 DEV-001 审核、集成检查和项目负责人授权后，只能由 DEV-001 合并；Stage 6 仍未获准。
## FCP-005-R3：TASK-005 安全上传 API 检查点

- 状态：Development Candidate / Locally Validated / Not Reviewed / Not Integrated。
- 分支/功能提交：`codex/task-005-knowledge-ragflow` / `f9fc4a0ed2a04249640d569de08c41f17aa4b684`；继续维护 Draft PR #37。
- 范围：经项目负责人批准新增 `minio` 与 `python-multipart`；实现 MinIO 随机对象键和限定 bucket 访问、ClamAV 失败关闭扫描、100MB multipart 上传、`intelligence:knowledge` 权限、幂等、成功/失败审计、文件元数据与文档状态查询 API。
- 证据：知识范围定向 `28 passed, 1 warning`；Python 3.13 全量 `200 passed, 9 skipped, 1 warning`；`pip check`、`compileall` 与 `git diff --check` 通过。
- 边界：未增加 Alembic 迁移或 Docker/部署配置；共享迁移仍由 DEV-001 集成，平台 MinIO 与 ClamAV 真实服务、RAGFlow 真实联调尚待 DEV-001 环境验证。无兼容层或范围外修改。
- 恢复/门禁：可回退本功能提交。TASK-005 仍处于 Draft 开发；最终精确 HEAD 经 DEV-001 审核、集成检查和项目负责人授权后，只能由 DEV-001 合并；Stage 6 仍未获准。
## FCP-005-R4：TASK-005 Worker 同步检查点

- 状态：Development Candidate / Locally Validated / Not Reviewed / Not Integrated。
- 分支/功能提交：`codex/task-005-knowledge-ragflow` / `5e134655bc087f972e84f8f40b31bac284ee6c29`；继续维护 Draft PR #37。
- 范围：批量扫描 `UPLOADING/PARSING` 文档；从已扫描 MinIO 对象读取并调用 RAGFlow 上传/解析；刷新远端生命周期；对象存储或同步异常写入固定安全失败原因；批量上限 500。
- 证据：Worker 定向 `3 passed, 1 warning`；Python 3.13 全量 `204 passed, 9 skipped, 1 warning`；`compileall` 与 `git diff --check` 通过。
- 边界：未新增 Alembic 迁移、Docker/部署配置或队列依赖；共享迁移、真实 Worker 调度、MinIO/RAGFlow/ClamAV 联调仍待 DEV-001 环境验证。
- 恢复/门禁：可回退本功能提交。TASK-005 仍处于 Draft 开发；最终精确 HEAD 经 DEV-001 审核、集成检查和项目负责人授权后，只能由 DEV-001 合并；Stage 6 仍未获准。

## FCP-007：TASK-007 Agent Runtime 开发候选

- 状态：Development Candidate / Ready for review 前；未集成，不解锁下游任务。
- 分支：`codex/task-007-agent-runtime`；功能提交 `7c3cf64fe7537ca8f7e05c66e4d5a71ff3383e61`；目标 `codex/stage-05-integration`。
- 范围：AgentThread/AgentRun/ToolCall/AgentConfirmation 持久化模型、线程创建者/管理员访问控制、配置快照、provider-neutral 推理参数映射、持久化 checkpoint、SSE 状态事件与恢复接口；新增 Alembic `0005_task007`。
- 验证：Python 3.13 全量后端 `224 passed, 9 skipped, 1 warning`；TASK-007 定向测试 `2 passed`；迁移检查、`compileall` 与 `git diff --check` 通过。唯一警告为既有 Starlette/httpx 弃用提示。
- 边界：未引入 LangGraph 或其他新生产依赖；真实外部模型、容器和 PostgreSQL checkpoint 联调仍待 DEV-001 环境验证；无原始思维链入库或出流。
- 回滚：应用可选择性回退提交 `7c3cf64fe7537ca8f7e05c66e4d5a71ff3383e61`；`0005_task007` downgrade 会删除四张 Runtime 表，生产数据回退须另行授权并先备份。

## FCP-007-R1：TASK-007 LangGraph 修订候选

- 状态：Development Candidate / 等待 DEV-001 PostgreSQL 专用环境复验；未集成，不解锁下游任务。
- 依赖授权：项目负责人已授权新增 LangGraph 生产依赖。
- 新增依赖：`langgraph>=0.6,<0.7`、`langgraph-checkpoint-postgres>=2.0,<3.0`。
- 实现：真实 StateGraph runtime；生产 PostgreSQL 使用 `PostgresSaver`，同一 `thread_id` 支持 checkpoint resume；本地 SQLite 测试使用内存 saver。
- 验证：Python 3.13 全量 `226 passed, 10 skipped, 2 warnings`；Runtime `4 passed`；`compileall`、`git diff --check` 通过。未完成 Docker/PostgreSQL 真实环境验证。

## FCP-007-R2：TASK-007 Resume 与持久化恢复修订候选

- 状态：Development Candidate / 等待 DEV-001 PostgreSQL 专用环境复验；未集成，不解锁下游任务。
- 修订：resume 写入纳入幂等重放/409；LangGraph saver 恢复先读取同一 `thread_id` 历史 checkpoint，再合并 `resume`/`confirmation` 白名单输入；PostgreSQL 集成测试覆盖首存、恢复和历史 state 保留。
- 验证：Python 3.13 全量 `227 passed, 10 skipped, 2 warnings`；Runtime/集成定向 `5 passed, 1 skipped`；compileall/diff-check 通过。
- 未验证：当前无专用 PostgreSQL DSN，真实 PostgresSaver 测试跳过；需 DEV-001 执行后才能重新请求 Ready 审核。

## FCP-007-R3：TASK-007 PostgreSQL DSN 修订候选

- 状态：Development Candidate / 等待 DEV-001 PostgreSQL 17 专用环境复验；未集成，不解锁下游任务。
- 修订：集成测试使用 `create_database_engine()` 的 psycopg v3 路径；LangGraph PostgresSaver 使用 libpq URL 规范化；新增转换回归。
- 验证：Python 3.13 全量 `228 passed, 10 skipped, 2 warnings`；定向 `6 passed, 1 skipped`；compileall/diff-check 通过。
- 未验证：本地没有专用 PostgreSQL DSN，真实 checkpoint/restart 仍待 DEV-001 执行。

## FCP-005-R5：TASK-005 真实 RAGFlow 联调与集成基线同步候选

- 状态：Review Candidate / 真实环境门禁已满足 / 等待 DEV-001 审核新精确 HEAD / 未集成。
- 分支/PR：`codex/task-005-knowledge-ragflow` / PR #37；真实联调对象为 `9375d12853248ceb39068f509a8dbd95bf717ce5`，随后同步当前集成基线并保留 TASK-005 与已集成模块的共同路由和生产依赖。
- 真实证据：上传、ClamAV 恶意附件拒绝、RAGFlow 解析、`READY`、混合检索和引用回传 `1 passed`；临时数据集、容器、网络、卷已清理，共享 RAGFlow 五项服务仍 healthy。
- 回归证据：Python 3.13 后端 `217 passed, 11 skipped`；`compileall`、验证脚本契约和 `git diff --check` 通过；三轮复核 Critical 0、Important 0、Minor 0。
- 同步后回归：Python 3.13.14 全量后端 `259 passed, 10 skipped, 2 warnings`；`pip check`、`compileall` 与暂存 diff check 通过。
- 恢复/门禁：应用可按 TASK-005 功能提交选择性回退；外部文档删除仍受业务删除与审计规则约束。新 HEAD 须由 DEV-001 重新审核并完成集成与授权流程；此前不解锁下游、不进入 Stage 6。

## FCP-007：TASK-007 Agent Runtime 合并后技术检查点

- 状态：Stable after post-merge governance closeout；依赖矩阵允许的下游可继续，Stage 6 仍未获准。
- 分支/PR：`codex/task-007-agent-runtime` / PR #40；源 HEAD `fcd643ab0b0e33a585e3be6ec0b0036a611059c4`；Merge Commit `bf842626987148575173c6cf3f34970fc496ad7c`。
- 合并关系：第一父 `fdec916fad943acb8ad62a1cf5bc3ce8f770cc8d`，第二父为源 HEAD；源 HEAD 已成为集成分支祖先。
- 合并后证据：后端 `228 passed, 10 skipped, 2 warnings`；PostgreSQL 17 真实 `PostgresSaver` checkpoint/restart `1 passed, 1 warning`；`compileall`、Compose 配置、API 镜像构建、PostgreSQL/Redis healthy、容器 `/healthz` HTTP 200、merge-tree 与 `git diff --check` 通过。
- 治理门禁：需纯治理 PR 同步 SELF_TEST、CHECKPOINTS、CODE_REVIEW、COMMIT_LOG、任务书、`workflow/DEV_TO_PM_HANDOFF.md` 与 `workflow/state.json`；追认及治理 PR 合入前 Stage 6 仍未批准。

## FCP-005-R3：TASK-005 审核整改中间检查点

- 状态：Draft / Changes Requested / Partially Remediated / Not Approved / Not Integrated。
- 分支/PR：`codex/task-005-knowledge-ragflow` / PR #37；审核基准 HEAD `1cee0317ab1eefca2ca4900e2e97804ae1448665`。
- 已关闭范围：可执行 Worker 模块入口及其 TDD；可选真实 PostgreSQL/MinIO/ClamAV/RAGFlow 生命周期测试；安全校验 PowerShell 调用脚本。
- 本地证据：全量后端 `261 passed, 11 skipped, 2 warnings`；新增/Worker 定向 `5 passed, 1 skipped, 2 warnings`；`pip check`、`compileall`、`git diff --check` 通过。
- 未关闭范围：知识三表的共享 Alembic revision 需 DEV-001 决定并取得项目负责人对具体迁移范围的确认；真实联调必须在完整新 HEAD 上由 DEV-001 重跑。
- 恢复/门禁：本检查点仅为可恢复整改提交，不是 Review Candidate；PR 保持 Draft，不解锁 TASK-009/011，不进入 Stage 6。
- 迁移增量：DEV-001 原提交 `2fe848bfb5f7f7849b950cbecfa40644e6782a05` 已由 DEV-002 cherry-pick 为 `78ad1c81f6292c1fc3706b35d9dd495a8244d1b4`；四表迁移链为 `0005_task007 -> 0006_task005`，PostgreSQL 17 往返 `1 passed`。
- 合入分支后回归：全量 `262 passed, 12 skipped, 2 warnings`；`pip check`、`compileall`、单一 head 和 diff check 通过。真实 RAGFlow/ClamAV 复验仍待 DEV-001，因此状态继续为 Draft / Not Approved。
- 验证基础设施增量：DEV-001 分支 `codex/task-005-validation-infra` 的三提交已由 DEV-002 连续 cherry-pick 至 PR #37；验证专用 Compose 服务限制在 `validation` profile，临时凭据和清理入口具备 marker/GUID/固定文件名约束，Worker 以独立 Compose 进程轮询推进 `READY`。DEV-002 本地回归 `266 passed, 12 skipped, 2 warnings`，定向 `10 passed, 2 skipped, 2 warnings`；Docker/PowerShell 本机不可用，真实联调和脚本语法结果仍待 DEV-001 对新 HEAD 绑定复审。
- 治理门禁：项目负责人已追认 PR #40、源 HEAD、Merge Commit 及合并结果；PR #41 Merge Commit `092eb84821131f6c6faa6b6a1c2acdb4079ecf8f` 已同步 SELF_TEST、CHECKPOINTS、CODE_REVIEW、COMMIT_LOG、任务书、`workflow/DEV_TO_PM_HANDOFF.md` 与 `workflow/state.json`。TASK-007 治理闭环完成；Stage 6 仍未批准。

## FCP-008-R1：TASK-008 AI 故障上报与指标读取开发候选

- 状态：Development Candidate / PR #43 Ready for review / 未审核、未集成，不解锁下游任务。
- 分支/基线：`codex/task-008-fault-metric-agents`，基于 `origin/codex/stage-05-integration@78e9dfb`。
- 范围：受控故障草稿字段采集与人工确认门禁；固定 40 项指标目录、最多五项批量查询、合法维度校验；健康分受控读取失败时返回 `UNAVAILABLE` 且不伪造分值；新增指标只读 API。
- 验证：Python 3.13.14 专项 `12 passed, 2 warnings`；完整后端 `240 passed, 10 skipped, 2 warnings`；`git diff --check` 通过。警告为既有 Starlette/httpx 与 LangChain serializer 弃用提示。
- 边界：未新增生产依赖、数据库迁移、兼容层或通用抽象；未实现诊断 Agent、模型计算指标/健康分或修改 TASK-005；健康分公开路由留待既有冻结 API 边界，避免 TASK-002 路由表冲突。
- 门禁：PR #43 已绑定候选；当前精确 HEAD 变化后旧审核请求立即失效。等待 DEV-001 按新精确 HEAD 审核；不得自批、自合并、请求 Merge 授权、解锁 TASK-009/010/011 或进入 Stage 6。

## FCP-008-R2：TASK-008 DEV-001 P1 修复候选

- 状态：Development Candidate / P1 已修复 / PR #43 等待 DEV-001 对新精确 HEAD 复审；未集成、不解锁下游。
- 修复：确认提交通过既有 `maintenance_service.create_fault_report`、权限、幂等和审计边界写入业务故障；新增 `/api/agent/fault-reports/submit`；健康分读取器接入 `/api/agent/health-score/{equipment_id}`，服务不可用返回 `UNAVAILABLE`；`get_health_score` 纳入工具白名单。
- 当前 PR HEAD：`24153155da11dac0579466c05c8a04c7371e8904`。
- 验证：后端全量 `244 passed, 10 skipped, 2 warnings`；专项故障/指标 `14 passed, 2 warnings`；compileall、JSON 解析和 `git diff --check` 通过。
- 门禁：旧 HEAD `4e6aec342849f60fdd281c083f3a21147bc7d866` 的 Changes requested 已针对同一 PR 修复；等待 DEV-001 绑定新 HEAD 复审，不请求 Merge 授权、不合并、不解锁下游或进入 Stage 6。

## FCP-008-R3：TASK-008 幂等冲突修复候选

- 状态：Development Candidate / P1 修复完成 / PR #43 等待 DEV-001 对新精确 HEAD 复审；未集成、不解锁下游。
- 修复：`/api/agent/fault-reports/submit` 捕获 `IdempotencyKeyReused` 并返回 `409 IDEMPOTENCY_KEY_REUSED`；新增同请求重放、不同请求体冲突、故障记录和成功审计无重复回归测试。
- 当前 PR HEAD：待本次证据提交后以 GitHub PR 当前完整 HEAD 绑定。
- 验证：专项 Agent 测试 `15 passed, 2 warnings`；完整后端 `245 passed, 10 skipped, 2 warnings`；compileall、`git diff --check` 通过。
- 门禁：仍不得请求 Merge 授权、合并、解锁下游或进入 Stage 6；等待 DEV-001 重新审核。

## FCP-008-R4：TASK-008 不完整草稿错误契约修复候选

- 状态：Development Candidate / P1 修复完成 / PR #43 等待 DEV-001 对新精确 HEAD 复审；未集成、不解锁下游。
- 修复：确认提交捕获 `MissingFaultFieldsError`，返回 `422 FAULT_DRAFT_INCOMPLETE` 和缺失字段；失败不写故障记录、不写成功审计、不保存成功幂等响应。
- 验证：专项 Agent 测试 `18 passed, 2 warnings`；完整后端 `246 passed, 10 skipped, 2 warnings`；compileall、`git diff --check` 通过。
- 门禁：当前仍不得请求 Merge 授权、合并、解锁下游或进入 Stage 6。
- 证据校准：PR #43 当前待审 HEAD `ad50034ccb18422ac9a9c88325b9f0c4e9cb22dc`；专项 Agent 测试真实结果为 `18 passed, 2 warnings`，全量后端为 `246 passed, 10 skipped, 2 warnings`；`compileall`、JSON 解析和 `git diff --check` 通过。
- 当前门禁：PR #43 仍 Open/Ready for review，等待 DEV-001 对最新精确 HEAD 复审；未集成、未请求 Merge 授权、未解锁下游、Stage 6 禁止。

## FCP-008：TASK-008 合并后验证与治理收尾候选

- 集成：PR #43 获批 HEAD `19eaf1f213c50471f93b4e09e17df57bbeb1987b` 经项目负责人授权后，由 DEV-001 手动 Merge Commit `84ac8815cab403cb71a86230b4f705944bb5f6d2` 合入 `codex/stage-05-integration`；双亲为 `78e9dfb...` 与获批 HEAD。
- 合并后验证：Python 3.13 后端 `246 passed, 10 skipped, 2 warnings`；14 项 `06-testing/tests/*.test.js` 静态回归通过；compileall、`workflow/state.json` JSON 解析和 merge diff check 通过。
- 状态：PR #45 已获项目负责人确认并由 DEV-002 以 Merge Commit `997e50e10a7964b60fc8d9b4357c6274df8f0e97` 合入；治理闭环完成，TASK-008 可按依赖矩阵解锁下游，Stage 6 仍禁止。

## FCP-005-R6：TASK-005 PR #37 合并后治理收尾候选

- 状态：Closed post-merge governance completed / dependency unlock allowed.
- PR/版本：PR #37；获批 HEAD `cac10a06d2ef48914c14fb7ad955cedb36878acd`；Merge Commit `58fc0b12db1298333eef52c8720ec7d3d5e4846c`。
- 合并关系：第一父 `ca2a07f5f9f19620568cc75f74c97a2d10ed98d3`，第二父为获批 HEAD；结果树与获批候选一致。
- 证据：后端 `284 passed, 12 skipped, 2 warnings`；`pip check`、`compileall`、普通与 `validation` Compose 配置、JSON、merge-tree 与 `git diff --check` 通过；真实 PostgreSQL 17、MinIO、ClamAV、RAGFlow 和 Compose Worker 文档生命周期联调通过。
- 结果：PR #47 已获项目负责人确认并由 DEV-002 以 Merge Commit `6763f1e7199765c08303aa567c3aed40210f7cf7` 合入；TASK-005 治理闭环完成，可按依赖矩阵解锁 TASK-009，Stage 6 仍禁止。

## FCP-009-R1：TASK-009 操作指引与维修前诊断开发候选

- 状态：Development Candidate / Superseded by FCP-009-R2；未集成，不解锁下游任务，Stage 6 仍禁止。
- 分支/基线：`codex/task-009-guidance-diagnosis`，基于 `origin/codex/stage-05-integration@e0333e2196fc1db9dba0056021625972576215e2`；代码提交 `f78deace39fde732bcea7ec36f9a3f5eea79dfc1`。
- 范围：操作指引最多两次定向检索与人工降级；报警码具体数字/否定证据；维修前诊断的复现工况加第二类技术证据门槛；8 步、24 问、4 项证据上限；采纳预填摘要与直接开始清除临时摘要；历史案例与知识引用均通过外部受控回调边界提供。
- 变更边界：新增两个 Agent 模块、生产受控 API、TASK-003 历史案例和 TASK-005 知识引用回调、既有 DiagnosisDraft 写入，以及对应测试和 Runtime 工具白名单；未新增生产依赖、数据库迁移、兼容层或通用抽象，未修改 TASK-005。
- 验证：Python 3.13 Agent API/Runtime `8 passed, 2 warnings`；完整后端 `293 passed, 12 skipped, 2 warnings`；`node 06-testing/tests/fault-report-repair-agent.test.js` 通过；`compileall`、`git diff --check` 通过。警告为既有第三方弃用提示。
- 未验证：DEV-002 当前无 Docker 环境，未执行真实 Docker/PostgreSQL/RAGFlow/LLM 联调；真实 RAGFlow 引用与运行态降级由 DEV-001 在复审/集成阶段核验。
- 门禁：该候选已被 DEV-001 第二轮 `Changes requested` 取代；同一 Draft PR #49 继续维护，不得自批、自合并、申请 Merge 授权、解锁 TASK-010/011 或进入 Stage 6。

## FCP-009-R2：TASK-009 服务端受控诊断会话修复候选

- 状态：Development Candidate / Superseded by FCP-009-R3；未集成，不解锁下游任务，Stage 6 仍禁止。
- 分支/PR：`codex/task-009-guidance-diagnosis` / PR #49；代码修复提交 `8d4d4c48aaa4ee39d01be4cbb5cb18de374a784c`，最终候选 HEAD 以本证据提交推送后的 PR #49 完整 HEAD 为准。
- 修复范围：`POST /api/agent/fault-diagnosis` 不再接受客户端回传的完整 `session` 作为事实源；诊断状态保存在服务端 `DiagnosisDraft.read_only_summary._session`，客户端后续步骤只提交 `diagnosis_draft_id`。服务端校验草稿存在、归属用户、故障绑定和状态，READY 后重复提交只返回既有服务端结果，不重复创建草稿或成功审计。
- 回归覆盖：伪造 `DIAGNOSIS_READY`/根因的客户端 `session` 请求稳定 422；其他用户访问草稿返回 403；同一幂等 Key 重放返回原响应、不同请求体返回 `409 IDEMPOTENCY_KEY_REUSED`；READY 后不同 Key 重放不新增 `DiagnosisDraft` 或 `agent.fault_diagnosis.ready` 审计；既有 `/api/fault-reports/{fault_id}/start-repair` 的 `ADOPTED` 采纳路径仍通过。
- 验证：Python 3.13 Agent/Runtime/Maintenance 聚焦回归 `49 passed, 2 warnings`；完整后端 `293 passed, 12 skipped, 2 warnings`；14 项原型静态回归通过；`compileall`、`workflow/state.json` JSON 解析和 `git diff --check` 通过。警告为既有第三方弃用提示。
- 未验证：DEV-002 当前无 Docker 环境，未执行真实 Docker/PostgreSQL/RAGFlow/LLM 联调；真实 RAGFlow 引用与运行态降级由 DEV-001 在复审/集成阶段核验。
- 门禁：该候选已被 DEV-001 第三轮 `Changes requested` 取代；同一 PR #49 继续维护，不得请求 Merge 授权、合并、解锁 TASK-010/011 或进入 Stage 6。

## FCP-009-R3：TASK-009 诊断权限与服务端上下文修复候选

- 状态：Development Candidate / 第三轮 P1 已修复 / 等待 DEV-001 绑定新精确 HEAD 复审；未集成，不解锁下游任务，Stage 6 仍禁止。
- 分支/PR：`codex/task-009-guidance-diagnosis` / PR #49；代码修复提交 `e0c058e182d7c29881c3de75403b2ef0eb648de7`，最终候选 HEAD 以本证据提交推送后的 PR #49 完整 HEAD 为准。
- 修复范围：`POST /api/agent/fault-diagnosis` 创建可采纳诊断草稿时除 `intelligence:agent` 外必须具备 `fault:repair`；`start` 请求不再接受客户端 `equipment_model`、`symptom`、`description` 或 `dataset_ids`。诊断上下文从服务端 `FaultReport` 与 `Equipment` 生成，知识数据集从 `fault_diagnosis` Agent 配置读取并随服务端会话保存。
- 回归覆盖：仅有 `intelligence:agent` 的用户请求诊断草稿返回 403 且不创建 `DiagnosisDraft`；伪造客户端诊断上下文/数据集返回 422；成功路径检索问题绑定服务端设备型号、故障症状和描述，数据集绑定服务端 Agent 配置；既有越权、重放、READY 幂等和 `ADOPTED` 采纳路径继续通过。
- 验证：Python 3.13 故障诊断定向 `5 passed, 2 warnings`；Agent/Runtime/Maintenance 聚焦回归 `49 passed, 2 warnings`；完整后端 `293 passed, 12 skipped, 2 warnings`；14 项原型静态回归通过；`compileall`、`workflow/state.json` JSON 解析和 `git diff --check` 通过。警告为既有第三方弃用提示。
- 未验证：DEV-002 当前无 Docker 环境，未执行真实 Docker/PostgreSQL/RAGFlow/LLM 联调；真实 RAGFlow 引用与运行态降级由 DEV-001 在复审/集成阶段核验。
- 门禁：PR #49 新 HEAD 会使旧审核结论失效；等待 DEV-001 重新审核，不得请求 Merge 授权、合并、解锁 TASK-010/011 或进入 Stage 6。

## FCP-010-R2：TASK-010 前端集成候选

- 状态：Development Candidate / Draft PR #50 / 等待 DEV-001 对推送后的完整精确 HEAD 正式复审；未集成，不解锁 TASK-011 或 Stage 6。
- 分支/目标：`codex/task-010-frontend-integration` → `codex/stage-05-integration`；功能检查点 `76d348620859e8931fed40bf316d4f94131b28ad`，最终候选以本次证据提交推送后的 PR #50 HEAD 为准。
- 范围：以正式前端调用既有维护和 Agent API，覆盖人工/AI 故障上报、健康分工作台、诊断分阶段呈现、仅服务端草稿 ID 的证据补充、直接/采纳维修、结果与受限摘要、操作指引引用及 Runtime SSE 状态。权限或 AI 不可用时保留人工上报、直接维修或人工操作流程。
- 验证：前端 Vitest `22 passed`；`npm --prefix codebase/frontend run build` 通过；14 项 `06-testing/tests/*.test.js` 静态回归通过；`git diff --check` 通过。
- 边界：未修改后端、数据库迁移、部署、生产依赖、Stage 3 原型或 Agent 配置页；未新增兼容层或通用抽象。
- 未验证：DEV-002 未执行带认证真实后端的浏览器端到端流、Docker/PostgreSQL/RAGFlow/LLM live-stack；这些需 DEV-001 在最终精确 HEAD 上复审/集成核验。
- 门禁：本记录只请求代码复审，不是 Merge 授权；不得合并、解锁 TASK-011 或进入 Stage 6。

## FCP-010-R3：TASK-010 Bearer 认证 P1 修复候选

- 审核输入：DEV-001 对 PR #50 的 `ec4e7be630f7bd40dc48ac731aba042e59993225` 提交 `Changes requested`；原前端 JSON、Agent 与 SSE 请求没有 Bearer 认证，会收到 `401 UNAUTHENTICATED`。
- 修复提交：`aac8ac098465da3792ffbee11caa73d5ee16bc9e`；最终候选以本证据提交推送后的 PR #50 完整 HEAD 为准。
- 修复范围：统一 API 边界从现有登录态 `sessionStorage.access_token` 读取 token，并仅在 token 存在时追加 `Authorization: Bearer …`；JSON 请求保留原有内容类型和幂等键，SSE `GET /api/agent/runs/{run_id}/events` 使用相同认证边界。
- 回归：新增 JSON 与 SSE 实际 fetch 初始化参数的 Bearer 断言；缺少 token 时不伪造认证头，后端继续作为唯一认证事实源。
- 验证：API 专项 `10 passed`；前端全量 `23 passed`；生产构建、14 项静态回归、`workflow/state.json` JSON 解析和完整 diff-check 通过。
- 门禁：旧审核结论已失效，等待 DEV-001 对新精确 HEAD 复审；不申请 Merge 授权、不合并、不解锁 TASK-011、不进入 Stage 6。

## FCP-010-R4：TASK-010 登录与受保护路由 P1 修复候选

- 审核输入：DEV-001 对 PR #50 的 `654439d8579d20ad67878607febc74e50bf652df` 提交 `Changes requested`；此前 token 只有测试写入，正式前端没有登录入口或未认证保护，首次使用会得到 401。
- 项目负责人已确认范围：在同一 PR 最小新增 `/login`、`/api/auth/login` 调用、`sessionStorage.access_token` 会话写入、未认证路由保护和交互回归；不修改后端认证规则或公开契约。
- 修复提交：`aef11599b0b820e7781abb5cb7faa83d8cb5b8b1`；最终候选以本证据提交推送后的 PR #50 完整 HEAD 为准。
- 行为：未认证用户访问既有页面会转到 `/login`；登录成功仅写入返回的 token 后回到原目标页；已认证用户访问 `/login` 回到工作台。JSON 与 SSE 继续在单一 API 边界读取该会话 token，登录请求本身不附带认证头。
- 验证：交互回归覆盖未认证重定向、成功登录写入 token、登录后受保护页面 JSON Bearer 请求；API 专项 `11 passed`，前端全量 `26 passed`，生产构建、14 项静态回归、`workflow/state.json` JSON 解析和完整 diff-check 通过。
- 未验证：DEV-002 未执行携带真实账号的浏览器 E2E 或 Docker/PostgreSQL/RAGFlow/LLM live-stack；请 DEV-001 在最终精确 HEAD 上复核。
- 门禁：仅请求代码复审，不是 Merge 授权；不得合并、解锁 TASK-011 或进入 Stage 6。

## FCP-010-R1：TASK-010 前端 API 客户端检查点

- 状态：已验证的开发检查点；PR #50 未审核、未集成，不解锁 TASK-011 或 Stage 6。
- 分支/提交：`codex/task-010-frontend-integration` / `3c37d6c3a85bc02c00b79b550b0622846d39e574`。
- 范围：正式前端的维护与 Agent API 类型、幂等 POST 边界，以及公开错误码映射；不修改后端、API 契约、原型、依赖或智能配置页。
- 验证：TDD 红灯证明维护 API 尚不存在；`npm --prefix codebase/frontend test -- src/api.test.ts` 为 `6 passed`，`npm --prefix codebase/frontend run build` 通过，`git diff --check` 通过。
- 回退：可单独回退该提交，不涉及数据、部署或生产操作。

## FCP-009-R8：TASK-009 可执行 RAGFlow 探针修复候选

- 状态：Development Candidate / PowerShell 原生参数传递 P1 已修复 / 等待 DEV-001 对最终 PR #49 精确 HEAD 复审与 live-stack 复验；未集成、不解锁下游，Stage 6 仍禁止。
- 修复提交：`913cb44b262e34e7d49e25162a1fb5bf3bfe113f`。
- 修复范围：删除 `Invoke-Validation.ps1` 通过 `python -c` 传递多行 here-string 的路径；新增可由 API 镜像直接运行的 `app.modules.knowledge.ragflow_probe`，脚本改用无源码参数的 `python -m` 执行。
- 回归覆盖：实际 Python 子进程启动探针模块，访问本地 HTTP RAGFlow stub 的 `/api/v1/datasets` 并验证 Bearer 认证；静态契约同时禁止旧 `$apiRagflowProbe` 并固定模块入口。
- 验证：相关 `20 passed, 2 warnings`；完整后端 `297 passed, 12 skipped, 2 warnings`；14 项原型静态回归、`compileall`、`workflow/state.json` JSON 解析和 `git diff --check` 通过。
- 未验证：DEV-002 当前 Mac 环境无 PowerShell/Docker 专用 live-stack，未用真实专用 RAGFlow Key 重跑 Windows Docker 脚本；需 DEV-001 在新精确 HEAD 上复验 Compose、容器探针、adapter、`/healthz` 和真实检索。
- 门禁：不得申请 Merge 授权、合并、解锁 TASK-010/011 或进入 Stage 6。

## FCP-009-R9：TASK-009 真实 RAGFlow Agent 路由验证候选

- 状态：Development Candidate / 第八轮唯一 Important 验证缺口已补齐 / 等待 DEV-001 对最终 PR #49 精确 HEAD 复审与 live-stack 执行；未集成、不解锁下游，Stage 6 仍禁止。
- 测试提交：`36c3bbd07f4033aabda4e43ff3f5ee9178696ce7`。
- 验证范围：在既有真实文档上传、ClamAV 扫描、Worker 解析并达到 READY 后，通过 `/api/agent/operation-guidance` 实际调用真实 `RagflowAdapter`，验证响应包含真实 chunk 引用和文档标记内容；再将 adapter 指向确定不可达地址，验证同一路由返回 `UNAVAILABLE`、空引用及 `manual_fallback=true`。
- 可重复执行：该验证属于现有 `test_task005_live_stack.py`，由 `Invoke-Validation.ps1` 在隔离 validator 容器中自动运行，继续复用专用数据库、临时 RAGFlow dataset、MinIO 对象和统一清理流程。
- 本地验证：相关 `7 passed, 1 skipped, 2 warnings`；完整后端 `297 passed, 12 skipped, 2 warnings`；live Agent 一项因 DEV-002 无专用 live-stack 环境按设计跳过。
- 待 DEV-001：在新精确 HEAD 上用专用 RAGFlow Key 运行完整 `Invoke-Validation.ps1`，确认 live Agent 成功引用与不可用降级均实际通过。
- 门禁：不得申请 Merge 授权、合并、解锁 TASK-010/011 或进入 Stage 6。

## FCP-009-R6：TASK-009 Compose RAGFlow 配置传递修复候选

- 状态：Development Candidate / 第六轮 P1 修复 / PR #49 等待 DEV-001 对推送后的精确 HEAD 复审；未集成、不解锁下游，Stage 6 仍禁止。
- 修复提交：`0599bb6de23ddab736b6d2f44a795c8303bee655`。
- 修复范围：`api` Compose 服务显式传递 `RAGFLOW_BASE_URL`、`RAGFLOW_API_KEY`、`RAGFLOW_TIMEOUT_SECONDS`；安全 `.env.example` 为超时提供 `30`。这使已存在的应用工厂装配逻辑可在 Compose 容器内创建 `RagflowAdapter`。
- 回归覆盖：Compose 静态契约将三个变量限定断言在 `api` 服务块，并验证模板超时值；避免仅 `worker`/`validator` 配置变量而 API 长期降级。
- 验证：先观察新增契约断言在修复前失败，再转绿；相关 `18 passed, 2 warnings`，完整后端 `296 passed, 12 skipped, 2 warnings`，14 项原型静态检查、`compileall` 和 `git diff --check` 通过。
- 未验证：DEV-002 环境无 Docker 命令且无专用 live-stack 变量，未执行 Compose 容器内 adapter 断言、`/healthz` 或真实 RAGFlow 检索；这些由 DEV-001 复审/集成环境执行。
- 门禁：旧 `a173233d39d752fe5f025d1423d2038c54b685ba` 的审核结论已失效；不得申请 Merge 授权、合并、解锁 TASK-010/011 或进入 Stage 6。

## FCP-009-R7：TASK-009 API 容器 RAGFlow 连通性修复候选

- 状态：Development Candidate / 第七轮 P1 修复 / PR #49 等待 DEV-001 对推送后的精确 HEAD 复审；未集成、不解锁下游，Stage 6 仍禁止。
- 修复提交：`a25f32f90ddf812c7cc75c1a940d09d5077a2eb5`。
- 修复范围：`api` 服务复用既有 `host.docker.internal:host-gateway` 映射及受限 `ragflow-egress` 网络；TASK-005 验证环境补齐超时变量，验证脚本在 API 容器内解析配置 host，并以 Bearer 凭据请求 RAGFlow `/api/v1/datasets`。
- 回归覆盖：Compose 契约限定检查 API 的 host 映射、RAGFlow egress 网络、超时模板及容器探针命令；运行脚本以 30 次重试将 DNS 或连接失败作为验证失败。
- 验证：先观察 API 映射与验证脚本断言失败，再转绿；相关 `18 passed, 2 warnings`，完整后端 `296 passed, 12 skipped, 2 warnings`，14 项原型静态检查、`compileall` 和 `git diff --check` 通过。
- 未验证：DEV-002 环境无 Docker 与 PowerShell，未运行实际 Compose 配置、容器内探针、`/healthz` 或真实 TASK-009 RAGFlow 检索；这些由 DEV-001 复审/集成环境执行。
- 门禁：旧 `f920af89f7fbaefbb1f5547582ed4d44b44005ef` 的审核结论已失效；不得申请 Merge 授权、合并、解锁 TASK-010/011 或进入 Stage 6。

## FCP-009-R4：TASK-009 CR-043 正式基线收敛候选

- 状态：Development Candidate / 第四轮基线冲突修复 / 等待 DEV-001 绑定新精确 HEAD 复审；未集成，不解锁下游任务，Stage 6 仍禁止。
- 分支/PR：`codex/task-009-guidance-diagnosis` / PR #49；本次仅同步正式基线文档和治理台账，最终候选 HEAD 以本证据提交推送后的 PR #49 完整 HEAD 为准。
- 修复范围：按项目负责人已批准的 CR-043，将 PRD、SPEC、AC-037、需求追踪矩阵和 API 契约统一为“本期不实现 `EquipmentGrant` 或设备/工厂行级授权隔离”；AC-037 收敛为认证、路由权限、线程/草稿创建者隔离、服务端事实绑定、非法对象不泄露详情和审计。
- 变更边界：未修改 `codebase/`、测试、数据库迁移、生产依赖、部署或运行时配置；不新增兼容层或抽象层。
- 验证：`workflow/state.json` JSON 解析、`git diff --check` 和授权冲突词扫描通过；因无代码变更，未重跑后端测试，沿用上一代码 HEAD 的 DEV-001 独立验证证据。
- 门禁：PR #49 新 HEAD 会使旧审核结论失效；等待 DEV-001 重新审核，不得请求 Merge 授权、合并、解锁 TASK-010/011 或进入 Stage 6。

## FCP-009-R5：TASK-009 生产 RAGFlow Adapter 装配修复候选

- 状态：Development Candidate / 第五轮 P1 已修复 / 等待 DEV-001 绑定新精确 HEAD 复审；未集成，不解锁下游任务，Stage 6 仍禁止。
- 分支/PR：`codex/task-009-guidance-diagnosis` / PR #49；代码修复提交 `655d4a2309251fd0bd0ae874787e63b73f35effd`，最终候选 HEAD 以本证据提交推送后的 PR #49 完整 HEAD 为准。
- 修复范围：`create_app()` 根据生产环境 `RAGFLOW_BASE_URL`、`RAGFLOW_API_KEY` 和 `RAGFLOW_TIMEOUT_SECONDS` 自动装配 `RagflowAdapter + UrllibRagflowTransport` 到 `app.state.knowledge_adapter`；显式传入 `knowledge_adapter` 的测试/集成路径仍可覆盖。
- 回归覆盖：新增应用工厂回归验证 adapter 来自环境；新增操作指引与故障诊断 API 回归，使用真实应用工厂、真实 `UrllibRagflowTransport` 和本地 HTTP RAGFlow stub，不再手动注入 `app.state.knowledge_adapter` 或 monkeypatch 知识服务。
- 验证：新增相关文件 `16 passed, 2 warnings`；Agent/Runtime/Maintenance 聚焦回归 `51 passed, 2 warnings`；完整后端 `296 passed, 12 skipped, 2 warnings`；14 项原型静态回归、`compileall`、`workflow/state.json` JSON 解析和 `git diff --check` 通过。
- 未验证：当前 DEV-002 环境缺少 `TASK005_ALLOW_LIVE_TESTS=1` 和专用 RAGFlow/PostgreSQL/MinIO/ClamAV 环境变量，真实 RAGFlow 联调用例 `test_task005_live_stack.py` 为 `1 skipped`；需 DEV-001 在具备环境时执行 TASK-009 操作指引/故障诊断真实 RAGFlow 检索联调。
- 门禁：PR #49 新 HEAD 会使旧审核结论失效；等待 DEV-001 重新审核，不得请求 Merge 授权、合并、解锁 TASK-010/011 或进入 Stage 6。
## FCP-012-CR048 治理候选合并后检查点（2026-07-31）

- 状态：`INTEGRATED_PENDING_FORMAL_START_NOTICE`
- 范围：记录 CR-048 治理候选 PR #73 的正式合入，不包含业务代码、测试、迁移、依赖、Compose 或部署变更。
- 获批 HEAD：`b4e28368c1294f30b80f4dd72187660eba06fc10`
- Merge Commit：`8d9beaefe01baef38e54baecbe3426d9ab816623`
- 验证：双亲、目标分支指针、`git diff --check`、`workflow/state.json` JSON 解析通过；Python 3.13 后端 `319 passed, 13 skipped, 2 warnings`。
- 下一步：DEV-001 向项目负责人 DEV-002 发送正式 TASK-012 开发启动通知；确认前 API-002—007、P0 前端和 Stage 6/7/8 继续锁定。

## FCP-012-API-002—007 与 P0 前端实现检查点（2026-07-31）

- 状态：`DEVELOPMENT_IN_PROGRESS_SINGLE_DRAFT_PR`；仅记录当前实现检查点，不构成审核、集成、Merge 或 Stage 7 解锁。
- 范围：在 `codex/task-012-p0-frontend-remediation` 的唯一 Draft PR 中新增 BI、设备历史、维修记录、工单、审计与智能只读 API，并接入正式 React 路由、组织/设备/系统管理、智能审计与全局 Agent 入口。
- 约束：全部读取均使用现有 Bearer 会话和服务端真实事实；没有持久化的智能调用指标返回明确空集合，不伪造仪表盘数值；FAILED 知识文档可通过既有 Worker 队列重试。
- 本地验证：TASK-012 定向后端 `4 passed, 2 warnings`；既有模块全量 `265 passed, 2 warnings`；前端 `29 passed`、生产构建和 15 项 Node 静态检查通过。Docker/live-stack/浏览器验收未在 DEV-002 环境执行，留给 DEV-001 最终验证。

## FCP-012-API-002—007 与 P0 前端完整候选检查点（2026-07-31）

- 状态：`DEVELOPMENT_CANDIDATE_PENDING_FINAL_DEV001_REVIEW`；不构成审核、集成、Merge 或 Stage 7 放行。
- 当前分支：`codex/task-012-p0-frontend-remediation`；变更仍集中在唯一 Draft PR。
- 新增范围：API-002—007 真实读模型与参数边界；Agent 线程历史列表（创建者隔离）、线程详情/resume/SSE；维修记录知识筛选、设备趋势、工单状态筛选；AI 故障上报附件安全引用。
- 验证：前端 `49 passed`、生产构建；后端 `328 passed, 13 skipped, 2 warnings`、compileall；15 项 Node 静态回归；JSON 解析与 `git diff --check`。
- 回退：当前未提交；稳定单元仍可按文件/提交选择性回退。不得把本检查点 SHA 当成最终候选，最终 SHA 需在提交后重新记录。
- 未验证：macOS 无 Docker/PowerShell，未执行 Windows 隔离 live-stack、RAGFlow、ClamAV/MinIO、HTTPS、浏览器逐页 E2E。
- 下一步：完成完整 diff 和文档审计后提交同一 Draft PR，才可一次性请求 DEV-001 对完整候选审核。

## FCP-012：TASK-012 合并后治理闭环（2026-08-03）

- 状态：`CLOSED_POST_MERGE_GOVERNANCE_COMPLETED`；不构成 Stage 6 重测结论、Stage 7 验收或 Stage 8 发布授权。
- 代码集成：PR #75 获批 HEAD `a0bbfdbe7149a6b3a257f7456b9a6d190bec03d8` 已由 DEV-001 以 Merge Commit `9c8a787ba2ba51f4362bf6186b1c7d54cbe3e15c` 合入；双亲分别为 `86d620480382524737140d449b08aafdb4d6fd6b` 与获批 HEAD。
- 治理收尾：PR #76 获批治理 HEAD `dd4b24e1369527a98da04c5e34b1e7b193b84c07` 已由非作者 DEV-002 以 Merge Commit `477cb16e8a1e68d9d9325705d9d7db685fba9d86` 合入；其结果树等价于获批治理源。
- 证据：DEV-001 正式审核 `4840904555`、完整 live-stack、HTTPS MIME/health 和认证浏览器 E2E 均绑定 PR #75 的获批 HEAD；两次合并后的目标分支指针、祖先关系、Merge Tree、`git diff --check` 与 `workflow/state.json` 解析均通过。
- 下一步：以 `477cb16e8a1e68d9d9325705d9d7db685fba9d86` 作为新测试基线重启 Stage 6 独立验证；此前 Stage 7 和 Stage 8 保持锁定。

## FCP-013-01：工厂建模与工作台原型一致性整改（2026-08-04）

- 状态：`DEVELOPMENT_IN_PROGRESS_SINGLE_DRAFT_PR`；仅为 TASK-013 的可恢复开发检查点，不构成中途审核、集成、Merge 或任何 Stage 解锁。
- 分支/提交：`codex/task-013-prototype-fidelity-remediation` / `5e1b56a165eb5b392284a47a26bb1dfc5e60b715`。
- 范围：工厂建模从常驻新建表单改为组织树与节点详情双栏工作区；工作台改为风险总览、待办处置、快捷事项与已授权设备健康查询的工业操作台结构。所有业务内容仍来自正式 API，未引入原型运行源码或静态业务数据。
- 验证：`npm test -- --run src/WorkbenchPage.test.tsx src/PortalPages.test.tsx` 为 `21 passed`；`npm run build`、`git diff --check` 均通过。
- 边界：其余 TASK-013 页面和全局 Agent 尚未完成；PR #85 继续保持 Draft，完成全部整改后才统一提交 DEV-001 审核；Stage 6/7/8 继续锁定。

## FCP-013-02：共享应用壳原型一致性整改（2026-08-04）

- 状态：`DEVELOPMENT_IN_PROGRESS_SINGLE_DRAFT_PR`；仅为 TASK-013 的可恢复开发检查点，不构成中途审核、集成、Merge 或任何 Stage 解锁。
- 范围：统一正式业务导航、页面标题与面包屑、产品品牌、受控会话状态、真实登录用户名和退出入口；保留现有 fail-closed 会话与路由权限边界。
- 验证：`npm test -- --run src/App.test.tsx` 为 `11 passed`；`npm run build` 与 `git diff --check` 通过。
- 边界：全局 Agent 的流式呈现与其余页面域仍在整改；未新增生产依赖、兼容层或抽象层，PR #85 保持 Draft。

## FCP-013-03：登录与 BI 视觉层级整改（2026-08-04）

- 状态：`DEVELOPMENT_IN_PROGRESS_SINGLE_DRAFT_PR`；仅为 TASK-013 的可恢复开发检查点，不构成中途审核、集成、Merge 或任何 Stage 解锁。
- 范围：登录页改为品牌说明与受控访问表单的双栏布局；BI 趋势视图以正式 API 的实际序列生成语义化柱形趋势，不再使用纯文本列表替代图表。
- 验证：`npm test -- --run src/App.test.tsx src/LoginPage.test.tsx src/PortalPages.test.tsx` 为 `32 passed`；`npm run build` 与 `git diff --check` 通过。
- 边界：未新增生产依赖、模拟数据、兼容层或抽象层；排行、设备、现场作业、智能配置与系统管理页面仍待继续整改。

## FCP-013-04：系统管理分区与权限呈现整改（2026-08-04）

- 状态：`DEVELOPMENT_IN_PROGRESS_SINGLE_DRAFT_PR`；仅为 TASK-013 的可恢复开发检查点，不构成中途审核、集成、Merge 或任何 Stage 解锁。
- 范围：系统管理改为账号、角色权限、权限目录、审计事件四个正式数据分区；身份只读用户不再看见账号创建或状态切换入口，角色与审计仍使用既有正式 API。
- 验证：`npm test -- --run src/PortalPages.test.tsx` 为 `21 passed`；`npm run build` 与 `git diff --check` 通过。
- 边界：未新增生产依赖、模拟数据、兼容层或抽象层；现场作业、维修执行、全局 Agent 与智能配置页面仍待继续整改。

## FCP-013-05：Agent 流式状态增量呈现整改（2026-08-04）

- 状态：`DEVELOPMENT_IN_PROGRESS_SINGLE_DRAFT_PR`；仅为 TASK-013 的可恢复开发检查点，不构成中途审核、集成、Merge 或任何 Stage 解锁。
- 范围：全局 Agent、操作指引和 AI 故障上报改为在 SSE 回调到达时立即追加运行事件，不再等待流结束后才一次性显示状态；流读取失败仍沿用既有可见错误路径。
- 验证：`npm test -- --run src/App.test.tsx src/RepairExecutionPage.test.tsx src/PortalPages.test.tsx src/api.test.ts` 为 `60 passed`；`npm run build` 与 `git diff --check` 通过。
- 边界：未新增生产依赖、模拟数据、兼容层或抽象层；剩余页面的视觉与交互对照仍在本 PR 中继续。

## FCP-013-06：资产、维修、智能与现场作业工作区整改（2026-08-04）

- 状态：`DEVELOPMENT_IN_PROGRESS_SINGLE_DRAFT_PR`；本检查点仅记录可恢复代码单元，不构成中途审核、集成、Merge 或任何 Stage 解锁。
- 范围：设备台账增加正式资产汇总、状态筛选和列表工具栏；设备详情、新增/编辑及维修记录/详情改为资产、参数、历史和检索分区；智能配置分离模型与绑定、知识入口、Agent 控制面；故障上报及维修执行形成现场上下文与 AI 辅助区。所有内容仍来自既有正式 API 与权限状态。
- 验证：`npm test -- --run src/PortalPages.test.tsx src/IntelligentConfigPage.test.tsx src/FaultReportPage.test.tsx src/RepairExecutionPage.test.tsx` 为 `43 passed`；`npm run build` 与 `git diff --check` 通过。
- 边界：未新增生产依赖、公开 API、权限规则、迁移、部署配置、兼容层或抽象层；未提交既有 `codebase/frontend/.vscode/` 文件。AI 故障上报和逐页浏览器原型对照仍待本 PR 后续切片完成。

## FCP-013-07：智能审计与 AI 上报工作区整改（2026-08-04）

- 状态：`DEVELOPMENT_IN_PROGRESS_SINGLE_DRAFT_PR`；本检查点仅记录可恢复代码单元，不构成中途审核、集成、Merge 或任何 Stage 解锁。
- 范围：智能审计页调整为“受控调用概览”和“知识文档状态”两个真实数据区，保留知识写权限对重试操作的禁用边界；AI 故障上报页调整为 AI 受控收集、实时运行状态、正式写入边界与人工确认四个连续区域。未改动既有 API、权限、提交或 SSE 逻辑。
- 验证：`npm test -- --run` 为 `74 passed`；`npm run build` 通过；仓库根目录 15 项 Node 静态回归全部通过；`git diff --check` 通过。
- 边界：已启动当前工作树的本地预览，仅确认 `/login` 的实际页面结构与当前源码一致。其余 15 条受保护路由仍需使用真实隔离测试账号进行固定桌面视口的浏览器对照；不得通过伪造会话或静态数据绕过认证。未新增生产依赖、兼容层或抽象层，既有未跟踪 `codebase/frontend/.vscode/` 文件未触碰。

## FCP-013-08：工作台实时处置中心原型一致性整改（2026-08-06）

- 状态：`DEVELOPMENT_IN_PROGRESS_SINGLE_DRAFT_PR`；本检查点仅记录可恢复代码单元，不构成中途审核、集成、Merge 或任何 Stage 解锁。
- 范围：工作台按已批准原型恢复组织筛选、五项风险指标、处置提醒、故障待办标签、健康概览、今日处置、故障趋势和维修动态的信息架构；待办、指标、快捷入口和单设备健康分继续仅取自正式 API。
- 数据边界：正式 API 未提供组织范围、全局健康风险聚合、今日效率、趋势和维修动态；页面保留原型对应区域并呈现受控不可用状态，未填充原型示例数据或推测指标。
- 验证：串行 Vitest 全量 `88 passed`；生产构建通过；`git diff --check` 通过。
- 边界：未新增生产依赖、公开 API、权限规则、迁移、部署配置、兼容层或抽象层；未触碰既有未跟踪 `codebase/frontend/.vscode/`，也未纳入同时进行的 `RepairExecutionPage` 修改。

## FCP-013-09：维修记录双视图原型一致性整改（2026-08-06）

- 状态：`DEVELOPMENT_IN_PROGRESS_SINGLE_DRAFT_PR`；本检查点仅记录可恢复代码单元，不构成中途审核、集成、Merge 或任何 Stage 解锁。
- 范围：维修记录页按已批准原型恢复“维修概览”和“维修记录列表”两项视图；概览保留六项维修指标与四个分析图表的版面，列表保留正式设备 ID、知识状态、分页与维修档案查询。
- 数据边界：总维修次数取正式分页 API 返回的 `count`；全量状态、MTTR、MTBF、平均维修时间、完成率及四项图表没有正式 API 时均呈现受控空状态，未复用原型示例数据或用当前页记录推测汇总事实。
- 验证：维护记录专属 Vitest `6 passed`；`PortalPages.test.tsx` 全量 `30 passed`；生产构建和 `git diff --check` 通过。
- 边界：未新增生产依赖、公开 API、权限规则、迁移、部署配置、兼容层或抽象层；未纳入同时进行的设备详情、故障上报、维修执行或本地 `.vscode/` 修改。

## FCP-013-10：智能配置一级页签原型一致性整改（2026-08-06）

- 状态：`DEVELOPMENT_IN_PROGRESS_SINGLE_DRAFT_PR`；本检查点仅记录可恢复代码单元，不构成中途审核、集成、Merge 或任何 Stage 解锁。
- 范围：智能配置页恢复原型的“模型配置、智能体配置、知识库配置、调用记录、Token 消耗统计”五项一级页签；既有模型提供商/绑定、Agent 配置与知识文档上传均归入对应面板。
- 数据边界：调用记录和 Token 区域明确跳转至正式智能审计页面；当前正式接口没有实际 Token 消耗明细和图表统计，页面不填充原型示例值。
- 验证：新增页签契约先失败后转绿；`IntelligentConfigPage.test.tsx` 为 `4 passed`；生产构建和 `git diff --check` 通过。
- 边界：未新增生产依赖、公开 API、权限规则、迁移、部署配置、兼容层或抽象层；未纳入同时进行的设备详情、故障上报、维修执行或本地 `.vscode/` 修改。

## FCP-013-11：故障、设备详情与维修执行原型工作区整改（2026-08-06）

- 状态：`DEVELOPMENT_IN_PROGRESS_SINGLE_DRAFT_PR`；本检查点仅记录可恢复代码单元，不构成中途审核、集成、Merge 或任何 Stage 解锁。
- 范围：故障上报补齐查询筛选、列表、新增入口、基础信息、故障描述和现场附件模块；设备详情补齐健康摘要与图谱/BOM/参数/知识/维修记录分区；维修执行补齐执行进度、维修结果、受控草稿/附件/成本/工时边界和摘要复制入口。
- 数据边界：故障列表、设备健康、图谱/BOM/参数/知识、备件成本、工时、维修附件和草稿保存没有正式接口时均保留原型布局并禁用或呈现明确空状态；不伪造列表、评分、成本、工时或附件业务事实。
- 验证：`FaultReportPage.test.tsx`、`RepairExecutionPage.test.tsx` 与 `PortalPages.test.tsx` 共 `48 passed`；生产构建和 `git diff --check` 通过。
- 边界：未新增生产依赖、公开 API、权限规则、迁移、部署配置、兼容层或抽象层；未纳入本地 `.vscode/` 文件。

## FCP-013-12：设备新增与编辑分区原型一致性整改（2026-08-06）

- 状态：`DEVELOPMENT_IN_PROGRESS_SINGLE_DRAFT_PR`；本检查点仅记录可恢复代码单元，不构成中途审核、集成、Merge 或任何 Stage 解锁。
- 范围：设备新增与编辑表单恢复原型的设备 BOM 组成、设备额定参数和知识资料三个分区，以及对应的新增分支节点、新增参数和上传资料入口。
- 数据边界：当前正式 API 没有 BOM、额定参数或知识资料的公开读写契约；三个分区均呈现明确无数据说明且入口禁用，未写入 mock 数据、原型示例表格、客户端临时数据或新接口。
- 验证：设备分区定向 Vitest `1 passed`；`PortalPages.test.tsx` 为 `31 passed`；生产构建和 `git diff --check` 待本切片最终验证。全量前端测试当前为 `93 passed, 4 failed`，失败仅来自工作区中另一组未提交的 `LoginPage.test.tsx` 新增登录行为要求，未纳入本切片。
- 边界：未新增生产依赖、公开 API、权限规则、迁移、部署配置、兼容层或抽象层；不纳入或删除本地 `.vscode/`，也不纳入同时出现的 `LoginPage.test.tsx` 修改。

## FCP-013-13：登录页受控交互原型一致性整改（2026-08-06）

- 状态：`DEVELOPMENT_IN_PROGRESS_SINGLE_DRAFT_PR`；本检查点仅记录可恢复代码单元，不构成中途审核、集成、Merge 或任何 Stage 解锁。
- 范围：登录页恢复原型中的账号/密码字段校验、密码显示切换、记住密码控件、忘记密码弹窗、登录中提示、连续三次凭证失败后 30 秒临时锁定及解除提示。
- 数据边界：认证仍只调用正式登录 API；空字段不发起请求，忘记密码只提示联系系统管理员，未伪造账号、Token、角色或认证成功结果。
- 验证：登录页 Vitest `5 passed`；Portal 页面 Vitest `31 passed`；全量前端 Vitest `97 passed`；生产构建和 `git diff --check` 通过。
- 边界：未新增生产依赖、公开 API、权限规则、迁移、部署配置、兼容层或抽象层；不纳入或删除本地 `.vscode/`。

## FCP-013-14：TASK-013 全部 P0 页面候选收口（2026-08-06）

- 状态：`DEVELOPMENT_COMPLETE_PENDING_DEV001_REVIEW`；仅记录 TASK-013 完整候选，不构成审核批准、集成、Merge 或任何 Stage 解锁。
- 精确候选：`aaa55274ef953c3ec6d2fcb9a4bf7cf78b9cda72`，分支 `codex/task-013-prototype-fidelity-remediation`。
- 范围：16 个正式 React 路由和跨页全局 Agent 已按 `03-ui-prototype/prototype/pages/*.html` 的页面结构、信息层级、主要组件和状态边界完成代码对照；Data import 明确排除。
- 数据边界：只消费既有正式 API 和权限；健康聚合、BOM、额定参数、知识资料、BI 部分指标等契约缺失区域保留原型位置并呈现禁用/空态，不填充 mock 业务数据、不复制原型运行源码。
- 修改范围：前端页面、测试和样式；未新增生产依赖、公开 API、数据库迁移、权限模型、部署配置、兼容层或抽象层；既有 `codebase/frontend/.vscode/` 未跟踪目录未纳入。
- 验证：前端 `8 files passed / 97 tests passed`；`npm run build`（`tsc -b` 与 Vite production build）通过；15 项 Node 静态回归通过；`git diff --check` 通过。
- 未验证：除 `/login` 固定桌面视口只读检查外，15 条受保护路由的认证浏览器视觉对照、Windows Docker/RAGFlow/ClamAV/MinIO/HTTPS live-stack 和 ECS 部署同步未在本检查点宣称完成。
- 下一步：将该精确候选推送到远端后，请 DEV-001 统一进行一次正式整体审核；在审核、集成检查和项目负责人精确授权前，不转入 Stage 6。
