# 自测

- 状态：Stage 5 开发自测与真实 PostgreSQL/Compose 验证已执行；Stage 6 独立测试和生产环境验收尚未执行
- 原型证据：Node 静态检查位于 `06-testing/tests/`，不属于生产测试。
- 必要生产检查：单元、API 契约、权限、健康分、Agent/RAGFlow 集成、安全、性能和端到端测试。
- 验收候选包必须绑定精确 Commit SHA 和最新结果。

## TASK-002 正式集成后治理收尾（2026-07-17）

- 正式合并记录：经 DEV-002 批准的任务分支 HEAD `2e89dcd8d8dff6af5b841f32ac0a7d5feb794e15` 已通过 PR #20 合入；集成负责人 DEV-001（`ll979053897-arch`）手动生成 Merge Commit `904886f48061e27c775f6ee2f8ddae99f5571ead`。
- 已归档验证：Python 3.13 `142 passed, 5 skipped, 1 warning`；真实 PostgreSQL 17 专项 `5 passed, 1 warning`；Compose 容器健康与容器内 `GET /healthz` 返回 HTTP 200。
- 本次变更仅为治理文档，不改动 `codebase/`，因此不重复运行上述业务测试；提交前仅运行文档范围的 JSON 解析、治理状态断言和 `git diff --check`。
- 治理合并：PR #25 已由 DEV-002（`QI-code1992`）以 Merge Commit `028da42eb9ab4b55ef981ac462e09993a31e8813` 合入。
- 结论：技术验证与治理收尾已完成。TASK-003、TASK-004 可按任务书启动；TASK-005 仍保持 TASK-004 依赖；TASK-006 已解除 TASK-002 前置，包括迁移、数据库集成和共享数据模型；Stage 6 仍需独立门禁。

## TASK-006 非数据库切片回归（2026-07-20）

- 同步后验证：Python 3.13.14 执行 `tests/modules/test_agent_config.py` 与 `test_agent_config_api.py`，结果 `24 passed, 1 warning`。
- 唯一 warning：第三方 Starlette TestClient 对 httpx 用法的弃用提示；无失败或跳过。
- 未验证：数据库、迁移、Docker、Compose、RAGFlow 和真实模型；相关验证由后续 TASK-006 代码及 DEV-001 环境核验承担。

## Task 1（2026-07-15）

- RED：在尚未实现 `service_name` 参数时运行健康检查，得到 `TypeError: create_app() got an unexpected keyword argument 'service_name'`；验证应用未配置场景确实尚未实现。
- 单元：`docker run --rm -v "${PWD}\\backend:/workspace" -w /workspace python:3.13-slim sh -c "pip install --disable-pip-version-check -q fastapi httpx pytest && pytest tests/test_health.py -q"`，结果 `4 passed, 1 warning`。警告来自 FastAPI/Starlette TestClient 对 `httpx` 兼容层的弃用提示，不影响断言结果。
- Compose：`docker compose --env-file infra/.env.example -f infra/docker-compose.yml config --quiet`，通过。
- 联调：`docker compose -p equipment-task1 --env-file infra/.env.example -f infra/docker-compose.yml up -d --build` 后，PostgreSQL 与 Redis 均显示 `healthy`；API 容器内实际请求 `http://127.0.0.1:8000/healthz` 返回 `{'status': 'ok', 'service': 'equipment-operations-platform'}`。

以上 Task 1 命令与结果是迁移前历史证据，保留原路径用于精确追溯。

## TASK-001 运行基线重新验证（2026-07-15）

- RED：`D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m pytest codebase/backend/tests/test_health.py -q` 在收集阶段失败；`app = create_app()` 命中重复定义并因 `Settings()` 缺少 `postgres_dsn`、`redis_url` 触发 `TypeError`。`docker compose --env-file codebase/infra/.env.example -f codebase/infra/docker-compose.yml config --quiet` 因顶层 `networks` 重复定义失败。
- GREEN：清理重复应用工厂、配置字段、Compose 服务与网络定义后，同一后端测试为 `4 passed, 1 warning`；警告为 FastAPI/Starlette 的 `httpx` 兼容层弃用提示，未影响断言。
- Compose：`docker compose --env-file codebase/infra/.env.example -f codebase/infra/docker-compose.yml config --quiet` 通过。
- 联调：`docker compose -p equipment-task1 --env-file codebase/infra/.env.example -f codebase/infra/docker-compose.yml up -d --build` 通过；PostgreSQL、Redis 状态为 `healthy`，API 容器内请求 `http://127.0.0.1:8000/healthz` 返回 `{'status': 'ok', 'service': 'equipment-operations-platform'}`。

## CR-032 目录迁移验证（2026-07-15）

- 当前后端测试入口：`pytest codebase/backend/tests/test_health.py -q`。
- 当前 Compose 校验入口：`docker compose --env-file codebase/infra/.env.example -f codebase/infra/docker-compose.yml config --quiet`。
- Stage 3 原型静态回归仍从 `06-testing/tests/*.test.js` 执行。
- 目录结构：`codebase/backend/`、`codebase/frontend/`、`codebase/infra/` 均存在；根目录旧路径和 `codebase/prototype/` 均不存在；通过。
- 原型回归：执行全部 `06-testing/tests/*.test.js`，14/14 通过。
- 后端与 Compose：后续由 TASK-001 重新验证，结果见“TASK-001 运行基线重新验证”。
- 路径与差异：目录断言和 `git diff --check` 通过；技能与工件参考中的归档规则一致性扫描通过。

## CR-038 PR #15 门禁违规合并补救（2026-07-16）

- 回滚前基线：`py -3.13 -m pytest tests -q` 为 `38 passed, 1 warning`；Compose 配置通过。
- 回滚方式：在隔离分支执行 `git revert -m 1 --no-commit e328cec64f1aa9c7cdc383579af042692dce5679`，审查暂存差异后提交为 `5d91e83679acefa5486a25bf5b921e9c12fd52d6`。
- 树状态：`git diff --name-status 42098613ffa20faed3bb0dcb842a0121722565bd` 仅显示 CR-038 的三份治理记录。
- Python 3.13：回滚后 `py -3.13 -m pytest tests -q` 为 `4 passed, 1 warning`。
- 静态检查：`py -3.13 -m compileall -q app tests` 通过。
- Compose：`docker compose --env-file ../infra/.env.example -f ../infra/docker-compose.yml config --quiet` 通过。
- 差异检查：`git diff --cached --check` 通过。
- 未执行：未启动容器和真实 PostgreSQL；本补救目标是恢复 PR #15 合并前的已验证 TASK-001 集成树，不重新验收 TASK-002。

### CR-038 合并后验证

- Merge Commit：`d37698c6e51df1701bbdfcf12ec6fa329241e0bd`，文件树与获批 PR 头 `9c1ff88a6842ffa1cb79bd63807b3d41d830d5bd` 一致。
- Python 3.13：`4 passed, 1 warning`；`compileall` 通过。
- Compose：配置、镜像构建和启动通过；PostgreSQL、Redis、API 均为 healthy。
- HTTP：API 容器内 `/healthz` 返回 `{"status":"ok","service":"equipment-operations-platform"}`。
- 清理：验证容器和网络已移除，未执行数据卷删除。
- 结论：CR-038 技术补救完成；该验证不验收 TASK-002，TASK-002 仍为 `Changes requested`。

## CR-037 PR #18 治理状态修正验证（2026-07-16）

- 修正提交：`e0f60f84d5ed31b693ad4f617b7b4c02ded0f718`。
- 任务书状态：旧的“v1.2 候选 / 等待批准 / 获批前暂停”当前状态措辞已清除；保留历史变更说明，不改写原审批记录。
- 任务矩阵：11 个 TASK 存在；TASK-002—011 均具备任务开发者、指定审核者、正式 PR 创建者、开发者不得自建正式 PR 和目标分支字段；开发者与审核者/PR 创建者不同。
- Python 3.13：`py -3.13 -m pytest codebase/backend/tests/test_health.py -q` 为 `4 passed, 1 warning`。
- 静态检查：`py -3.13 -m compileall -q codebase/backend/app codebase/backend/tests` 通过。
- Compose：`docker compose --env-file codebase/infra/.env.example -f codebase/infra/docker-compose.yml config --quiet` 通过。
- 治理文件：`workflow/state.json` 解析通过；`git diff --check` 通过。
- 范围：相对 `codex/stage-05-integration` 无 `codebase/` 修改；未运行容器启动和数据库验证，因为本修正仅涉及治理状态文本。

## CR-037 PR #18 合并后验证（2026-07-16）

- Merge Commit：`18485653a94cd033cfc82e8d6c7e40c35fcfbe33`。
- 树一致性：Merge Commit 树与 PR 合并前 HEAD `e6b571d16192fb4462b7c118ef977df8f6ce186a` 一致。
- Python 3.13：`py -3.13 -m pytest codebase/backend/tests/test_health.py -q` 为 `4 passed, 1 warning`。
- 静态检查：`py -3.13 -m compileall -q codebase/backend/app codebase/backend/tests` 通过。
- Compose：`docker compose --env-file codebase/infra/.env.example -f codebase/infra/docker-compose.yml config --quiet` 通过。
- 治理检查：11 个 TASK 存在；`workflow/state.json` 解析通过；`git diff --check` 通过。
- 范围：相对 Merge Commit 第一父提交无 `codebase/` 修改；未启动容器或数据库，因为 PR #18 仅包含任务书和治理文档。
- 结论：CR-037 合并后验证通过；TASK-002 仍为 `Changes requested`，仅允许恢复 CR-036 R6/R7，依赖任务继续阻塞。

## TASK-002 / CR-036 R6-R7 修复验证（2026-07-16）

- Python：本机与 API 容器均为 `Python 3.13.14`。
- R6 契约与迁移提交：`35119954ba1d9ca475f03d1faa026bf6a474b18f`。
- R7 PostgreSQL 与审查修复提交：`11dbb226e9b77ff5185fed5fa1434b0de6749206`。
- 完整后端：`python -m pytest tests -q`，结果 `125 passed, 5 skipped, 1 warning`；5 个跳过项是带专用数据库与显式破坏性开关的 PostgreSQL 集成测试。
- 聚焦回归：审计、失败响应、设备、组织、迁移共 `58 passed, 1 warning`；测试职责搬迁后 identity 相关两文件共 `32 passed, 1 warning`。
- 编译：`python -m compileall -q app alembic`，退出码 0。
- 规模检查：`test_identity_permissions.py` 461 行；新增 `test_task002_identity_regressions.py` 262 行；审计、组织和 PostgreSQL 集成测试均不超过 500 行；迁移测试函数均不超过 60 行。
- Compose 配置：`docker compose ... config --quiet`，退出码 0。
- 连续迁移：真实 PostgreSQL 17 执行 `0002 -> 0001 -> 0002` 成功；`alembic current` 为 `0002 (head)`。
- 真实 PostgreSQL：专用数据库 `equipment_task2_validation`，同时要求 `TASK002_ALLOW_DESTRUCTIVE_TESTS=1`；集成测试连续两轮均为 `5 passed`，最终修复镜像复验为 `5 passed, 1 warning`。
- 并发覆盖：失败写事务回滚与恰好一条失败审计、同 Key 同请求回放、同 Key 不同请求拒绝、最后一个系统管理员保护、同级组织名称唯一。
- 容器：PostgreSQL 与 Redis 为 `healthy`，API 正常启动；容器内 `/healthz` 返回 `{'status': 'ok', 'service': 'equipment-operations-platform'}`。
- 静态差异：`git diff --check` 通过。
- 唯一警告：FastAPI/Starlette TestClient 对 `httpx` 兼容层的第三方弃用提示；未新增生产依赖。
- 未验证：尚未取得 DEV-002 对新候选的正式批准，尚未创建后继正式 PR，尚未合入 `codex/stage-05-integration`。

## TASK-002 集成基线同步后复验（2026-07-16）

- 同步验证候选：`4c111d0243d947a32d555bd48b1b72cab552bac4`。
- 同步基线：`origin/codex/stage-05-integration` 精确 SHA `ac767c83128cb89ceea8e28c518be0adfbe1984c`。
- 同步 Merge Commit：`0aac415d18aee256c237adb508d2ab24314a7486`；当前集成基线是任务分支祖先，`git merge-tree --write-tree` 无冲突。
- 完整后端：同步解决后和 Merge Commit 后均执行 `python -m pytest tests -q`，结果 `125 passed, 5 skipped, 1 warning`。
- 编译与静态检查：`python -m compileall -q app alembic`、`git diff --check`、`workflow/state.json` 解析均通过。
- Compose：`up -d --build` 客户端命令在 180 秒边界返回超时码 124，但输出已完成镜像构建、API 重建和启动；后续独立检查确认 PostgreSQL/Redis healthy、API 正常启动，故不把原超时命令记为直接成功。
- 健康检查：容器内 Python `3.13.14`；`/healthz` 返回 `{'status': 'ok', 'service': 'equipment-operations-platform'}`。
- 迁移：真实 PostgreSQL 17 再次完成 `0002 -> 0001 -> 0002`，最终 `0002 (head)`。
- PostgreSQL 集成：基于同步后 API 镜像重新构建测试镜像，结果 `5 passed, 1 warning`。
- 未验证：DEV-002 尚未复审同步后的新精确 HEAD；后继正式 PR 尚未创建或集成。

## TASK-002 / CR-036 R8 最终审核阻断修复验证（2026-07-17）

- 审核输入：DEV-002 对分支 HEAD `60c71dd5ab7588006ee16d794b03bef493fb3c72` 提交 Changes requested；4 个 Important 为固定目录迁移、`user_management.view_all`、脱敏绕过和未预期异常失败审计，另有 2 个历史 Minor。
- RED：新增迁移目录、用户范围、脱敏和异常审计测试首次执行为 `9 failed`，确认全部阻断可复现。
- 第一轮：修复后模块回归发现旧契约/测试夹具与固定角色规则不一致并修正；最终 `131 passed, 1 warning`。
- 第二轮：完整后端 `python -m pytest tests -q` 为 `136 passed, 5 skipped, 1 warning`；`python -m compileall -q app alembic`、`git diff --check`、`workflow/state.json` 解析通过。
- 第三轮：专用数据库 `equipment_task2_validation_r8` 且显式 `TASK002_ALLOW_DESTRUCTIVE_TESTS=1`，PostgreSQL 17 集成 `5 passed, 1 warning`；迁移往返最终 `0002 (head)`。
- 固定目录：真实 PostgreSQL 查询为 roles=4、permissions=33、system_admin_grants=33、non_fixed_roles=0；自定义旧角色/目录外权限迁移均拒绝，非固定角色不参与运行时授权。
- 用户范围：无 `user_management.view_all` 仅返回本人且不可查看他人；持有该权限可查看全量和他人详情。
- 审计安全：数据库提交、成功审计和未知运行时异常统一返回稳定错误；主事务回滚后独立失败审计恰好一条并返回真实 `audit_event_id`；独立审计失败才返回无伪造 ID 的 `AUDIT_PERSIST_FAILED`。
- 脱敏：`password_confirmation`、`password2`、`cookies` 和 `attachment_payload.content` 均递归脱敏，同时不误伤 `token_count`、`token_usage` 等业务统计字段。
- Compose/HTTP：配置和 `up -d --build` 通过；PostgreSQL/Redis healthy、API Up；`/healthz` 为 HTTP 200，正文 `{"service":"equipment-operations-platform","status":"ok"}`。
- 依赖与边界：未新增生产依赖、兼容分支、通用抽象或 TASK-003/TASK-004 代码；临时测试容器安装的 pytest/httpx 未写入生产镜像，执行后已删除。

## TASK-002 / CR-036 R9 审计脱敏复测（2026-07-17）

- RED：新增 `newPasswordConfirmation`、`current_password_confirmation`、`attachment_payload.raw_content` 与嵌套/list 断言，首次为 `2 failed, 17 passed`；失败审计表实际包含秘密，确认问题可复现。
- GREEN：密码键按归一化独立语义段识别；附件上下文仅保留文件名、类型、尺寸、校验和等白名单元数据，未知正文/二进制键默认脱敏。
- 回归：`python -m pytest tests/modules/test_task002_audit_safety.py tests/modules/test_task002_audit.py -q` 为 `19 passed, 1 warning`；`python -m pytest tests -q` 为 `138 passed, 5 skipped, 1 warning`；`python -m compileall -q app alembic` 与 `git diff --check` 通过。
- 持久化断言：受保护写校验失败后读取 `AuditEvent.metadata_json`，四个秘密原文均不存在。
- PostgreSQL：定位到 `internal: true` 网络内在线安装必然不可依赖、生产镜像无 dev 依赖；新增 Docker `test` 目标后，构建阶段安装 `--group dev`，内部网络专用 PostgreSQL 17 集成 `5 passed, 1 warning`。默认生产镜像确认不含 pytest/httpx；Compose PostgreSQL/Redis healthy、API Up，容器内标准库 HTTP 请求 `/healthz` 为 `200`。
- 唯一警告：既有 FastAPI/Starlette TestClient 对 `httpx` 的第三方弃用提示。
- 未验证：DEV-002 尚未批准；后继正式 PR 尚未由 DEV-002 创建；TASK-002 尚未合入 `codex/stage-05-integration`，依赖继续锁定。

## TASK-004 PR #27 R2 审核修正验证（2026-07-20）

- 审核输入：DEV-002 对精确 HEAD `6c6fda004f806f8b72eddaad64aac419b78a7a6f` 给出 `Changes requested`，Critical 0、Important 4、Minor 2。
- TDD：`verify-review-remediation.ps1` 先分别因缺少 Compose/运行镜像绑定、Web 有限超时、当前执行窗口日志扫描、显式 `EnvFile` 和失败探针保留而 RED，再以最小修改转 GREEN。完整矩阵发现历史日志导致 22 次假阳性，新增“日志窗口绑定本次开始时间”RED 后修正并复跑通过。
- 镜像链：展开 Compose 镜像标签、获批 RepoDigest、本地固定标签镜像 ID 与运行容器不可变镜像 ID 四者绑定；错误 `RAGFLOW_IMAGE` 覆盖和错误摘要均被拒绝，且运行容器 ID/本地标签未被修改。
- 健康与日志：Web/API 请求均有有限超时；真实结果为 5 服务 healthy、Web/API HTTP 200、RAGFlow v0.25.6、Elasticsearch 8.11.3。完成前最终复测时间 `2026-07-20T05:07:01.3918899Z`—`2026-07-20T05:07:39.5000371Z`；日志 133 行，依赖连接失败 0、秘密值命中 0；Docker info/config/up/ps/logs 退出码均为 0。
- 持久化：正常 restart 后 MySQL/Redis/MinIO-S3/Elasticsearch 四项探针一致、容器重建数 0；注入 Redis 不一致时脚本按预期失败且四项探针全部保留，测试后仅清理本次 TASK-004 命名空间。
- 其他：Python 3.13 健康回归 `5 passed, 1 warning`；compileall、平台/RAGFlow Compose config、两个静态契约、网络隔离均通过。运行手册所有命令显式使用忽略的本地 `EnvFile`；本地 `.env.local` 未纳入 Git。
- 边界：未修改业务 API、数据库迁移、TASK-005、生产依赖、兼容代码或通用抽象层；未执行 TASK-005 文档生命周期或 TASK-011 灾备演练。PR #27 新 HEAD 尚待 DEV-002 精确审核，TASK-005 继续锁定。

## TASK-004 PR #27 R3 审核修正验证（2026-07-20）

- 审核输入：DEV-002 对精确 HEAD `601d54d2427302999c7bc10ac5beec3ac0565501` 给出 `Changes requested`，Critical 0、Important 2、Minor 0。
- 根因：Runbook 给不消费 Compose 环境的 `verify-isolation.ps1` 传入未声明的 `-EnvFile`，旧静态检查只搜索参数文本而未核对脚本签名；持久化脚本在清理前输出 PASS，且清理命令绕过 `Invoke-Compose` 的退出码门禁。
- TDD：增强 `verify-review-remediation.ps1` 后先得到 `persistence PASS is emitted before cleanup completes`，修复清理顺序后继续得到 `runbook passes unsupported EnvFile to isolation verifier`，再删除无效参数并转为 `TASK-004 review remediation contract: PASS`。
- 修正提交：`dc909fff1c8260f2f8a50670192761572cdfb76b`。健康和持久化脚本继续显式使用同一 `.env.local`；隔离脚本只检查已运行容器/网络。MySQL DROP、Redis DEL、MinIO object/bucket 删除、Elasticsearch DELETE 及临时资源清理全部经过退出码检查，所有清理完成后才输出 PASS。
- 真实验证：Docker Client/Server `29.6.1`、Compose `v5.1.4`；5 容器 healthy；Web/API HTTP 200；RAGFlow `v0.25.6`；Elasticsearch `8.11.3`；依赖错误 0、秘密值命中 0；网络隔离通过；四存储 restart 后探针一致、容器重建数 0、严格清理探针数 4。
- 静态验证：三个 PowerShell 文件语法解析通过；Compose 契约和审核修正契约均 PASS；RAGFlow Compose `config --quiet`、`git diff --check` 通过。
- 边界：只修改 TASK-004 运行手册、持久化验证脚本、审核回归与正式证据；未修改业务 API、数据库迁移、TASK-005、生产依赖、兼容代码、通用抽象或无关文件。TASK-005 继续锁定，等待 DEV-002 对新精确 HEAD 复审。

## TASK-004 PR #27 R4 审核修正验证（2026-07-20）

- 审核输入：DEV-002 对精确 HEAD `6cd29f158b2c03f61c5b21a7e9bf99d30ec17a34` 给出 `Changes requested`，Critical 0、Important 2、Minor 0。
- 根因：设计和计划中的真实运行命令未与 Runbook 的 `.env.local` 约束同步；清理门禁只有源码结构检查，没有从外部命令非零退出到脚本非零退出且无 PASS 的可执行证据。
- RED/GREEN：环境契约增强后先报 `TASK-004_RAGFLOW_INFRA_DESIGN.md does not define the local runtime environment file`；清理行为测试先报 `missing injectable cleanup helper`。修正后两个脚本分别输出 `TASK-004 review remediation contract: PASS` 和 `TASK-004 cleanup failure behavior: PASS; categories=4`。一次临时动态脚本被 AMSI 拦截的环境事件未作为 RED 证据。
- 修正提交：`29180e285767cbffb9d694cd1834f04514d2cc18`。设计和计划明确真实运行只使用忽略的 `codebase/infra/.env.local` 并显式传 `-EnvFile`，只有不启动容器的静态 `config --quiet` 可使用 `.env.example`。
- 失败行为：新增最小 Compose 外部副作用边界；测试以静态假命令返回 42，并分别覆盖 MySQL、Redis、MinIO、Elasticsearch 清理参数。四个子进程均为非零且没有 PASS；生产持久化验证仍在全部清理成功后才输出 PASS。
- 真实验证：Docker Client/Server `29.6.1`、Compose `v5.1.4`；5 容器 healthy；Web/API HTTP 200；RAGFlow `v0.25.6`；Elasticsearch `8.11.3`；依赖错误 0、秘密值命中 0；网络隔离通过；四存储 restart 后探针一致、容器重建数 0、清理探针数 4。
- 其他验证：Python 3.13 健康回归 `5 passed, 1 warning`；compileall、Compose 契约、RAGFlow Compose config、全部 PowerShell 语法和 `git diff --check` 通过。
- 边界：未新增生产依赖或兼容代码；新增一个仅用于外部 Compose 退出码检查的最小模块，没有业务 API、迁移、TASK-005 或无关修改。TASK-005 继续锁定，等待 DEV-002 对推送后的新精确 HEAD 复审。

## TASK-004 独立 RAGFlow 基础设施验证（2026-07-20）

- 分支/基线：`codex/task-004-ragflow-infra`，基于 `origin/codex/stage-05-integration@b29c69d13c3d1c81f01023152eabf0c0f2d02741`；证据提交前功能候选为 `ac8c007730d8e947c5687380e4583e8b23d2cce1`。
- TDD RED：静态契约首次因缺少 `codebase/infra/ragflow/docker-compose.yml` 失败；健康、隔离和持久化脚本分别先以“not implemented”失败，再实现 GREEN。
- 环境：Python `3.13.14`；Docker Client/Server `29.6.1`；Docker Compose `v5.1.4`；Docker Desktop Linux 的 `vm.max_map_count=262144`。
- Python 回归：`py -3.13 -m pytest codebase/backend/tests/test_health.py -q` 为 `5 passed, 1 warning`；警告为既有 Starlette/httpx 弃用提示。
- Compose：平台 Compose 与 RAGFlow Compose 的 `config --quiet` 均通过；静态契约脚本输出 `TASK-004 compose contract: PASS`。
- 真实健康：5 个容器全部 healthy；RAGFlow Web 为 HTTP 200；Elasticsearch 为 `8.11.3`；本机已有无关 RAGFlow 占用默认端口，验证仅通过环境覆盖使用 `127.0.0.1:18080/19380`，未停止无关容器。
- 固定镜像摘要：RAGFlow `sha256:74595f13bb09c51b1c151ce85d9e06e42cf4371b0c8aeaef222e67253d7c7543`；Elasticsearch `sha256:58a3a280935d830215802322e9a0373faaacdfd646477aa7e718939c2f29292a`；MySQL `sha256:ccb8f749bb5e59f9f8f03bf7282c7ef27a93a1814a24f0a8a926fb4e19b7fb97`；MinIO `sha256:a72bf37c235a83a73890d2a46c5b36801fed61c335175e0396070bf84a8bbb98`；Redis `sha256:02419de7eddf55aa5bcf49efb74e88fa8d931b4d77c07eff8a6b2144472b6952`。
- 网络隔离：内部网络 5 个成员，访问网络仅 RAGFlow；MySQL、Redis、MinIO、Elasticsearch 宿主端口为 0；RAGFlow 两个端口均只绑定 `127.0.0.1`。
- 重启恢复：MySQL、Redis、MinIO、Elasticsearch 写入同一随机探针，整栈 restart 后均读回；5 个容器 ID 未变化；探针已清理，未删除命名卷。
- 环境事件：Docker 引擎经内部代理访问 Docker Hub 持续 EOF，宿主机 Registry 探测正常；使用项目既有 DaoCloud 透明镜像拉取同一固定版本并核对 ID/RepoDigest，未修改 Docker Desktop 全局代理或仓库运行镜像身份。
- 静态与边界：`git diff --check origin/codex/stage-05-integration...HEAD` 通过；没有业务代码、迁移、TASK-005 实现、生产依赖、兼容代码或通用抽象层修改。
- 未验证：DEV-002 尚未审核当前最终精确 HEAD；PR #27 尚未合入；合并后验证、TASK-005 真实文档上传/解析/检索/引用和 TASK-011 完整备份恢复演练均未执行。

### TASK-004 PR #27 R1 审核修正验证

- 审核基线：DEV-002 对 `8b628fcfbf80fb6490d8d3dd5257feafba9d1595` 给出 `Changes requested`，Critical 0、Important 3、Minor 0；修正功能提交为 `f87a0c309c322f9accedcaea4a80aed84483b0e7`。
- TDD RED/GREEN：新增 `verify-review-remediation.ps1`；依次确认 9380 API 契约缺失、MinIO S3 生命周期缺失、5 个获批摘要缺失时失败，随后逐项实现并转为 `TASK-004 review remediation contract: PASS`。
- API：从 Compose 展开配置定位 target `9380`，以 60 秒有限窗口真实请求 `/api/v1/system/version`；结果为 HTTP 200、`code=0`、`data=v0.25.6`、`message=success`，任一契约漂移或超时均失败。
- MinIO：创建随机 bucket/object，经 `mc` 使用 S3 API 写入；整栈 restart 后经 S3 API 回读一致，再删除对象、bucket、client alias 和临时文件；输出 `stores=mysql,redis,minio-s3,elasticsearch; containers_recreated=0`。
- 镜像：`verify.ps1` 对 5 个固定标签逐一匹配获批 SHA-256；内存替换 Redis 期望值为全零摘要的负向测试得到 `Image digest mismatch`，证明漂移会返回非零，未改写本地镜像标签。
- 完整矩阵：Python 3.13 健康回归 `5 passed, 1 warning`；平台/RAGFlow Compose config、Compose 静态契约、审核修正契约、真实健康/API、网络隔离和重启持久化全部通过；`git diff --check` 通过。
- 完成前复查：首次在持久化重启后立即执行摘要突变测试时，容器虽 healthy 但 API 连接短暂关闭，暴露一次性 API 请求的时序缺陷；新增 RED 契约后以 `ba7e13f2b585f872ca811e98b50c09e25020fba5` 实现有限重试，再按“持久化重启 → API/摘要负向验证”顺序复现通过。
- 边界：仅修改 TASK-004 验证脚本、审核回归脚本、既有实施计划/运行手册和正式台账；未修改业务 API、迁移、TASK-005、生产依赖、兼容代码或通用抽象层。PR #27 尚未获 DEV-002 对新精确 HEAD 的批准，TASK-005 继续锁定。

## TASK-002 / CR-036 R11 语义敏感键脱敏复测（2026-07-17）

- RED：`binaryAttachment`、`uploadedFile`、`sessionCookieValue`、`passwordvalue` 在直接函数和失败审计落库用例中均为 `2 failed`，确认 R10 的前缀/后缀枚举遗漏。
- GREEN：归一化后仅按完整语义段识别附件（`attachment/file/upload/document/image`）与敏感键；密码、Cookie、Secret、Authorization 使用有限紧凑前后缀，Token 仅按完整段脱敏并保留 `token_count`、`token_usage`。
- 反例：`code`、`name`、`status`、`profile`、根层普通 `content` 和 Token 统计字段均保持原值；附件上下文内仍仅保留元数据白名单。
- 回归：定向审计 `23 passed, 1 warning`；Python 3.13 全量 `142 passed, 5 skipped, 1 warning`；compileall 与 diff check 通过；失败请求的 `AuditEvent.metadata_json` 不含七类测试秘密。
- 运行验证：独立 test 镜像 PostgreSQL 17 集成 `5 passed, 1 warning`；Compose 重建成功，PostgreSQL/Redis healthy、API Up，`/healthz` HTTP 200。
- 残余风险：本轮关闭已知敏感语义别名漏洞；攻击者将秘密置于无敏感语义的任意未知字段（如 `notes`）尚未默认脱敏，作为后续独立强化项，不在本 CR 实现。
- 未验证：DEV-002 尚未批准；后继正式 PR 尚未由 DEV-002 创建；TASK-002 尚未合入 `codex/stage-05-integration`，依赖继续锁定。

## TASK-002 / CR-036 R10 审计标量脱敏复测（2026-07-17）

- 审核复现：DEV-002 给出的 `newpassword`、`attachment_payload` 标量、`attachments` 标量列表和 `uploadData` 在修复前均会原样进入审计；新增 RED 用例为 `2 failed`。
- 根因：附件上下文只在字典分支用于键白名单，标量与列表递归虽传入 context 却未消费；密码规则只识别有分隔符的语义段。
- GREEN：附件上下文中的非字典标量默认脱敏；纯标量列表整体脱敏，混合列表递归处理；仅字典白名单元数据标量可保留。无分隔的 `newpassword`、`userpassword` 按紧凑敏感后缀脱敏。
- 回归：定向审计 `21 passed, 1 warning`；Python 3.13 全量 `140 passed, 5 skipped, 1 warning`；`python -m compileall -q app` 和 `git diff --check` 通过。两层测试同时检查 `sanitize_audit_metadata()` 返回值和失败请求的 `AuditEvent.metadata_json`，均无明文。
- 运行验证：当前代码重新构建独立 `test` 镜像后，内部网络 PostgreSQL 17 集成 `5 passed, 1 warning`；Compose 重建成功，PostgreSQL/Redis healthy、API Up，容器内 `/healthz` 为 HTTP 200、正文 `{"status":"ok","service":"equipment-operations-platform"}`。
- 未验证：DEV-002 尚未批准；后继正式 PR 尚未由 DEV-002 创建；TASK-002 尚未合入 `codex/stage-05-integration`，依赖继续锁定。

## TASK-004 PR #27 R5 Markdown 运行命令契约修正（2026-07-22）

- 审核输入：DEV-002 对精确 HEAD `a5ac8490bf678ea03efc702052f7f1edecff182b` 给出 `Changes requested`，Critical 0、Important 1、Minor 0；任务书 `- 验证：...` 内的反引号运行命令未进入 `$runtimeLines`，因此静态断言无法防止其回退到 `.env.example`。
- RED：保留 `.env.local` 定义，仅将临时任务书列表中的 `--env-file $RagflowEnvFile` 变异为 `.env.example`，旧检查器错误输出 PASS。修正后同一变异稳定返回非零并报告运行命令违规。
- GREEN：功能提交 `314b46d3efdc7af0d13c671fadd41be7bb3900d1` 按 Markdown 代码块和任务书验证列表提取真实命令；静态 `config --quiet` 不进入运行检查。独立复审发现禁用示例误报后，补充 RED 并排除明确标记为禁止、错误、反例或不得执行的代码块。
- 验证：Windows PowerShell 语法解析通过；`verify-review-remediation.ps1`、`verify-cleanup-failure.ps1`、`verify-compose-contract.ps1` 均 PASS；任务书回退变异非零；禁用错误示例通过；`git diff --check` 通过。独立复审为 Critical 0、Important 0、Minor 0。
- 未验证：本轮未改 Compose、镜像、运行脚本或业务代码，因此未重新执行 Docker 五服务重启验证；当前环境中的历史 Python 3.13 虚拟环境入口无法创建进程，本轮未生成新的 Python 结果，沿用记录仅作为上一 HEAD 历史证据，不宣称本轮重新通过。
- 边界：只修改 TASK-004 审核契约测试；无生产依赖、兼容代码、抽象层、业务 API、迁移、TASK-005 或无关修改。DEV-002 批准新精确 HEAD 前 TASK-005 继续锁定。
## TASK-004 PR #27 R6 运行环境默认值修复验证（2026-07-22）

- 审核输入：DEV-002 对精确 HEAD `80b40182efa49033ee561f34fd6e078b3469a733` 给出 `Changes requested`；Critical 0、Important 1、Minor 0。
- RED：增强 `verify-review-remediation.ps1` 后，首先稳定失败于 `verify.ps1 does not default EnvFile to codebase/infra/.env.local`。
- GREEN：`verify.ps1` 与 `verify-persistence.ps1` 默认改为 Git 忽略的 `codebase/infra/.env.local`，并在任何 Docker 调用前检查文件存在；缺失时两个子进程均非零退出并包含 `Missing local RAGFlow environment file`。
- 功能提交：`78e3132d907870f17980ade7142f7c9a7ae7562e`。
- 静态与失败行为：审核契约 PASS；四类清理失败行为 PASS；Compose 契约 PASS；RAGFlow Compose `config --quiet` PASS；8 个 PowerShell 文件语法通过。
- 真实运行：5 个容器 healthy；Web/API HTTP 200；RAGFlow `v0.25.6`；Elasticsearch `8.11.3`；镜像摘要与运行镜像一致；日志依赖失败 0、秘密命中 0；网络隔离 PASS。
- 持久化：MySQL、Redis、MinIO S3、Elasticsearch 重启后探针一致，容器重建数 0，严格清理探针数 4。
- 其他：Python 3.13.14 健康回归 `5 passed, 1 warning`；compileall、`git diff --check` 通过。唯一警告为既有 Starlette/httpx 第三方弃用提示。
- 边界：未增加生产依赖、兼容代码、抽象层、业务 API、迁移、TASK-005 或无关修改；DEV-002 尚未审核新 HEAD，TASK-005 继续锁定。

## TASK-003 最新集成基线本地复验（2026-07-22）

- 同步：本地候选以 Merge Commit `4877dcdc301b97d884a43883a5584fdee1d28c41` 吸收 `codex/stage-05-integration` 的 `f135997a6ecc009de75735b673499b475615a717`，无文件、迁移、API 或治理冲突。
- Python：Python 3.13.14 执行 `pytest codebase/backend/tests/modules -q` 为 `168 passed, 1 warning`；唯一警告为既有 Starlette/httpx 第三方弃用提示。
- PostgreSQL：一次性 PostgreSQL 17 专用空库执行 `test_task003_postgres.py` 为 `4 passed, 1 warning`，覆盖 `0002 -> 0003 -> 0002 -> head`、失败回滚、同 Key 并发重放、并发开始维修、故障创建/设备停用竞争；容器已移除。
- 静态门禁：`compileall`、Alembic 单一 `0003_task003 (head)`、平台 Compose、RAGFlow Compose 和 `git diff --check` 通过。
- 业务边界：四个 API、状态迁移、人工最终字段、设备停用保护和结构化案例查询已覆盖；查询无外部网络访问，诊断草稿只复制批准且类型正确的字段。
- 未验证/门禁：尚未推送当前本地候选、尚未创建或更新 Draft PR、DEV-002 尚未审核；TASK-003 未正式集成，不解锁下游任务，不构成 Stage 6 证据。

## TASK-003 PR #32 合并后复验（2026-07-22）

- 集成对象：获批源 HEAD `8960b5d8ab1e7073036c6151744233e26c15c9e9`；Merge Commit `51337db767eb94051f78a5c537a3ff48d428a742`；双亲顺序与任务书要求一致。
- Python：Python 3.13.14 全量后端 `173 passed, 9 skipped, 1 warning`；唯一警告为既有 Starlette/httpx 第三方弃用提示。
- PostgreSQL：一次性 PostgreSQL 17 专用库执行 TASK-003 迁移、失败事务、同 Key 幂等与并发场景为 `4 passed, 1 warning`；临时容器及数据已清理。
- 静态门禁：`compileall`、Alembic 单一 `0003_task003 (head)`、平台 Compose、RAGFlow Compose 和 Merge diff check 通过。
- 范围检查：无新增生产依赖、兼容代码、通用抽象、前端、RAGFlow/Agent/向量调用或其他任务实现；工作树在治理修改前保持干净。
- 结论：技术合并后复验通过；本纯治理 PR 合入后 TASK-003 才完成连续台账闭环。Stage 6 不因此自动获准。

## TASK-004 PR #27 合并后复验（2026-07-22）

- 集成对象：源 HEAD `76732606412d71239d302e4e9e5a0da6b364fd70`；Merge Commit `87e8e3c0aab62ee9105bf3807b23fcf44ac15137`；最新集成基线 `960c64ffc64c20edfb5bd73a2721678c9b9972c8` 包含该 Merge Commit。
- Review/Merge：DEV-002 Approved 同一源 HEAD，并作为非任务作者使用 Merge Commit 合并；项目负责人授权绑定 PR #27 和同一精确 HEAD。
- 合并后静态回归：`verify-review-remediation.ps1`、`verify-cleanup-failure.ps1`、`verify-compose-contract.ps1` 均 PASS；RAGFlow Compose `config --quiet` PASS。
- Python：Python 3.13.14 健康回归 `5 passed, 1 warning`；唯一警告为既有 Starlette/httpx 第三方弃用提示。
- 真实运行：5 个容器 healthy；Web/API HTTP 200；RAGFlow `v0.25.6`；Elasticsearch `8.11.3`；五个固定镜像摘要与运行镜像一致；日志依赖失败 0、秘密命中 0。
- 隔离/持久化：内部网络成员 5、访问网络成员 1、内部依赖宿主端口 0、RAGFlow 回环端口 2；MySQL、Redis、MinIO S3、Elasticsearch 重启后探针一致，容器重建 0，探针清理 4。
- 边界：治理收尾只更新任务书和连续台账；无 `codebase/`、测试代码、数据库、部署配置、依赖、兼容层、抽象层或无关修改。
- 结论：本治理 PR 合并后 TASK-004 正式闭环并解除 TASK-005 的 TASK-004 依赖；Stage 6 仍禁止进入。

## TASK-006-FE 正式前端工程基础自测（2026-07-22）

- 功能提交：`800e7a43fcc6ae98f00e74d738924c236c84b118`，基于 `codex/stage-05-integration@f135997a6ecc009de75735b673499b475615a717`。
- 范围：在唯一的 `codebase/frontend/` 建立 React、Vite 与 TypeScript 工程；提供构建/测试脚本、共享应用壳、非业务路由页面骨架和最小 `fetch` JSON 边界。
- 已确认依赖：运行时仅 `react`、`react-dom`、`react-router-dom`；开发时仅 TypeScript、Vite、React 插件、Vitest、jsdom 与 React Testing Library。未引入 UI 框架、全局状态、HTTP 客户端或 CSS 框架。
- TDD：实现前，应用壳和 JSON 边界测试因模块不存在而不能执行；首次依赖安装产生不完整的 `pathe` 包，按干净安装重试后可执行。随后应用壳测试暴露重复页面标题，修正后转绿；构建再发现 Vite 配置未使用 Vitest 类型入口，修正后通过。
- 验证：`npm --prefix codebase/frontend test` 为 `2 passed`；`npm --prefix codebase/frontend run build` 通过；`06-testing/tests/*.test.js` 全部通过；`git diff --check` 通过；对 `codebase/frontend` 的原型运行时引用扫描无匹配。
- 边界：未复制、移动或运行时引用 `03-ui-prototype/`；只新写共享视觉语言，不实现智能配置字段/保存、Agent 对话、SSE、引用、故障或维修流程、认证规则或业务 API。
- 未验证：未执行浏览器人工视觉回归；未执行 Docker/Compose 或后端测试，原因是本任务未修改对应范围且 DEV-002 不具备容器验证职责。
- 兼容/抽象/无关修改：无兼容代码；仅实现任务书要求的外部副作用边界 `requestJson`；无无关修改。

## TASK-006-FE Ready 审核证据修正（2026-07-22）

- 审核输入：DEV-001 对 PR #33 精确 HEAD `59fb79ef2e1cba76705e1269434e18cfec92d595` 给出 `Changes requested`，Critical 0、Important 2、Minor 0。
- 修正范围：同步 Ready 审核证据、PR 当前完整 HEAD 绑定说明、Node/npm 运行基线和 `npm ci` 验证证据；未修改业务页面、Agent 配置、SSE、维修流程、认证或业务 API。
- 运行基线：`package.json` 声明 Node `^20.19.0 || >=22.12.0`、npm `>=10.0.0`；本轮验证环境为 Node `v26.5.0`、npm `11.17.0`。
- 验证计划：重新执行 `npm ci`、前端测试、生产构建、原型静态回归和 `git diff --check`；推送后以新完整 HEAD 重新请求 DEV-001 审核。
## TASK-005 安全知识上传 API 自测（2026-07-22）

- 功能提交：`f9fc4a0ed2a04249640d569de08c41f17aa4b684`；基线为 `codex/stage-05-integration@8c0087928f693674f498044b0e2dbbe96196847c`，同一 Draft PR #37。
- TDD RED：MinIO 边界因 `app.integrations.object_storage` 不存在而收集失败；知识 API 因 `create_app` 不接受存储/扫描依赖而 4 项失败；ClamAV 边界因模块不存在而收集失败。逐项实现后转绿。
- 依赖：项目负责人已明确批准 `minio>=7.2.20,<8.0` 与 `python-multipart>=0.0.32,<1.0`；当前 Python 3.13.14 环境安装 `minio 7.2.20`、`python-multipart 0.0.32`，`pip check` 为 `No broken requirements found`。
- 安全边界：上传最大 100MB且非空；ClamAV 未配置、不可达或响应异常均失败关闭；不安全文件不写 MinIO；对象键随机且限制在 `knowledge/`；审计和响应不含文件正文、Token 或扫描器原始错误。
- API：`POST /api/knowledge/documents` 使用 `intelligence:knowledge`、`Idempotency-Key`、multipart 和内容 SHA-256 幂等摘要；`GET /api/knowledge/documents/{id}` 向授权操作者返回生命周期及失败原因。
- 验证：知识/RAGFlow/MinIO/ClamAV 定向 `28 passed, 1 warning`；Python 3.13 全量 `200 passed, 9 skipped, 1 warning`；`compileall`、`git diff --check` 通过。唯一警告是既有 Starlette/httpx 第三方弃用提示。
- 未验证：无共享 Alembic 迁移；未连接真实平台 MinIO、ClamAV 或 RAGFlow，未执行真实文档扫描、上传、解析、切片、混合检索和重启恢复。这些仍须 DEV-001 在 Docker 环境完成。
- 兼容/抽象/无关修改：无兼容代码；新增抽象仅限 MinIO、ClamAV 和 RAGFlow 外部副作用边界；无范围外修改。
## TASK-005 Worker 同步自测（2026-07-22）

- 功能提交：`5e134655bc087f972e84f8f40b31bac284ee6c29`；继续维护 Draft PR #37。
- TDD RED：Worker 模块不存在导致测试收集失败；实现批量上传/解析、状态刷新和安全失败后转绿。
- 行为：只处理 `UPLOADING/PARSING`；上传前要求关联文件扫描状态为 `CLEAN`；对象存储错误不泄露原始异常；RAGFlow 失败不产生伪 READY 状态；批量上限为 500。
- 验证：Worker 定向 `3 passed, 1 warning`；Python 3.13 全量 `204 passed, 9 skipped, 1 warning`；compileall、git diff check 通过。唯一警告为既有 Starlette/httpx 第三方弃用提示。
- 未验证：未接真实队列调度、MinIO、ClamAV、RAGFlow 或 PostgreSQL 迁移；这些需 DEV-001 真实环境验证和共享迁移集成。

## TASK-006 全范围候选自测（2026-07-22）

- 同步：候选先合并 `codex/stage-05-integration@8c0087928f693674f498044b0e2dbbe96196847c`；解决 `app/main.py` 路由注册与连续台账冲突，未修改已集成任务的业务语义。
- 前端：智能配置页固定展示 AI 故障上报、智能问数、操作指引、故障诊断四个 Agent；只在首次选中某个尚未初始化的 Agent 时调用其单项读取端点，保存仅向当前 `agent_id` 发出 PUT，并携带 `Idempotency-Key`。无模型或不支持推理的模型开启深度思考时给出明确提示且不提交。
- 迁移：同步后发现旧 TASK-006 `0003` 与已集成 TASK-003 `0003_task003` 形成双头；将 TASK-006 修订为 `0004_task006`，前置 `0003_task003`。专项 RED 显示 `head` 多头导致迁移失败；修正后 `alembic heads` 仅输出 `0004_task006 (head)`，TASK-006 回退至 `0003_task003` 时不删除 TASK-003 表。
- 验证：Node/npm 锁定依赖安装后，`npm test` 为 `7 passed`，`npm run build` 通过；Python 3.13.14 的 TASK-003/006 迁移回归为 `7 passed, 1 warning`，全量后端为 `221 passed, 9 skipped, 1 warning`，`compileall` 与 `git diff --check` 通过。唯一警告为既有 Starlette/httpx 第三方弃用提示。
- 边界：未新增生产依赖、兼容层或通用抽象；未实现 Agent Runtime、对话、SSE、引用、版本/发布/回滚或生产操作。临时 Python/Node 验证环境位于 `/private/tmp`，不纳入提交。
- 门禁：本候选尚未由 DEV-001 针对新精确 HEAD 复审；在审核、集成检查、项目负责人逐 PR/HEAD 授权、DEV-001 Merge Commit 及合并后验证完成前，不解锁 TASK-007/008/009/010，也不进入 Stage 6。

## TASK-006 PR #14 合并后治理复核（2026-07-22）

- 集成对象：源 HEAD `e564b15f42492087578d03c3a1f5412c9db35f6b`；Merge Commit `da460c64f48e1b1522979d2e5f381fb797571934`，双亲为 `8c0087928f693674f498044b0e2dbbe96196847c` 与源 HEAD。
- 执行者/授权：PR 作者 DEV-002；DEV-001 `ll979053897-arch` 执行手动 Merge Commit；项目负责人授权绑定 PR #14 与同一精确 HEAD。
- 合并后验证：前端 7 tests/build、后端 `221 passed / 9 skipped / 1 warning`、PostgreSQL 迁移往返、祖先关系和 merge-tree 通过；无 HEAD、目标分支或批准记录漂移。
- 结论：TASK-006 正式闭环，TASK-007 仅按自身任务书门禁继续；未批准 Stage 6，也未自动解锁其他非直接依赖任务。

## TASK-007 开发候选自测（2026-07-22）

- 候选：`codex/task-007-agent-runtime@7c3cf64fe7537ca8f7e05c66e4d5a71ff3383e61`，目标 `codex/stage-05-integration`。
- 实现：线程归属与管理员读取、运行配置快照、持久化 checkpoint、SSE 状态事件、恢复确认、敏感文本不回显、provider-neutral 推理参数映射及 `0005_task007` 迁移。
- 验证：Python 3.13 全量 `224 passed, 9 skipped, 1 warning`；TASK-007 `2 passed`；迁移检查、`compileall`、`git diff --check` 通过。唯一警告为既有 Starlette/httpx 弃用提示。
- 未验证：未执行 Docker/PostgreSQL 真实 checkpoint 联调，当前环境无 Docker；未连接真实外部 LLM，Runtime 以可审计 provider-neutral gateway 等待模型执行。
- 兼容/依赖/抽象：未新增生产依赖、兼容层或通用抽象；新增 Runtime 模块仅承载本任务边界；无无关修改。
- 门禁：尚未创建/更新 Draft PR，未请求 DEV-001 审核，不申请 Merge 授权，不解锁 TASK-008/009/010，不进入 Stage 6。

## TASK-007 DEV-001 Changes requested 修订（2026-07-23）

- 审核对象：PR #40，原精确 HEAD `24421bc49d45823fa9e2946124940a26de684545`；DEV-001 提出 3 项 P1、1 项 P2，旧批准不适用。
- 已修订：恢复 `Idempotency-Key` 重放/冲突保护；线程/运行成功与 resume 写入脱敏审计；业务上下文、附件引用、运行状态递归脱敏；加入 allowlist ToolCall 审计边界；补充幂等、管理员访问、SSE、checkpoint 状态和嵌套敏感字段测试；增加可选 `TASK007_POSTGRES_DSN` 集成测试。
- 新验证：Python 3.13 全量 `226 passed, 10 skipped, 1 warning`；定向 Runtime `4 passed`；`compileall`、`git diff --check` 通过。唯一警告为既有 Starlette/httpx 弃用提示。
- 未解决阻断：TASK-007 批准范围要求真实 LangGraph checkpoint。当前 `pyproject.toml` 未声明 LangGraph，新增生产依赖按项目规则需要项目负责人确认；本轮未静默添加依赖，PR 仍不得 Ready/合并。

## TASK-007 LangGraph 依赖授权后修订（2026-07-23）

- 项目负责人已确认允许 TASK-007 新增 LangGraph 生产依赖。
- 新增依赖：`langgraph>=0.6,<0.7`、`langgraph-checkpoint-postgres>=2.0,<3.0`。
- 实现：Runtime 使用 LangGraph `StateGraph`；生产 PostgreSQL 使用 `PostgresSaver` 并初始化 checkpoint 表，本地 SQLite 测试使用内存 saver；运行与 resume 均通过同一 `thread_id` 恢复状态。
- 验证：Python 3.13 全量 `226 passed, 10 skipped, 2 warnings`；定向 Runtime `4 passed`；`compileall`、`git diff --check` 通过。警告为既有 Starlette/httpx 弃用及 LangChain serializer pending deprecation。
- 结论：原 LangGraph P1 已修订；真实 PostgreSQL checkpoint 仍需 DEV-001 专用环境执行可选集成测试，完成前不得宣称容器级验证通过。

## TASK-007 DEV-001 第二轮 Changes requested 修订（2026-07-23）

- 审核对象：PR #40，HEAD `71b7d3c1993beb6abd94a22bacd0b9d392347d7d`；DEV-001 提出 resume 幂等、真实 PostgreSQL checkpoint/restart、恢复不得覆盖历史 checkpoint 三项问题。
- 已修订：resume 接受并校验 `Idempotency-Key`，相同请求重放原响应、冲突返回 409；resume 仅传入允许的 confirmation/resume 输入，LangGraph saver 先读取同一 `thread_id` 的历史 state 再合并；可选 PostgreSQL 集成测试增加真实 `run_checkpoint` 首次保存、同 thread resume 和历史事件保留断言。
- 验证：Python 3.13 全量 `227 passed, 10 skipped, 2 warnings`；Runtime/集成定向 `5 passed, 1 skipped`；`compileall`、`git diff --check` 通过。专用 PostgreSQL 未配置，真实集成测试本地跳过。
- 门禁：新 HEAD 尚未由 DEV-001 复审；不得 Ready、请求 Merge 授权、合并或解锁下游。

## TASK-007 DEV-001 第三轮 DSN 修订（2026-07-23）

- 审核对象：PR #40，HEAD `d315d11c67e3886aad7feae9b0699d12e64b1336`；DEV-001 发现测试未走 psycopg v3 构造路径，生产 PostgresSaver 收到错误的 SQLAlchemy 方言 URL。
- 修订：PostgreSQL 集成测试改用 `create_database_engine()`；LangGraph 边界将 `postgresql+psycopg://`/`postgresql+psycopg2://` 转换为 libpq `postgresql://`；新增 URL 规范化回归测试。
- 验证：Python 3.13 全量 `228 passed, 10 skipped, 2 warnings`；Runtime/集成定向 `6 passed, 1 skipped`；`compileall`、`git diff --check` 通过。
- 未验证：当前无专用 PostgreSQL DSN，真实 checkpoint 测试仍跳过；需要 DEV-001 在 PostgreSQL 17 环境执行并记录结果。

## TASK-005 DEV-001 真实 RAGFlow 联调证据（2026-07-23）

- 验证对象：PR #37 原精确 HEAD `9375d12853248ceb39068f509a8dbd95bf717ce5`；由具备 Docker/RAGFlow 环境的 DEV-001 执行。
- 真实生命周期：上传、ClamAV 恶意附件拒绝、RAGFlow 解析、状态进入 `READY`、混合检索和引用回传全部通过，结果 `1 passed`。
- 清理复核：临时数据集、容器、网络和卷均已清理；共享 RAGFlow 五项服务保持 healthy。
- 回归复核：Python 3.13 后端 `217 passed, 11 skipped`；`compileall`、验证脚本契约和 `git diff --check` 通过；三轮复核 Critical 0、Important 0、Minor 0。
- 当前处理：任务分支已同步当前 `codex/stage-05-integration` 并解决 TASK-005 与已集成模块的路由、依赖和连续台账冲突；同步后的新精确 HEAD 必须重新绑定 DEV-001 审核，不能沿用旧 HEAD 结论。
- 同步后回归：Python 3.13.14 全量后端 `259 passed, 10 skipped, 2 warnings`；`pip check`、`compileall` 与暂存 diff check 通过。警告为既有 Starlette/httpx 弃用及 LangChain serializer pending deprecation。
- 门禁：证据提交并推送后，PR #37 才可请求 DEV-001 审核；未批准、未完成集成检查和逐 PR Merge 授权，不解锁 TASK-009/011，不进入 Stage 6。

## TASK-007 合并后技术验证（2026-07-23）

- 集成对象：PR #40，源 HEAD `fcd643ab0b0e33a585e3be6ec0b0036a611059c4`；Merge Commit `bf842626987148575173c6cf3f34970fc496ad7c`；第一父 `fdec916fad943acb8ad62a1cf5bc3ce8f770cc8d`，第二父为源 HEAD。
- DEV-001 实测：合并结果后端 `228 passed, 10 skipped, 2 warnings`；PostgreSQL 17 真实 `PostgresSaver` checkpoint/restart `1 passed, 1 warning`；`compileall`、合并树 `git diff --check`、Compose 配置、API 生产镜像构建通过；PostgreSQL/Redis healthy，容器内 `/healthz` 返回 HTTP 200。
- 治理状态：代码已集成；项目负责人对 PR #40/源 HEAD/合并结果的正式追认及治理收尾 PR 合入前，不宣称 TASK-007 彻底闭环、不解锁下游、不进入 Stage 6。

## TASK-005 PR #37 Changes requested 修订（2026-07-23）

- 审核对象：PR #37 精确 HEAD `1cee0317ab1eefca2ca4900e2e97804ae1448665`；DEV-001 提出 Worker 入口、三张知识表迁移、真实验证资产和过期 PR 描述问题，PR 已恢复 Draft。
- TDD：新增 Worker 入口测试时因 `app.modules.knowledge.worker_main` 不存在而 `2 failed`；实现运行依赖装配、批量参数、事务提交和安全配置校验后，Worker 定向为 `5 passed, 2 warnings`。
- 验证资产：新增默认跳过的 `tests/integration/test_task005_live_stack.py`，仅在显式启用和提供专用 PostgreSQL/MinIO/ClamAV/RAGFlow 参数时执行；新增 `codebase/infra/task-005/scripts/Invoke-Validation.ps1`，不保存凭据、不启动或改写共享服务。
- 本地验证：Python 3.13 全量 `261 passed, 11 skipped, 2 warnings`；TASK-005 新增/Worker 定向 `5 passed, 1 skipped, 2 warnings`；`pip check`、`compileall`、`git diff --check` 通过。跳过项是当前无 DEV-001 专用实栈参数；警告均为既有第三方弃用提示。
- 未解决阻断：当前 Alembic 单链截至 `0005_task007`，知识三表迁移缺失。共享迁移最终决策归 DEV-001，且数据库迁移需项目负责人针对具体范围确认；DEV-002 未擅自新增 revision。完成迁移集成并由 DEV-001 重跑真实联调前，不得 Ready、批准、申请 Merge 授权或解锁下游。
- 边界：无新增生产依赖、兼容代码、通用抽象或无关修改；真实凭据和运行数据未写入仓库。
- 迁移接收：项目负责人批准 `0006_task005` 接续 `0005_task007` 并创建四张表；DEV-001 提交 `2fe848bfb5f7f7849b950cbecfa40644e6782a05` 经三文件边界核验后，由 DEV-002 精确 cherry-pick 为 `78ad1c81f6292c1fc3706b35d9dd495a8244d1b4`。
- 迁移验证：DEV-001 在 PostgreSQL 17 执行 `0005 -> 0006 -> 0005 -> 0006` 为 `1 passed`；DEV-002 本地定向 `6 passed, 2 skipped`，全量 `262 passed, 12 skipped, 2 warnings`，Alembic 唯一 head 为 `0006_task005`。既有 TASK-003 head 断言按批准链路由 `0005_task007` 最小更新为 `0006_task005`。
- 剩余验证：含迁移的完整候选仍需 DEV-001 执行真实 RAGFlow/ClamAV 生命周期联调并绑定最终新 HEAD；完成前 PR 保持 Draft。

## TASK-005 DEV-001 隔离真实验证基础设施（2026-07-23）

- 范围：为 PR #37 提供独立 PostgreSQL、Redis、MinIO、ClamAV、Worker、迁移和验证器环境；共享 RAGFlow 仅通过 `host.docker.internal` API 访问，不启动、停止或修改共享服务。
- TDD：验证基础设施契约先后暴露迁移门禁、宿主 API 地址、测试镜像阶段、专用数据库命名、单次 Worker 初始化竞态和临时凭据清理缺失；新增契约测试后逐项修复。
- 真实验证：隔离栈迁移至 `0006_task005`；PostgreSQL 执行 `0006 -> 0005_task007 -> 0006`；ClamAV 拒绝 EICAR；安全文档完成上传、RAGFlow 解析、READY、检索和引用回传，验证器 `2 passed`。临时数据集、容器、网络、卷和工作区外临时凭据文件均已清理。
- 回归：Python 3.13 后端 `264 passed, 12 skipped, 2 warnings`；基础设施契约 `2 passed`；Compose `config --quiet`、PowerShell 语法、`pip check`、`compileall` 与 `git diff --check` 待本独立提交完成前复跑。两项 warning 均为既有第三方弃用提示。
- 边界：无业务代码、生产依赖、兼容代码或通用抽象层修改；仅新增隔离验证所需 Compose 服务、脚本、环境模板和契约测试。该基础设施提交须由 DEV-002 核验后 cherry-pick 到 PR #37；PR #37 继续 Draft，未申请 Merge 授权、不解锁下游、不进入 Stage 6。

## TASK-005 DEV-002 Critical 修正复验（2026-07-23）

- 修正 1：`worker`、`migrate`、`minio`、`clamav` 和 `validator` 全部置于 `validation` profile；普通平台 Compose 仅保留原 API、PostgreSQL、Redis 拓扑，验证脚本显式启用该 profile。
- 修正 2：临时环境目录必须匹配 `equipment-task005-<GUID>`、文件名必须为 `task005.env`，并且目录内必须存在由创建脚本写入的 `task005-validation-marker`；清理不满足来源校验时拒绝递归删除。
- 修正 3：真实验证循环改由 `app.modules.knowledge.worker_main.main(--limit 1)` 执行；同时修正 `limit` 关键字调用，避免只由 validator 直接调用底层同步函数。
- 复验：普通/validation Compose config、PowerShell 语法、契约 `2 passed`、Python 全量 `264 passed, 12 skipped, 2 warnings`；真实 PostgreSQL 往返和 RAGFlow/ClamAV 文档生命周期 `2 passed`。未产生新依赖、兼容层或无关修改。
- 门禁：修正提交尚未由 DEV-002 重新边界核验和 cherry-pick；PR #37 保持 Draft，不申请 Merge 授权、不解锁下游、不进入 Stage 6。

## TASK-005 DEV-001 基础设施复验 R2（2026-07-24）

- 根因：Compose Worker 作为独立进程仅加载知识模型，`knowledge_documents.created_by` 对 `users.id` 的外键目标未注册；首个上传文档触发 SQLAlchemy `NoReferencedTableError` 后 Worker 退出，文档停留在 `UPLOADING`。
- TDD：新增独立 Python 进程回归测试，初始因 `Base.metadata` 缺少 `users` 表失败；Worker 入口显式注册共享 identity 模型后通过。Worker 以 `--poll-seconds 1` 常驻轮询，真实联调测试不再在 validator 进程直接调用 Worker。
- 安全与失败传播：临时凭据环境创建将写入与 `icacls` 放入 `try/catch`，权限设置失败时删除专用目录；清理脚本即使 Compose 清理失败也先删除经过 marker/GUID/固定文件名校验的凭据目录，再传播清理失败。
- 真实验证：独立 PostgreSQL 17、MinIO、ClamAV、Compose Worker 和本机 RAGFlow 环境中，验证器上传安全文档后由 Compose Worker 推进为 `READY`，RAGFlow 检索与引用回传通过，EICAR 被 ClamAV 拒绝；专用 RAGFlow dataset、容器、网络、卷及工作区外临时凭据目录均已清理。
- 门禁：此基础设施分支仍待 DEV-002 边界核验后 cherry-pick 至 PR #37；PR #37 继续保持 Draft，不申请 Merge 授权、不解锁下游、不进入 Stage 6。

## TASK-005 DEV-002 接收基础设施增量（2026-07-24）

- 接收范围：DEV-001 基础设施分支 `codex/task-005-validation-infra` 的连续提交 `dbf4d68b074838bfdaf629b2b6897c6ec5d79843`、`579a98ea048430a4b79684b6191ec1a3d71cd574`、`6c2df422f36e84f9660cb16d3c7c925d9d9a6f7a` 已精确 cherry-pick 至 PR #37，生成本分支提交 `339956d`、`b8b840c`、`7daab78`。
- 边界核验：验证专用 `worker/migrate/validator/minio/clamav` 均位于 `validation` profile；清理脚本绑定系统临时目录、`equipment-task005-<GUID>`、`task005.env` 和 marker；真实测试不再直接调用底层同步函数，改由 Compose Worker 常驻轮询入口推进文档状态。
- 本地验证：TASK-005/Worker/迁移/基础设施契约定向 `10 passed, 2 skipped, 2 warnings`；Python 3.13 全量 `266 passed, 12 skipped, 2 warnings`；`pip check`、`compileall`、Alembic 唯一 `0006_task005 (head)`、`git diff --check` 通过。
- 未验证：当前 DEV-002 Mac 环境无 `docker` 和 `pwsh`，未本机复跑两套 Compose config 或 PowerShell 语法；这些结果引用 DEV-001 已提供的真实验证，仍需 DEV-001 对 PR #37 新 HEAD 复审绑定。
- 门禁：PR #37 保持 Draft；未请求 Merge 授权、不解锁 TASK-009/011、不进入 Stage 6。
- 治理状态：项目负责人已正式追认 PR #40/源 HEAD/合并结果；PR #41 治理收尾 Merge Commit `092eb84821131f6c6faa6b6a1c2acdb4079ecf8f` 已合入。TASK-007 治理闭环完成，可按依赖矩阵解锁下游；Stage 6 仍未批准。
