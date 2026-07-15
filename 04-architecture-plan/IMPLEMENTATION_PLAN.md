# 平台 Stage 5 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use `subagent-driven-development`（推荐）或 `executing-plans` 按任务逐项执行；步骤使用复选框追踪。

**目标：** 在单台 Windows + Docker Desktop/WSL2 上交付可审计的智能运维平台，以及由独立配置真实驱动的四个 Agent。

**架构：** 以 FastAPI 模块化单体承载业务 API、Agent Runtime 与 Worker；PostgreSQL 保存业务事实及 Agent 状态，RAGFlow/Elasticsearch 独立处理非结构化知识。所有模型输出经受控工具和人工确认边界进入业务流程。

**技术栈：** Python 3.13、FastAPI、SQLAlchemy/Alembic、PostgreSQL、Redis、MinIO、LangGraph、RAGFlow、Elasticsearch 8.11、Docker Compose、TypeScript Web 前端。

## 全局约束

- 所有 Git 推送只允许到 `codex/*` 开发分支，禁止直接推送 `main`。
- 不实现工厂/设备行级授权隔离或 `EquipmentGrant`；必须实施平台账号、角色、菜单、操作权限、线程隔离与审计。
- 历史维修案例只能查询 PostgreSQL；文档引用只能通过本地 RAGFlow。
- 每个 `agent_id` 独立配置；禁用共享配置覆盖；不实现 Agent 版本、发布或回滚 UI。
- 深度思考必须驱动实际模型推理参数和图执行；不输出、不存储原始思维链。
- 生产代码、测试和部署文件的确切目录须在任务 1 建立后保持稳定，后续任务不得重命名。

---

### Task 1：建立生产工程与本地容器基线

**文件：**
- Create：`backend/pyproject.toml`、`backend/app/main.py`、`backend/app/core/config.py`
- Create：`infra/docker-compose.yml`、`infra/.env.example`、`frontend/`
- Test：`backend/tests/test_health.py`

- [ ] 写出 `/healthz` 的失败测试，分别断言应用、PostgreSQL 和 Redis 未配置时返回健康检查失败。
- [ ] 运行 `pytest backend/tests/test_health.py -v`，确认初始失败。
- [ ] 实现配置加载、FastAPI 应用工厂、`GET /healthz` 和 Docker Compose 内部网络；只暴露 Nginx HTTPS。
- [ ] 运行 `docker compose -f infra/docker-compose.yml config` 与 `pytest backend/tests/test_health.py -v`，预期均通过。
- [ ] 提交：`feat: bootstrap platform runtime`。

### Task 2：认证、权限、审计与核心业务数据迁移

**文件：**
- Create：`backend/app/modules/identity/`、`backend/app/modules/audit/`、`backend/app/modules/equipment/`
- Create：`backend/alembic/versions/`、`backend/tests/modules/test_identity_permissions.py`

- [ ] 为平台账号、角色、菜单/操作权限、设备、审计和幂等键写失败测试；明确不创建 `EquipmentGrant`。
- [ ] 实现 PostgreSQL 迁移、认证中间件、操作权限依赖和审计写入。
- [ ] 验证无登录/无操作权限被拒绝，拥有操作权限的账号可访问不同工厂设备数据，且审计不记录敏感凭据。
- [ ] 提交：`feat: add identity audit and equipment foundation`。

### Task 3：故障、工单、维修与结构化案例闭环

**文件：**
- Create：`backend/app/modules/maintenance/`、`backend/tests/modules/test_maintenance_lifecycle.py`
- Modify：`backend/app/main.py`

- [ ] 为故障、工单、维修状态迁移、最终人工字段、直接开始维修不保留 AI 摘要写失败测试。
- [ ] 实现故障上报、开始维修、结束维修与案例沉淀 API；以数据库事务保护状态迁移和幂等。
- [ ] 实现 `/api/repair-cases/similar`，仅查询 `HistoricalRepairCase`。
- [ ] 运行模块测试和 API 契约测试，确认历史案例查询不调用 RAGFlow。
- [ ] 提交：`feat: add maintenance lifecycle and repair cases`。

### Task 4：知识文档与 RAGFlow 独立适配器

**文件：**
- Create：`backend/app/integrations/ragflow/`、`backend/app/modules/knowledge/`
- Create：`backend/tests/integrations/test_ragflow_adapter.py`

- [ ] 为上传、`UPLOADING -> PARSING -> READY|FAILED`、引用 ID 映射、超时降级写失败测试。
- [ ] 实现 MinIO 文件元数据、RAGFlow ingest/status/retrieve/delete 适配器与 Worker 同步任务。
- [ ] 验证只有 `READY` 文档可检索，RAGFlow 依赖与平台 PostgreSQL/Redis/MinIO 不共享账户。
- [ ] 提交：`feat: integrate isolated ragflow knowledge lifecycle`。

### Task 5：智能配置控制面与模型能力校验

**文件：**
- Create：`backend/app/modules/agent_config/`、`backend/tests/modules/test_agent_config.py`
- Modify：`frontend/src/pages/intelligent-config/`

- [ ] 为四个 `agent_id` 独立读取/保存、首次单独初始化、更新一个 Agent 不影响另外三个写失败测试。
- [ ] 实现 `AgentConfig`、模型能力 `supports_reasoning`、配置 API 与运行配置快照。
- [ ] 实现深度思考校验：非推理模型开启时 `PUT /api/agent-configs/{agent_id}` 返回 `MODEL_REASONING_UNSUPPORTED`。
- [ ] 移除原型/前端中页面加载重写统一 `localStorage` 默认配置的逻辑，改为 API 加载该 Agent 的独立配置。
- [ ] 提交：`feat: add independent agent configuration control plane`。

### Task 6：Agent Runtime、SSE 与安全过程事件

**文件：**
- Create：`backend/app/modules/agent_runtime/`、`backend/tests/modules/test_agent_runtime.py`
- Create：`frontend/src/components/agent/AgentConversation.tsx`

- [ ] 为线程归属、运行快照、SSE 顺序、恢复、原始思维链不入库不出流写失败测试。
- [ ] 实现 `AgentThread`、`AgentRun`、`ToolCall`、`AgentConfirmation`、LangGraph checkpoint 和 SSE 事件端点。
- [ ] 实现模型网关参数映射，使深度等级实际传递推理参数并产生真实 `reasoning_status`/工具事件。
- [ ] 验证刷新或容器重启可恢复 checkpoint，且 SSE 没有思维链、密钥或伪造事件。
- [ ] 提交：`feat: add auditable agent runtime and streaming`。

### Task 7：实现 AI 故障上报与智能问数 Agent

**文件：**
- Create：`backend/app/modules/agents/fault_reporting.py`、`backend/app/modules/agents/metric_query.py`
- Create：`backend/tests/agents/test_fault_reporting.py`、`backend/tests/agents/test_metric_query.py`

- [ ] 为缺失字段追问、人工确认后提交、最多五个指标批量查询、错误口径重新澄清写失败测试。
- [ ] 实现字段采集和指标查询状态机，使用配置中心提供的模型、上下文、流式、建议和引用开关。
- [ ] 验证 Agent 不自行提交业务事实、不生成指标数值，指标查询只执行一次已校验批量查询。
- [ ] 提交：`feat: add fault reporting and metric query agents`。

### Task 8：实现操作指引与故障诊断 Agent

**文件：**
- Create：`backend/app/modules/agents/operation_guidance.py`、`backend/app/modules/agents/fault_diagnosis.py`
- Create：`backend/tests/agents/test_operation_guidance.py`、`backend/tests/agents/test_fault_diagnosis.py`

- [ ] 为页面能力优先、最多两次定向检索、报警码具体追问、否定证据、证据不足、诊断采纳门槛和 8/24/4 上限写失败测试。
- [ ] 实现操作指引状态机与受约束的诊断“思考—行动—核验”图，使用受控工具和模型推理参数。
- [ ] 实现故障单创建后的预诊断任务、开始维修约三秒的平滑加载状态、采纳后预填和摘要关联。
- [ ] 验证直接开始维修不保存摘要；诊断 Agent 的历史案例来源为 PostgreSQL、文档引用来源为 RAGFlow。
- [ ] 提交：`feat: add guidance and fault diagnosis agents`。

### Task 9：完成前端集成与结束维修摘要

**文件：**
- Modify：`frontend/src/pages/fault-report/`、`frontend/src/pages/repair-execution/`、`frontend/src/pages/intelligent-config/`
- Test：`frontend/src/pages/**/*.test.tsx`

- [ ] 为独立左右滚动、固定底部输入、真实流式展示、引用折叠展开、诊断采纳按钮门槛和摘要位置写失败测试。
- [ ] 用 API 客户端替换静态原型数据源；保持已批准原型的直接开始、采纳开始与结束维修交互。
- [ ] 将只读 AI 诊断对话摘要放到“备件更换说明”之后；无采纳诊断时隐藏该区。
- [ ] 运行前端单元/交互测试和静态原型回归，记录差异。
- [ ] 提交：`feat: integrate configured agents into approved flows`。

### Task 10：补齐平台能力、部署、安全与回归

**文件：**
- Create：`backend/tests/e2e/`、`infra/nginx/`、`08-release-handoff/DEPLOYMENT_CHECKLIST.md`
- Modify：`06-testing/TEST_PLAN.md`、`06-testing/TEST_CASES.md`

- [ ] 为健康分、固定指标、附件扫描、超时降级、配置不可用、备份恢复写端到端失败测试。
- [ ] 配置 Nginx HTTPS、Docker 健康检查、备份与恢复脚本、外部 LLM/RAGFlow 连通性检查。
- [ ] 执行全量单元、API、集成、E2E、权限、安全和恢复演练；生成测试报告与开发检查点。
- [ ] 提交：`test: verify platform integration and operations`。

## 计划自检

- 覆盖：平台基础、业务闭环、知识、四个 Agent、独立配置、真实深度思考、前端、部署和测试均对应至少一个任务。
- 一致性：所有 Agent 运行均通过 `AgentConfig -> AgentRun.config_snapshot`；历史案例与文档检索来源分离；没有 `EquipmentGrant`、Agent 版本或思维链持久化任务。
- 范围：本计划只在 Stage 4 获批后执行；每个任务须先写失败测试、通过验证并创建开发分支检查点。
