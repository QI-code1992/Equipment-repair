# 功能/页面检查点

静态原型检查点记录在 `03-ui-prototype/PROTOTYPE_CHECKPOINTS.md`，不得自动提升为生产检查点。

## FCP-001：平台运行环境基线

- 状态：已重新验证，允许工作包 B 以此作为生产工程前置。
- 范围：TASK-001；`codebase/backend/`、`codebase/frontend/`、`codebase/infra/` 目录边界，FastAPI 应用工厂与 `GET /healthz`，PostgreSQL/Redis 内部 Docker 网络。
- 修复提交：`87538b04a168cb3c11c2e65dfb976d3a206d8218`（`codex/task-001-runtime-baseline`）；推送后作为远端可恢复检查点。
- 已验证：Python 3.13.14 下 `pytest codebase/backend/tests/test_health.py -q` 为 4 passed；`docker compose ... config --quiet` 通过；独立 Compose 项目 `equipment-task1` 中 PostgreSQL、Redis 为 healthy，API 容器内实际请求 `/healthz` 返回 200。
- 接口冻结：`GET /healthz`、`codebase/backend/pyproject.toml`、`codebase/infra/docker-compose.yml`、`POSTGRES_DSN`、`REDIS_URL`。
- 限制：本检查点未发布公网端口；Nginx HTTPS 的实际公网入口与证书配置归 Task 10 部署工作处理。

## FCP-002：身份、审计与设备主数据基础

- 状态：任务分支已验证并推送；PR [#15](https://github.com/QI-code1992/Equipment-repair/pull/15) 已 Ready for review，合入 `codex/stage-05-integration` 后解锁依赖 TASK-002 的数据库集成。
- 范围：TASK-002；Alembic revision `0001`、会话认证、角色/权限、审计、全局请求指纹幂等、组织树和设备主数据 API。
- 远端恢复点：`0b0d9cf0dc066143c0a57d4683567fadb4714c12`（`codex/task-002-identity-equipment`）。
- 交接证据：`9f162b421f4fefae4cdd69a001891c7e83d4bc13` 已推送至同一任务分支。
- 已验证：Python 3.13.14 下 38 tests passed；Compose 配置和 API 镜像构建通过；PostgreSQL downgrade/upgrade/current 通过；容器 `/healthz` 为 200；真实并发幂等、唯一冲突和组织树竞争通过。
- 接口冻结：`get_current_user`、`require_permission(code)`、`User/Role/Permission/LoginSession/AuditEvent/IdempotencyRecord/Organization/Equipment`、`0001`、`Idempotency-Key` 与 `audit_event_id`。
- 边界：不提供行级数据过滤；设备存在活跃故障时的停用保护由 TASK-003 实现；在合入集成分支前，TASK-003 与 DEV-002 的数据库集成仍保持阻塞。
