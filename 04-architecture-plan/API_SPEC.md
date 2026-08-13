# API 规格

- 基线：已批准 v2.1
- 状态：Stage 4 已批准；见 `workflow/STAGE_APPROVALS.md` 的 Gate-005 与 Gate-006

所有写请求要求平台账号认证；可重复写请求需携带 `Idempotency-Key`；响应包含字段级校验错误和 `audit_event_id`。权限仅校验角色、菜单和操作权限，不按工厂或设备进行数据行过滤。

## 智能配置

| Method | Endpoint | 请求/响应要点 | 约束 |
|---|---|---|---|
| GET | `/api/agent-configs` | 返回四个 `agent_id` 的当前有效配置 | 不返回密钥。 |
| GET | `/api/agent-configs/{agent_id}` | 返回一个 Agent 的配置与模型能力 | 不回退到其他 Agent 配置。 |
| PUT | `/api/agent-configs/{agent_id}` | 保存该 Agent 的现有前台配置字段 | 深度思考开启时要求模型支持推理；只影响新 `AgentRun`。 |
| POST | `/api/agent-configs/{agent_id}/test-runs` | 用当前有效配置发起测试运行 | 与生产运行共用同一配置解析和校验。 |

## Agent 会话与事件

| Method | Endpoint | 请求/响应要点 | 约束 |
|---|---|---|---|
| POST | `/api/agent/threads` | `agent_id`、业务上下文，返回 `thread_id` | 全局入口仅接受前三个 Agent；诊断仅由开始维修上下文创建。 |
| POST | `/api/agent/threads/{thread_id}/messages` | 用户文本/附件引用，返回 `run_id` | 后端按 `agent_id` 加载配置并写入运行快照。 |
| GET | `/api/agent/runs/{run_id}/events` | SSE 事件流 | 仅推送真实过程状态、令牌、引用和建议；不推送思维链。 |
| POST | `/api/agent/threads/{thread_id}/resume` | 确认、补充信息或恢复标记 | 只能恢复创建者的线程或管理员线程。 |
| GET | `/api/agent/threads/{thread_id}` | 消息、已展示引用、确认状态、摘要 | 线程创建者或系统管理员可读。 |

Global Agent 的入口对所有已登录用户可见并可调用；故障正式提交、知识文档重试及其他业务写操作仍按各自接口权限校验。

## 账户安全 API

| Method | Endpoint | 请求/响应要点 | 约束 |
|---|---|---|---|
| POST | `/api/auth/password-reset/request` | 账号标识；返回统一不枚举结果 | 生成一次性限时凭证；密码和凭证不得写入日志、响应或持久 URL。 |
| POST | `/api/auth/password-reset/confirm` | 一次性凭证、新密码、确认新密码 | 校验未过期/未使用、密码策略和一致性；成功后凭证失效并要求重新登录。 |
| PATCH | `/api/auth/password` | `current_password`、`new_password`、`confirm_password` | 校验当前密码、账号状态、密码策略和一致性；成功撤销该账号所有会话并记录审计，失败不改变会话。 |

## 业务与知识工具 API

| Method | Endpoint | 用途 |
|---|---|---|
| POST | `/api/fault-reports` | 人工正式上报。 |
| POST | `/api/fault-reports/{id}/diagnosis-drafts` | 后台预诊断草稿任务。 |
| POST | `/api/fault-reports/{id}/start-repair` | 直接开始或采纳已确认诊断后开始维修。 |
| POST | `/api/work-orders/{id}/repair-result` | 提交维修人员最终处理结果。 |
| GET | `/api/repair-cases/similar` | 结构化同类设备相似案例查询。 |
| GET | `/api/metrics/catalog` | 固定指标目录。 |
| POST | `/api/metrics/query-batch` | 一次正式查询最多五个已校验指标。 |
| POST | `/api/knowledge/documents` | 上传并创建知识文档元数据。 |
| GET | `/api/knowledge/documents/{id}` | 查询 RAGFlow 生命周期状态。 |

内部工具不直接暴露给浏览器：`retrieve_knowledge`、`get_similar_repair_cases`、`query_metric_batch`、`get_page_capability`、`create_fault_draft`、`submit_confirmed_business_action` 均经服务端参数模型、权限校验、超时和审计封装。禁止 Agent 生成 SQL 或任意文件系统命令。

## 诊断状态与错误契约

诊断运行状态：`QUEUED`、`OPEN_LOADING`、`QUESTIONING`、`EVIDENCE_PENDING`、`DIAGNOSIS_READY`、`ADOPTED`、`DIRECT_START`、`UNAVAILABLE`。仅 `DIAGNOSIS_READY` 可以返回“采纳 AI 建议并开始维修”。

| 错误码 | 场景 | 前台行为 |
|---|---|---|
| `AGENT_DISABLED` | Agent 未启用 | 提示 AI 暂不可用，保留人工流程。 |
| `AGENT_CONFIG_INVALID` | 模型/知识库/推理配置不完整 | 提示配置不可用，保留人工流程。 |
| `MODEL_REASONING_UNSUPPORTED` | 非推理模型开启深度思考 | 拒绝保存并要求改绑模型或关闭开关。 |
| `RAGFLOW_TIMEOUT`、`LLM_TIMEOUT` | 外部依赖超时 | 不伪造结果；诊断降级为不可用或继续人工。 |
| `EVIDENCE_INSUFFICIENT` | 证据未满足根因门槛 | 继续追问、上传附件或直接开始维修。 |
