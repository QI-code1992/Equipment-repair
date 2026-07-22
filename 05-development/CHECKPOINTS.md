# 功能/页面检查点

静态原型检查点记录在 `03-ui-prototype/PROTOTYPE_CHECKPOINTS.md`，不得自动提升为生产检查点。

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
