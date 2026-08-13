# 新能源装载机设备智能运维平台 SPEC

- 基线：已批准 v1.1
- 状态：Stage 1 已批准；见 `workflow/STAGE_APPROVALS.md` 的 Gate-002
- 关联 PRD：`01-requirements/PRD.md`

## 1. 系统边界

| 组件 | 职责 | 禁止事项 |
|---|---|---|
| 业务系统 | 认证、菜单、权限、设备、故障、工单、维修、健康分服务、审计和界面 | 将静态演示数据当作业务事实 |
| LangGraph Agent | 意图识别、权限门禁、缺失字段收集、受控工具调用、人工确认和回复 | 直接写数据库、计算健康分、绕过业务 API |
| RAGFlow | 文档解析、切片、向量化、索引、检索、重排和引用 | 保存业务事实、计算指标、创建工单 |
| LLM | 理解语言、总结 API/RAG 结果 | 猜测数值、诊断事实、来源或权限 |

## 2. 角色与权限矩阵

| 能力 | 系统管理员 | 设备管理员 | 维修工 | 产线作业员 |
|---|---:|---:|---:|---:|
| User/role/menu/operation management | Manage | View | None | None |
| User management scope (`user_management.view_all`) | All users | Granted scope | Self only | Self only |
| Equipment list/detail | Manage | Manage | View | View assigned context |
| Equipment knowledge | Manage | Manage | View | None |
| Manual fault report | Create/view | Create/view | Create/view | Create/view |
| AI floating Agent | Use/manage | Use | Use | Use |
| AI fault-report creation | Create | Create | Create | Create |
| AI diagnosis review | View | Review/confirm | View | View related |
| Draft work order | Manage | Confirm/dispatch | View | View related |
| Repair execution | View | View/accept | Execute/submit | View progress |
| Health score/BI | View | View | View | View related |

必须执行服务端授权。设备授予仅约束 Agent 的设备查询和上报，不扩展为通用数据过滤。

Global Agent 入口对所有已登录用户可见并可调用，暂不按权限码隐藏或阻止入口；其业务写操作仍执行各自 API 的服务端权限校验。

`user_management.view_all` controls user-management visibility; it does not expand Agent device grants or create general data permissions.

## 3. 页面与路由契约

| 页面 | 候选路由 | 必要状态 |
|---|---|---|
| Login | `/login` | default, invalid, disabled, loading |
| Workbench | `/workbench` | default, empty, error, permission |
| BI dashboard | `/bi-dashboard` | default, empty, error, filter |
| Equipment ledger | `/equipment` | list, empty, loading, error, permission |
| Factory modeling | `/factory-modeling` | tree, detail, add/edit, disable cascade, delete blocked |
| Equipment add/edit/detail | `/equipment/new`, `/equipment/:id/edit`, `/equipment/:id` | validation, saving, error, forbidden |
| Equipment knowledge/config | `/intelligent-config` | tab, upload states, failed index, readonly metrics |
| Fault report | `/fault-report` | draft, validation, AI pending, submitted |
| Agent report | `/agent-report` | permission identified, missing fields, handoff, submit gate |
| Maintenance records | `/maintenance-records` | list, detail modal, empty, error |
| Repair execution | `/repair-execution` | assigned, editing, submitted, forbidden |
| System management | `/system-management` | user/role/menu/audit tabs, readonly/permission |
| Global Agent | drawer on every authenticated page | closed, open, tab history, collecting, preview, error |

历史数据导入页面不是当前路由、菜单、权限或 API 需求。
独立 `/intelligence-audit` 页面不是当前路由、菜单或原型需求；调用记录与知识文档状态由 `/intelligent-config` 承载。根路径 `/` 仅作为登录后的默认跳转入口。

### 3.1 账户安全契约

- `POST /api/auth/password-reset/request`：提交账号标识，始终返回不泄露账号是否存在的统一结果；服务端生成一次性、限时找回凭证，凭证不得写入日志。
- `POST /api/auth/password-reset/confirm`：提交一次性凭证、新密码、确认新密码；校验凭证未过期且未使用、密码策略和两次新密码一致，成功后凭证立即失效并要求重新登录。
- `PATCH /api/auth/password`：提交 `current_password`、`new_password`、`confirm_password`；校验当前密码、账号状态、密码策略和一致性。成功后撤销该账号现有会话并写入审计事件；失败不得撤销会话。
- 密码、凭证、Cookie、Token 不得出现在日志、URL、错误响应或审计明文中。

## 4. 数据契约

### Equipment

`id`, `code` unique, `name`, `model`, `type`, `manufacturer`, `manufacturedAt`, `commissionedAt`, `operatingHours >= 0`, `status`, `ownerUserId`, `imageRefs`, timestamps.

### Fault report

`id`, `equipmentId`, `submitterId`, `urgency`, `symptom`, `occurredAt <= now`, `duration`, `possibleLocation`, `description`, `attachmentRefs`, `status`, `submittedAt`, `auditRefs`. AI 上报正式提交前 `occurredAt` 与 `duration` 必填。Status: `AI_DRAFT -> PENDING_ACCEPT -> IN_REPAIR -> PROCESSED`.

### Work order

`id`, `faultId`, `assigneeId`, `diagnosisRef`, `repairAdviceRef`, `status`, `actualCause`, `actualSolution`, `repairResult`, `inspectionResult`, timestamps. Status: `DRAFT -> PENDING_ACCEPT -> IN_REPAIR -> PENDING_INSPECTION -> COMPLETED`, with reject/repair exception paths.

### Health score

`equipmentId`, `score`, `grade`, `calculatedAt`, `periodStart`, `periodEnd`, `components`, `serviceStatus`. Snapshot: before/after score, trigger, deductions/recoveries, fault/order refs, calculation time.

### Knowledge document

`id`, `datasetId`, `ragDocumentId`, `name`, `mimeType`, `size <= 100MB`, `status`, `failureReason`, `sourceRefs`, timestamps. Only `READY` documents are retrievable.

## 5. 健康分服务契约

`GET /api/equipment/{equipmentId}/health-score` returns score, grade, component breakdown, current period, snapshot summary and `serviceStatus`. On failure it returns an error status; clients must not substitute cached, zero or empty values. Workbench, BI, ledger, detail and metric-query adapters call this service.

## 6. 指标查询契约

`GET /api/metrics/catalog` returns the fixed 40 metric definitions, allowed dimensions, formula, period and examples. `POST /api/metrics/query` accepts only a catalog metric ID, allowed dimension values, and a date range. Agent tool `get_metric` may call only these endpoints. The LLM receives results and may summarize them but cannot create values.

## 7. Agent 工具白名单

`get_metric`, `get_health_score`, `get_granted_equipment`, `retrieve_knowledge`, `create_fault_draft`, `submit_fault_report`, `get_fault_progress`. Every write tool requires a permission check and, where specified, human confirmation. RAG citations must include document and chunk identifiers.

The allowlist is closed: no direct database, arbitrary SQL, health-score write, maintenance-record write, permission/user mutation or filesystem-execution tool may be registered.

## 8. Agent 状态机

### AI 故障上报

`load_context -> check_permission -> collect_equipment -> collect_urgency -> collect_symptom -> collect_optional_context -> preview -> human_confirm -> create_fault_draft -> final_response`.

缺少必填字段时返回收集环节；权限拒绝时结束并说明原因；附件失败时保留文字上下文并提示重试。

### 智能问数

`load_context -> detect_intent -> match_metric -> validate_dimensions -> ask_missing_or_query -> summarize -> final_response`.

未知指标、不允许的维度和后端错误都必须明确失败，不得猜测数值。

### 诊断与维修建议

`load_context -> check_permission -> retrieve_knowledge -> load_business_data -> generate_diagnosis -> generate_repair_advice -> human_review -> draft_work_order -> final_response`.

低置信度、高压、制动或其他安全关键场景必须人工复核并展示安全指引。

### Agent 运行契约

- `POST /api/agent/threads` creates a user-bound thread.
- `POST /api/agent/threads/{thread_id}/messages` streams `token`, `tool_started`, `tool_finished`, `interrupt`, `completed`, and `error` events through SSE.
- `POST /api/agent/threads/{thread_id}/resume` resumes a LangGraph interrupt using the same `thread_id`.
- `GET /api/agent/threads/{thread_id}` is visible only to the creator or system administrator.
- Shared state includes `thread_id`, `user_id`, `role`, `page_context`, `messages`, `tool_results`, `citations`, `pending_confirmation`, and `audit_id`.

## 9. 校验与异常规则

- Equipment code duplicate blocks save.
- Equipment deactivation is blocked by pending/repairing faults.
- Fault requires one equipment, urgency and symptom; occurrence cannot be future.
- AI preview is readonly; edits happen through dialogue or fault-report page.
- AI draft cannot become a formal pending fault until user submits.
- Work order cannot close without actual cause, solution and repair result.
- RAGFlow parse/index failure excludes a document from retrieval.
- Agent unavailable does not block manual fault and work-order flows.
- Permission failures are audit events.
- AI fault reporting pauses on missing `occurredAt` or `duration` and resumes after user input; formal submission always requires explicit user confirmation.
- RAGFlow empty retrieval returns an explicit no-citation result; it must not be converted into a fabricated citation or answer.
- Work-order UI labels map to API states: `待派单`=`DRAFT/PENDING_ACCEPT`, `维修中`=`IN_REPAIR`, `待验收`=`PENDING_INSPECTION`, `已关闭`=`COMPLETED`.

## 10. 非功能需求追踪

| NFR | 规格说明 |
|---|---|
| NFR-001 安全 | 服务端认证、审计事件、密钥不得进入 Git |
| NFR-002 可解释性 | 引用 ID、置信度、评分构成 |
| NFR-003 可用性 | Agent/RAGFlow 不可用时保留人工流程 |
| NFR-004 可追溯性 | 精确 Commit SHA、阶段台账和变更编号 |
| NFR-005 运维 | Windows 演示、00:10 备份、保留 10 天、Tailscale Funnel |

## 11. 待确认工程决策

Confirm before Stage 4 approval: first equipment models, supported document MIME types, RAGFlow deployment, embedding/rerank models, LLM deployment/data boundary, metadata schema, database choice, API authentication, and backup storage.

## 12. 接单前故障诊断 Agent 交互规格（候选 v1.1）

### 12.1 配置读取

页面读取“故障诊断 Agent”的 `enabled`、`streaming`、`suggestions`、`sources`、默认 LLM 与上下文轮数配置。配置关闭、缺失、调用失败或超过 30 秒时，状态为 `UNAVAILABLE`，仅提供人工直接开始维修。

### 12.2 状态机

`PRE_DIAGNOSIS_QUEUED -> OPEN_LOADING -> QUESTIONING -> EVIDENCE_PENDING -> DIAGNOSIS_READY -> ADOPTED | DIRECT_START | UNAVAILABLE`。

- `OPEN_LOADING`：固定展示理解故障、检索同类维修、检索知识库、形成首问四个阶段，约 3 秒后转入 `QUESTIONING`。
- `QUESTIONING`：Agent 主动提出一个当前最重要的问题；输入区固定在右侧底部，消息区独立滚动。
- `EVIDENCE_PENDING`：如用户确认有报警码，输入区进入 `报警码` 必填状态，自动聚焦，发送按钮仅在输入含数字的具体报码后可用；“暂无报码/未读取”可作为否定证据完成该项。
- `DIAGNOSIS_READY`：至少收集故障复现工况和两类以上有效技术证据后，输出可折叠的根因、检查清单、维修方案、备件与安全建议，并开放采纳按钮。
- `DIRECT_START`：删除临时 Agent 状态与摘要，不预填结束维修字段。
- `ADOPTED`：持久化人工可编辑的预填字段与 AI 对话摘要；结束维修详情仅展示摘要，不展示原始模型消息或思维过程。

### 12.3 动态问题计划

问题计划由设备型号、故障现象、故障描述、检索案例、知识库和已确认事实共同决定。至少覆盖电池压差、转向角传感器、液压、驱动过温/限扭和通用电气故障。每种计划的“报警码、关键测量、部件检查、复现工况”问题及快捷建议不同；生产环境由模型返回下一问、建议和依据。
