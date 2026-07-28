# 缺陷记录

### DEF-STAGE6-001：备份恢复性能与受控负载干扰证据未满足门槛

- 严重程度：Stage 6 阻断（测试/交付证据）；当前不是已确认的生产代码缺陷。
- 状态：Open，待集中处置。
- 发现时间：2026-07-28。
- 证据：在隔离 Compose 项目中，备份后向随机恢复项目执行恢复脚本的功能性命令退出码为 0，但包含附件压测对象的恢复耗时约 194.7 秒，超过已约定的 180 秒；同时尚未完成恢复过程中维持 10 个只读请求、并验证 P95 不超过 2 秒的组合试验。
- 边界：该结果来自一次包含大量测试附件对象的隔离环境，不能外推为生产容量结论，也不得删改结果以规避门槛。
- 必要动作：建立可复现的受控数据集，分别记录备份、恢复及组合负载的起止时间、请求数、P50/P95、错误率和容器资源；若仍超过阈值，提交最小化修复 PR 并在新精确 HEAD 上重跑。完成前 Stage 6 不得申请整体通过或进入 Stage 7。

### TASK-002 合并后治理台账修正（2026-07-17）

- 严重程度：交付治理 Important；不构成新的 `codebase/` 实现缺陷。
- 状态：已由 PR #25 Merge Commit `028da42eb9ab4b55ef981ac462e09993a31e8813` 集成；TASK-002 下游前置已解除。
- 发现：R10 指出任务摘要过期、TASK-005/006 依赖状态错误，以及 PR #20 缺少 DEV-001 手动合并记录。
- 处理：以 PR #20 的实际 Merge Commit `904886f48061e27c775f6ee2f8ddae99f5571ead`、执行人 DEV-001（`ll979053897-arch`）和已归档技术证据统一更新任务书、评审、自测、检查点与交接台账。
- 残余风险：审计脱敏的字段语义规则关闭已知别名漏洞，不宣称能识别攻击者以任意未知字段名承载的秘密；该风险不在本纯治理 PR 中扩大实现范围。

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

## TASK-002 / CR-036 缺陷复核（2026-07-16）

- DEV-002 对 PR #15 提出的 Standards 与 Spec 阻断统一由 CR-036 管理，不另行拆成重复 DEF。
- R6/R7 已修复公开契约、失败审计、完整设备字段、组织层级、固定角色/用户权限、附件引用脱敏和迁移问题。
- DEV-001 最终独立复审为 Critical 0、Important 0；未发现需要保持 Open 的新缺陷。
- 唯一非阻断提醒：Alembic `0002` 接近规模上限，后续数据库变化必须新增 revision；第三方 TestClient/httpx 弃用警告留待依赖维护任务处理。
- TASK-002 仍待 DEV-002 复审；若正式审核发现新阻断项，应在本台账新增 DEF 或重新打开 CR-036，不得改写本次历史结果。

## TASK-002 / CR-036 R8 缺陷复核（2026-07-17）

- DEV-002 最新 4 个 Important 均属于既有 CR-036 范围，不重复创建 DEF；代码候选为 `73030f83638b3b063db483029591720bf65aac21`。
- 固定目录、用户范围、脱敏变体和未知异常失败审计已由新增回归测试及真实 PostgreSQL 验证关闭。
- DEV-001 三轮复核为 Critical 0、Important 0；未发现新的 Open 产品/代码缺陷。
- 历史 `merge(task-002)` 类型与不可变 `0001` 职责说明为非阻断治理处置，详见 `CODE_REVIEW.md`；不得通过 force-push 或改写已发布 migration 处理。
- 既有 TestClient/httpx 弃用警告仍为非阻断依赖维护项；本次未升级或新增生产依赖。
- TASK-002 仍待 DEV-002 正式复审和后继 PR 集成，不得据本内部结论解锁依赖。

## TASK-002 / CR-036 R9 复审发现（2026-07-17）

- DEV-002 新发现为 CR-036 的剩余 Important，不另建重复 DEF：密码确认驼峰/中缀变体和附件未知正文别名可绕过失败审计脱敏。
- 根因和修复见 `CODE_REVIEW.md` R9；代码候选为 `ac6947a642f00ba48aebcb80064f87fcc4c01ea8`，新增数据库持久化断言。
- 当前状态：独立 `test` 镜像已补齐 pytest/httpx 并完成 PostgreSQL 17 `5 passed`；仍等待 DEV-002 复审，不得据内部证据提前关闭外部审核门禁。

## TASK-002 / CR-036 R10 复审发现（2026-07-17）

- DEV-002 补充发现属于既有 CR-036 的同一审计脱敏 Important，不新增重复 DEF：附件上下文标量、标量列表及紧凑密码键会绕过 R9 的字典白名单规则。
- 根因和修复见 `CODE_REVIEW.md` R10；代码候选 `b4d451009d1deb9dbe3286f5bff4db9414ef4aee`，新增直接脱敏和数据库持久化两层回归。
- 当前状态：DEV-001 内部复核未见 Critical/Important；真实 PostgreSQL 17、Compose 与 `/healthz` 已复测。外部审核仍未通过，TASK-002 不得视为完成或解除依赖。

## TASK-002 / CR-036 R11 复审发现（2026-07-17）

- DEV-002 的 R10 Important 属于既有 CR-036，不新增重复 DEF：附件/文件语义仅识别键首，Cookie 和紧凑密码规则不完整，导致失败审计可含明文。
- 根因和修复见 `CODE_REVIEW.md` R11；代码候选 `ea4338bad15f16048226a329801d3144b367909e`，新增直接和落库反例测试。
- 残余风险：无敏感语义的未知字段默认脱敏未实施，须作为独立安全强化项评估；不得把 R11 结论表述为可识别任意秘密。
- 当前状态：DEV-001 内部复核未见 Critical/Important；真实 PostgreSQL 17、Compose 与 `/healthz` 已复测。外部审核仍未通过，TASK-002 不得视为完成或解除依赖。
