# Stage 5 双团队工作包

## 分工原则

- 以业务事实边界划分：业务状态、权限、事务和结构化历史案例由同一工作包负责；RAGFlow、Agent 配置、运行时与前端对话由同一工作包负责。
- Task 1 是共同前置，不并行修改其目录结构、依赖清单或 Docker Compose 主文件。
- 两包只通过已提交、已验证的 API 与数据契约协作；不得复制对方领域模型或直接读写对方数据库表。
- 每个工作包在独立 `codex/*` 分支和工作区执行，稳定单元先推送并记录 `05-development/CHECKPOINTS.md`，再供另一包依赖。

## 共同前置：WP-A.0 工程基线

负责人：工作包 A。工作包 B 在此项通过前只可审阅接口和准备测试用例，不创建生产目录或依赖。

- 范围：实施计划 Task 1。
- 交付：`codebase/backend/`、`codebase/frontend/`、`codebase/infra/` 的稳定目录边界，Python 3.13 FastAPI 健康检查，PostgreSQL/Redis Docker 内部网络与可执行测试命令。
- 接口冻结点：`GET /healthz`、`codebase/backend/pyproject.toml`、`codebase/infra/docker-compose.yml`、环境变量命名。
- 验收：健康测试、Compose 配置检查、容器健康检查通过；创建 FCP-001 后，两个包才可并行实施。

## 工作包 A：业务平台内核

目标：交付可审计的业务事实与维修闭环，成为所有 Agent 的唯一写入边界。

### 负责范围

1. 实施计划 Task 1、Task 2、Task 3，以及 Task 10 中平台 API、权限、安全、备份恢复和 Nginx 相关工作。
2. 平台账号、角色/菜单/操作权限、审计、幂等键、组织与设备主数据。
3. 故障上报、工单、开始/结束维修、人工最终字段与 `HistoricalRepairCase` 沉淀。
4. 结构化历史案例查询 `GET /api/repair-cases/similar`；不得调用 RAGFlow。

### 对外契约

- 业务 API 是故障、工单、维修记录和历史案例的唯一写入者。
- 提供 `/api/fault-reports`、`/api/fault-reports/{id}/start-repair`、`/api/work-orders/{id}/repair-result`、`/api/repair-cases/similar`。
- 直接开始维修不保存 AI 摘要；只有明确采纳诊断后的维修记录可关联只读摘要。
- 向工作包 B 提供已认证的业务 API 与稳定迁移版本；B 不直接写业务表。

### 依赖与里程碑

- A.0：Task 1 通过后开放工程骨架。
- A.1：Task 2 通过后开放身份、权限、审计和迁移基础。
- A.2：Task 3 通过后开放诊断 Agent 所需的业务上下文、开始维修和历史案例契约。

## 工作包 B：AI、知识与交互

目标：交付独立配置驱动的四个 Agent、真实 RAGFlow 文档生命周期与前端对话集成。

### 负责范围

1. 实施计划 Task 4 至 Task 9。
2. 独立 RAGFlow 依赖栈、知识文档生命周期、引用映射与超时降级。
3. 四个 `agent_id` 的独立配置、模型能力校验、运行快照、LangGraph、SSE 安全过程事件与线程隔离。
4. AI 故障上报、智能问数、操作指引、故障诊断四类 Agent，以及批准原型的前端 API 集成。

### 实施计划任务映射

| 实施计划任务 | 工作包 B 交付 |
|---|---|
| Task 4 | RAGFlow 独立部署、知识文档与引用生命周期。 |
| Task 5 | 四个 Agent 的独立配置与模型能力校验。 |
| Task 6 | Agent 线程、运行快照、LangGraph 与 SSE 安全过程事件。 |
| Task 7 | AI 故障上报与智能问数 Agent。 |
| Task 8 | 操作指引与故障诊断 Agent。 |
| Task 9 | 已批准原型的前端 API、流式对话与结束维修摘要集成。 |

### 对外契约

- 文档检索只经 RAGFlow；结构化案例仅调用工作包 A 的 `/api/repair-cases/similar`。
- Agent 只调用白名单业务工具，不能直连业务数据库、生成 SQL 或直接写业务事实。
- `AgentConfig -> AgentRun.config_snapshot` 为运行配置来源；不得共享默认配置、不得实现 Agent 版本功能。
- SSE 仅输出真实安全过程事件，不输出或保存原始思维链。

### 依赖与里程碑

- B.0：等待 A.0 后开始 Task 4、Task 5、Task 6 的工程实现。
- B.1：等待 A.1 后接入认证、权限与审计。
- B.2：等待 A.2 与 RAGFlow 生命周期通过后实施故障诊断 Agent 和维修前/后端集成。
- B.3：Task 9 只消费 A.2、B.0-B.2 已验证 API，不改写工作包 A 的业务状态逻辑。

## 协作与合并顺序

1. A 完成 A.0，创建 FCP-001；B 从该提交创建或更新自己的工作分支。
2. A 与 B 并行：A 推进 A.1/A.2；B 推进 RAGFlow、配置中心和运行时。
3. B 的故障诊断与维修前端集成等待 A.2、RAGFlow 和运行时三个依赖均通过。
4. 最后由 A 负责平台安全/部署闭环，B 负责 Agent/前端回归；共同进入 Stage 6 的完整测试。

## 禁止的交叉修改

- 工作包 B 不修改 A 负责的故障、工单、维修、历史案例状态迁移和数据库业务事实。
- 工作包 A 不修改 B 负责的 Agent 编排、RAGFlow 适配器、配置中心或对话组件。
- `codebase/backend/app/main.py`、`codebase/infra/docker-compose.yml`、共享迁移基线只由当前对应责任方在评审后合并；另一方通过小型、可审阅的集成提交接入。
