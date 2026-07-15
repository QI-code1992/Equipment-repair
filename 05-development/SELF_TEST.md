# 自测

- 状态：已执行 TASK-001 与 TASK-006 非数据库切片生产测试；其他生产测试仍按任务依赖推进
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

## TASK-006 非数据库切片验证（2026-07-15）

- 精确基线：输入 `42098613ffa20faed3bb0dcb842a0121722565bd`；实现 HEAD `f7da3393f8861e3f7b8a453629fce7079915e58e`；Python `3.13.14`（`codebase/backend/.venv/bin/python`）。
- 模块：`codebase/backend/.venv/bin/python -m pytest codebase/backend/tests/modules/test_agent_config.py codebase/backend/tests/modules/test_agent_config_api.py -q` → `21 passed, 1 warning in 0.08s`。
- 后端全量：`codebase/backend/.venv/bin/python -m pytest codebase/backend -q` → `25 passed, 1 warning in 0.19s`。
- 两次有效 pytest 的唯一 warning 均为 `fastapi/testclient.py:1` 的 `StarletteDeprecationWarning`：当前 Starlette TestClient 使用 `httpx` 的方式已弃用并提示未来使用 `httpx2`；warning 已单独记录，不归类为无警告通过。两次有效 pytest 均无 skip 或失败。
- 语法：`codebase/backend/.venv/bin/python -m compileall -q codebase/backend/app codebase/backend/tests` → 退出码 0、无输出。
- 空白：`git diff --check 42098613ffa20faed3bb0dcb842a0121722565bd..HEAD` → 退出码 0、无输出。
- 范围：`git diff --name-status 42098613ffa20faed3bb0dcb842a0121722565bd..HEAD` 仅含两份 TASK-006 设计/计划、Agent 配置模块及模块测试；无 `codebase/infra/`、`codebase/frontend/`、`03-ui-prototype/`、迁移或 `app/main.py` 变更。
- 说明：首次从 `codebase/backend` 工作目录误用仓库根相对解释器路径，shell 以 127 退出且 pytest 未启动；已改回仓库根目录用指定解释器重跑，未将该命令错误计作测试结果。
- 结论：TASK-006 非数据库切片已验证；TASK-006 总任务仍未完成。数据库/迁移/事务/认证审计/正式路由挂载/真实模型测试/前端均未完成；数据库继续 Blocked By TASK-002，TASK-007 不解锁。DEV-002 未执行或宣称 Docker、Compose、RAGFlow 通过。
