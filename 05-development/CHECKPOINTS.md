# 功能/页面检查点

静态原型检查点记录在 `03-ui-prototype/PROTOTYPE_CHECKPOINTS.md`，不得自动提升为生产检查点。

## FCP-001：平台运行环境基线

- 状态：已重新验证，允许工作包 B 以此作为生产工程前置。
- 范围：TASK-001；`codebase/backend/`、`codebase/frontend/`、`codebase/infra/` 目录边界，FastAPI 应用工厂与 `GET /healthz`，PostgreSQL/Redis 内部 Docker 网络。
- 修复提交：`87538b04a168cb3c11c2e65dfb976d3a206d8218`（`codex/task-001-runtime-baseline`）；推送后作为远端可恢复检查点。
- 已验证：Python 3.13.14 下 `pytest codebase/backend/tests/test_health.py -q` 为 4 passed；`docker compose ... config --quiet` 通过；独立 Compose 项目 `equipment-task1` 中 PostgreSQL、Redis 为 healthy，API 容器内实际请求 `/healthz` 返回 200。
- 接口冻结：`GET /healthz`、`codebase/backend/pyproject.toml`、`codebase/infra/docker-compose.yml`、`POSTGRES_DSN`、`REDIS_URL`。
- 限制：本检查点未发布公网端口；Nginx HTTPS 的实际公网入口与证书配置归 Task 10 部署工作处理。

## FCP-006-NDB：Agent 配置非数据库实现检查点

- 状态：TASK-006 非数据库切片已验证；这是可恢复的非数据库实现检查点，不是 TASK-006 完成门禁。
- 范围：不可变领域模型、`AgentConfigRepository` 与 `ModelCatalog` 两个外部端口、四 Agent 单独初始化/读取/保存、模型推理能力校验、不可变配置快照、未挂载 API 契约。
- 精确实现提交：`33d7712334044437eba0d3fc884859d48a3c71ed`、`7cbf76bb9ae627e023cbeaa86fd883b18a916373`、`f7da3393f8861e3f7b8a453629fce7079915e58e`；实现 HEAD 为 `f7da3393f8861e3f7b8a453629fce7079915e58e`，分支 `codex/task-006-agent-config`。
- 验证：Python 3.13.14 下模块 `21 passed, 1 warning`，后端全量 `25 passed, 1 warning`；warning 为同一条第三方 `StarletteDeprecationWarning`。`compileall` 与 `git diff --check` 退出码 0，范围检查未发现数据库、前端、infra、原型、迁移或 `app/main.py` 变更。
- 审查：Tasks 1–3 已逐任务审查；Task 2 保留四项非阻塞 Minor 测试增强（空列表/未初始化、身份不匹配隔离、完整快照 sentinel、精确范围边界）。
- 未完成：数据库仓储、迁移、事务/并发唯一性、认证/权限/审计接入、正式路由挂载、真实模型测试、前端集成。因此 TASK-006 总任务仍未完成。
- 依赖与环境：数据库部分继续 Blocked By TASK-002；TASK-007 不得解锁；DEV-002 未执行或宣称 Docker、Compose、RAGFlow 验证通过。
- 工程声明：未新增生产依赖、兼容代码或范围外抽象，无无关修改。
