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
