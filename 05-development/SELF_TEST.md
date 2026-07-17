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

## TASK-002 认证、权限、审计与设备基础（2026-07-15）

- TDD：首个管理员引导、权限/角色查询、组织/设备更新、登录/登出/权限拒绝审计、全局请求指纹幂等、唯一冲突、外键、组织循环和脱敏均先得到失败用例，再完成实现；审查整改累计关闭 1 个 Critical、13 个 Important、4 个 Minor。
- Python：`D:\codex\tools\equipment-task1-py313\Scripts\python.exe --version` 返回 `Python 3.13.14`；`python -m pytest codebase/backend/tests -q` 最终为 `38 passed, 1 warning`。唯一告警来自 FastAPI/Starlette TestClient 的第三方弃用提示。
- Compose：`docker compose --env-file codebase/infra/.env.example -f codebase/infra/docker-compose.yml config --quiet` 通过；API 镜像重建成功，并已将 `alembic.ini` 与 migration revisions 纳入镜像。
- 迁移：在 `equipment-task2` PostgreSQL 17 容器执行 `alembic downgrade base`、`alembic upgrade head`、`alembic current` 均成功，最终为 `0001 (head)`。
- 健康：新镜像容器内请求 `/healthz` 返回 HTTP 200 与 `{"status":"ok","service":"equipment-operations-platform"}`。
- Bootstrap：首次管理员引导成功并写入 1 条 `user.bootstrap` 系统审计（`actor_user_id` 为空）；空凭据和第二次引导均被拒绝。
- PostgreSQL 竞争：同一幂等键的两个并发创建设备请求均为 201 且响应一致；不同键同时创建同一设备编码为 201/409，冲突码为 `EQUIPMENT_CODE_EXISTS`。
- 组织完整性：未知 `organization_id` 返回 404；顺序成环返回 422；并发 A→B/B→A 更新在共享事务锁下返回 200/422，未形成循环。
- 静态：`python -m compileall -q app` 与 `git diff --check` 通过；Git 仅提示工作树 LF→CRLF 转换，不是内容错误。
