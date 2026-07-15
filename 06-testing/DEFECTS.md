# 缺陷记录

### DEF-001: Legacy metric static test conflicted with current requirement

- 严重程度：重大基线不一致
- 状态：候选验证已解决；生产行为仍未验证
- 证据：导入的 `06-testing/tests/intelligent-config-metric-inline.test.js`
- 当前预期行为：固定指标目录为只读。
- 处理：测试现在检查可见的只读指标弹窗，完整静态套件通过；生产指标 API 尚未实现。

### DEF-002: Prototype runbook paths were stale before migration

- 严重程度：中等文档缺陷
- 状态：候选迁移修复
- 证据：原 README 和运行说明引用了缺失文件/根目录服务器路径。
- 必要动作：更新根入口并验证迁移后的服务器路径。

### DEF-003：后端健康检查基线存在重复定义冲突

- 严重程度：阻断后端测试收集
- 状态：已解决 / TASK-001 已验证
- 发现时间：2026-07-15
- 复现命令：`python -m pytest codebase/backend/tests/test_health.py -q`
- 实际结果：导入 `codebase/backend/app/main.py` 时调用 `Settings()`，因缺少 `postgres_dsn` 和 `redis_url` 触发 `TypeError`，测试在收集阶段中止。
- 初步证据：`codebase/backend/app/main.py` 和 `codebase/backend/app/core/config.py` 均包含重复定义；该内容在本次目录迁移前已存在，CR-032 只执行 Git 路径重命名，没有修改业务代码。
- 处理：删除 `main.py` 中第二套无参数应用工厂及 `config.py` 中重复字段；保留四条已批准的应用、PostgreSQL、Redis 缺失与完整配置健康检查契约。Python 3.13.14 下结果为 `4 passed, 1 warning`。

### DEF-004：Compose 基线存在重复服务和网络定义

- 严重程度：阻断 Compose 配置验证
- 状态：已解决 / TASK-001 已验证
- 发现时间：2026-07-15
- 静态证据：`codebase/infra/docker-compose.yml` 重复定义 `postgres`、`redis` 和顶层 `networks`，且网络结构互相矛盾。
- 处理：删除重复 `postgres`、`redis` 与顶层 `networks` 定义，保留唯一 `platform` 内部网络。`docker compose ... config --quiet` 通过；独立 `equipment-task1` 项目中 PostgreSQL、Redis 均为 `healthy`，API 实际健康检查返回 200。
