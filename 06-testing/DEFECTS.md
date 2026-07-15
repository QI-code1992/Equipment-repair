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
- 状态：已发现 / 未纳入 CR-032 修复范围
- 发现时间：2026-07-15
- 复现命令：`python -m pytest codebase/backend/tests/test_health.py -q`
- 实际结果：导入 `codebase/backend/app/main.py` 时调用 `Settings()`，因缺少 `postgres_dsn` 和 `redis_url` 触发 `TypeError`，测试在收集阶段中止。
- 初步证据：`codebase/backend/app/main.py` 和 `codebase/backend/app/core/config.py` 均包含重复定义；该内容在本次目录迁移前已存在，CR-032 只执行 Git 路径重命名，没有修改业务代码。
- 处理边界：需要单独诊断与修复，不得通过修改测试或弱化健康检查要求使迁移验证通过。

### DEF-004：Compose 基线存在重复服务和网络定义

- 严重程度：阻断 Compose 配置验证
- 状态：已发现 / 计划在 Stage 5 TASK-001 修复
- 发现时间：2026-07-15
- 静态证据：`codebase/infra/docker-compose.yml` 重复定义 `postgres`、`redis` 和顶层 `networks`，且网络结构互相矛盾。
- 未验证项：当前协调环境没有 Docker，未运行 `docker compose config`；不得据此声称 Compose 的具体运行错误或容器状态。
- 处理边界：Stage 4 只登记风险和修正任务顺序；任何 Compose 配置修改及真实运行验证必须在 Stage 4 → Stage 5 门禁批准后由 `DEV-001` 执行。
