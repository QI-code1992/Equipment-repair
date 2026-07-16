# 自测

- 状态：尚未执行生产测试
- 原型证据：Node 静态检查位于 `06-testing/tests/`，不属于生产测试。
- 必要生产检查：单元、API 契约、权限、健康分、Agent/RAGFlow 集成、安全、性能和端到端测试。
- 验收候选包必须绑定精确 Commit SHA 和最新结果。

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
