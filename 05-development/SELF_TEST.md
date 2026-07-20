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
