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

## CR-032 目录迁移验证（2026-07-15）

- 当前后端测试入口：`pytest codebase/backend/tests/test_health.py -q`。
- 当前 Compose 校验入口：`docker compose --env-file codebase/infra/.env.example -f codebase/infra/docker-compose.yml config --quiet`。
- Stage 3 原型静态回归仍从 `06-testing/tests/*.test.js` 执行。
- 目录结构：`codebase/backend/`、`codebase/frontend/`、`codebase/infra/` 均存在；根目录旧路径和 `codebase/prototype/` 均不存在；通过。
- 原型回归：执行全部 `06-testing/tests/*.test.js`，14/14 通过。
- 后端：使用 `/tmp/equipment-repair-verify` 一次性 Python 3.12 环境安装项目已声明的 FastAPI、httpx、pytest 后执行；测试收集失败，`Settings()` 缺少 `postgres_dsn` 与 `redis_url`，见 `DEF-003`。本机没有项目要求的 Python 3.13，因此未宣称后端通过。
- Compose：未验证；当前执行环境缺少 `docker` 命令。
- 路径与差异：目录断言和 `git diff --check` 通过；技能与工件参考中的归档规则一致性扫描通过。
