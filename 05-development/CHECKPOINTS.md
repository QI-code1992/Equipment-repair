# 功能/页面检查点

当前不存在生产功能/页面检查点。静态原型检查点记录在 `03-ui-prototype/PROTOTYPE_CHECKPOINTS.md`，不得自动提升为生产检查点。

## FCP-001：平台运行环境基线

- 状态：稳定，允许工作包 B 以此作为生产工程前置。
- 范围：Task 1；`backend/`、`frontend/`、`infra/` 目录边界，FastAPI 应用工厂与 `GET /healthz`，PostgreSQL/Redis 内部 Docker 网络。
- 远端提交：`e742fb0`（`codex/stage-05-development`）。
- 已验证：健康检查测试 4 通过；Compose 配置校验通过；独立 Compose 项目 `equipment-task1` 中 PostgreSQL、Redis 为 healthy，API 实际 HTTP 请求返回 200。
- 接口冻结：`GET /healthz`、`backend/pyproject.toml`、`infra/docker-compose.yml`、`POSTGRES_DSN`、`REDIS_URL`。
- 限制：本检查点未发布公网端口；Nginx HTTPS 的实际公网入口与证书配置归 Task 10 部署工作处理。
