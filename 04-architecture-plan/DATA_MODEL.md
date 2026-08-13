# 数据模型

- 基线：已批准 v2.1
- 状态：Stage 4 已批准；见 `workflow/STAGE_APPROVALS.md` 的 Gate-005 与 Gate-006

## 核心聚合

| 聚合 | 关键字段/关系 | 约束 |
|---|---|---|
| `User`、`Role`、`Permission`、`Session` | 用户、角色、菜单/操作权限、登录会话 | 不包含工厂或设备授权关系。 |
| `Organization`、`Equipment` | 组织树与设备主数据 | `equipment.code` 唯一；有待处理或维修中故障时不得停用设备。 |
| `FaultReport`、`WorkOrder`、`MaintenanceRecord` | 故障—工单—维修闭环 | 业务状态迁移由业务 API 控制；维修人员最终提交字段是业务事实。 |
| `HistoricalRepairCase` | 从已完成维修沉淀的结构化案例 | 仅 PostgreSQL 查询，不写入 RAGFlow 作为案例事实源。 |
| `KnowledgeDataset`、`KnowledgeDocument`、`KnowledgeCitation` | 知识文档业务元数据、RAGFlow 映射与引用 | 只有 `READY` 文档可检索；RAGFlow ID、对象存储文件 ID 和失败原因必须保留。 |
| `ModelProvider`、`ModelBinding`、`AgentConfig` | 模型能力、密钥引用、每 Agent 当前有效配置 | `AgentConfig.agent_id` 唯一；推理开启时绑定模型必须具备 `supports_reasoning=true`。 |
| `AgentThread`、`AgentRun`、`ToolCall`、`AgentConfirmation` | 会话、运行、工具审计、人工确认 | 线程绑定创建者；`AgentRun.config_snapshot` 不可变，只作审计，不作为版本管理。 |
| `HealthScoreSnapshot`、`MetricDefinition`、`MetricQueryResult` | 健康快照、固定指标、查询结果 | 快照追加式；指标目录只读；模型不能生成或写入指标数值。 |
| `FileObject`、`AuditEvent`、`IdempotencyKey`、`JobRun` | 附件、审计、重复写防护、异步任务 | 审计不得保存密钥、令牌、Cookie、原始思维链或敏感附件原文。 |

## Agent 配置与运行模型

```text
AgentConfig(agent_id, enabled, model_binding_id, knowledge_dataset_ids,
            streaming_enabled, suggestions_enabled, sources_enabled,
            context_turns, retrieval_limit, similarity_threshold,
            deep_thinking_enabled, deep_thinking_level, max_reply_tokens,
            updated_at, updated_by)

AgentThread(thread_id, agent_id, creator_user_id, business_context_json,
            checkpoint_ref, status, created_at)

AgentRun(run_id, thread_id, config_snapshot_json, state_json,
         model_binding_id, status, started_at, completed_at, error_code)
```

- 首次初始化只在某个 `agent_id` 没有记录时插入该 Agent 自己的默认值；不使用共享默认对象批量覆盖。
- `config_snapshot_json` 必须包含该轮实际使用的模型、流式、建议、引用、上下文和深度思考参数，支持审计与复现。
- `state_json` 只保存结构化工作状态、已确认字段、工具结果摘要、待补证据与安全状态；不保存模型原始思维链。

## 故障诊断补充关系

```text
FaultReport -> DiagnosisDraft -> AgentThread -> AgentRun
AgentRun -> ToolCall / KnowledgeCitation / AgentConfirmation
MaintenanceRecord -> HistoricalRepairCase
```

`DiagnosisDraft` 是可丢弃的 AI 草稿。只有用户点击“采纳 AI 建议并开始维修”才将允许预填的内容与只读对话摘要关联到维修记录；直接开始维修不保留 AI 摘要。结束维修页面显示的摘要放在“备件更换说明”之后，且包含故障现象、关键故障码/现场证据、验证结果、根因与建议，不包含操作过程流水账或思维链。

## 系统管理后端补齐（2026-08-13）

迁移 `0010_system_management_completion` 为 `User` 增加 `display_name,gender,email,phone,remark,organization_id`。角色字段由前序迁移 `0009_task013_role_management` 提供。内置角色以 `built_in=true` 保护；自定义角色在未绑定用户时可变更或删除。用户不会物理删除，密码重置撤销全部未撤销会话。完整字段和约束见 `04-architecture-plan/SYSTEM_MANAGEMENT_COMPLETION_CONTRACT.md`。

## TASK-002 正式契约

本节冻结 `CR-036` 修复后的身份权限、组织和设备主数据模型。数据库迁移以 Alembic `0002` 为准；运行时不保留旧 `Equipment.enabled` 双事实来源。

### 字段矩阵

| Entity | Fields | 关键约束 |
|---|---|---|
| Organization | id,type,code,name,parent_id,sort_order,enabled,remark,created_at,updated_at | `code` 全局唯一；同一 `parent_id` 下 `name` 唯一；唯一固定根节点。 |
| Equipment | id,code,name,model,type,manufacturer,manufactured_at,commissioned_at,operating_hours,status,organization_id,owner_user_id,image_refs,created_at,updated_at | `code` 全局唯一；`operating_hours >= 0`；组织必须是启用的 `LINE`。 |
| User | id,username,password_hash,enabled,created_at,updated_at | `username` 全局唯一；密码哈希不进入 API 响应或审计。 |
| Role | id,code,name,built_in | 仅允许四个固定角色；角色不可新增、删除或改名。 |
| Permission | id,code | 固定目录；权限本身不提供动态增删 API。 |
| AuditEvent | id,actor_user_id,action,resource_type,resource_id,result,metadata_json,created_at | 成功与失败事件持久化；元数据递归脱敏。 |
| IdempotencyRecord | id,user_id,method,path,idempotency_key,request_hash,response_status,response_body | 每个用户的 Key 唯一；只保存成功响应和原审计 ID。 |

### Organization

`Organization.type` 为 `ROOT,FACTORY,WORKSHOP,LINE`，且只允许 `ROOT -> FACTORY -> WORKSHOP -> LINE`。迁移建立且仅建立一个固定 `ROOT`；根节点 `parent_id=null`，不可停用、删除或修改类型。业务 API 不允许修改任何节点的 `type` 或 `parent_id`。

`code` 全局唯一，同一父节点下 `name` 唯一。停用节点在同一事务内级联停用全部后代；重新启用父节点不会自动启用后代。停用父节点下不得新增或重新启用子节点。存在子节点或设备引用时禁止删除组织。所有组织树写与设备组织引用写在 PostgreSQL 中先获取固定事务级 advisory lock，防止删除/引用竞态。

### Equipment

`Equipment.code` 可编辑且全局唯一。`model,type,manufacturer` 为正式必填主数据；`manufactured_at` 与 `commissioned_at` 可为空；`operating_hours` 精度为 `Numeric(12,2)` 且不小于零；`status` 为 `NORMAL,FAULT,REPAIRING,DISABLED`。`organization_id` 必须引用存在、启用且类型为 `LINE` 的组织；`owner_user_id` 可为空，否则必须引用启用用户。

`image_refs` 为对象数组，每项只含 `object_key,filename`，仅保存对象引用及展示元数据，不含文件正文。TASK-002 不提供设备物理删除接口。旧 `enabled=true/false` 迁移为 `NORMAL/DISABLED` 后删除该列，不增加兼容字段、双写或回退读取。

Alembic `0002` 对旧设备执行确定性收口：`model` 回填为 `LEGACY-{code}`，`type` 与 `manufacturer` 回填为 `LEGACY_UNSPECIFIED`；原组织为空或不是 `LINE` 时，迁移到专用的 `Legacy Equipment Factory -> Workshop -> Line` 兜底层级，且生成名称会确定性避让旧同级名称。完成回填后，`model,type,manufacturer,organization_id` 均改为非空列。上述占位值是可识别的待治理主数据，不是兼容读取分支；设备管理员可通过正式更新 API 替换为真实信息。`0002 -> 0001` 是有损降级：升级前为空或指向非 `LINE` 的旧组织关系不会额外保存，降级后恢复为 `NULL`，执行前必须备份。

### User Role Permission

`User.username` 是稳定登录标识。用户与角色、角色与权限均为多对多关系。用户写接口可完整替换 `enabled` 和角色集合；不得停用自己，也不得停用最后一个有效系统管理员或移除其系统管理员角色。

固定角色恰为 `SYSTEM_ADMIN,EQUIPMENT_ADMIN,REPAIR_WORKER,LINE_OPERATOR`。`SYSTEM_ADMIN` 始终拥有固定权限目录中的全部权限且不可削弱；另外三个角色可在固定目录内更新权限集合。角色不能通过 API 新增、删除或改名，权限实体也不能通过 API 动态增删。

权限目录分为 API 权限 `identity:read,identity:write,equipment:read,equipment:write,organization:read,organization:write` 与已批准的菜单/操作权限；授权不包含工厂、组织或设备行级关系。用户启停、用户角色和角色权限变更均产生审计。

### AuditEvent 与 IdempotencyRecord

受保护写成功时，业务变更、`AuditEvent(result=success)`、`IdempotencyRecord` 在同一主事务提交，响应体保存真实 `audit_event_id`。失败时先回滚主事务，再由独立事务写恰好一条 `AuditEvent(result=failure)`；失败响应不写入 `IdempotencyRecord`。审计元数据递归脱敏密码、Token、Authorization、Cookie、密钥以及附件或文件上下文内的正文、字节和 Base64 内容，同时允许保留文件名、类型、大小和对象引用。

`IdempotencyRecord` 保存 `user_id,method,path,idempotency_key,request_hash,response_status,response_body`。`idempotency_key` 在同一用户范围内全局唯一；相同 Key 只有在方法、路径和请求摘要全部一致时才重放已保存成功响应，任一项不一致均拒绝并产生失败审计。

### 延后边界与产品侧修正

TASK-003 负责建立故障、工单和维修事实，并已据此实现活跃故障设备停用保护。附件上传、MinIO/S3、扫描、下载和生命周期不属于 TASK-002；当前只保存图片引用元数据。

Stage 3 原型中的动态自定义角色控件与 FR-010 及 CR-036 的固定四角色模型冲突，必须在 TASK-010 前完成产品侧修正。本次修复不修改原型、PRD、SPEC 或验收标准。

## TASK-003 正式契约

TASK-003 迁移候选为 `0003_task003`，开发基线 `down_revision=0002`。正式送审前必须按最新集成分支线性化；当前候选的 downgrade 会删除以下五张 TASK-003 表，但保留 TASK-002 表。

| Entity | 核心字段 | 唯一、检查与外键约束 |
|---|---|---|
| `FaultReport` | `number,equipment_id,organization_snapshot,urgency,symptom,occurred_at,possible_location,description,attachment_refs,status,submitter_id,submitted_at,updated_at` | `number` 唯一；状态仅 `PENDING_ACCEPT,IN_REPAIR,PROCESSED`；引用设备和提交人；按设备与状态索引。 |
| `DiagnosisDraft` | `fault_report_id,status,allowed_prefill,read_only_summary,adopted_at,created_at,updated_at` | 状态仅 `DRAFT,DIAGNOSIS_READY`；引用故障；一次采纳由事务与行锁保护。 |
| `WorkOrder` | `number,fault_report_id,equipment_id,status,repairer_user_id,started_at,pending_inspection_at,completed_at,created_at,updated_at` | `number` 和 `fault_report_id` 分别唯一；状态仅 `DRAFT,PENDING_ACCEPT,IN_REPAIR,PENDING_INSPECTION,COMPLETED`；引用故障、设备和维修人。 |
| `MaintenanceRecord` | `work_order_id,start_mode,diagnosis_draft_id,diagnosis_prefill,ai_summary,actual_cause,actual_solution,repair_result,parts_replacement_notes,created_at,updated_at` | `work_order_id` 唯一；非空 `diagnosis_draft_id` 唯一；开始模式仅 `DIRECT,ADOPTED`；引用工单和诊断草稿。 |
| `HistoricalRepairCase` | `source_work_order_id,source_fault_report_id,equipment_id,equipment_type,equipment_model,symptom,actual_cause,actual_solution,repair_result,completed_at,created_at` | `source_work_order_id` 唯一；引用工单、故障和设备；按故障与设备索引。 |

### 状态机与业务事实

故障上报以设备行锁读取正式设备：停用设备拒绝上报；正常设备变为 `FAULT`。开始维修锁定故障并只接受 `PENDING_ACCEPT`，创建唯一工单和唯一维修记录，故障变为 `IN_REPAIR`、设备变为 `REPAIRING`。结束维修锁定工单、故障、设备和维修记录，保存人工最终字段，生成唯一结构化案例，将工单收口为 `COMPLETED`、故障收口为 `PROCESSED`；若同设备仍有其他活跃故障则设备为 `FAULT`，否则为 `NORMAL`。

设备停用与故障创建都先锁定同一设备行。目标状态不是 `DISABLED` 时不增加活跃故障限制；目标为 `DISABLED` 时，只要存在 `PENDING_ACCEPT` 或 `IN_REPAIR` 故障就拒绝，从而禁止形成“停用设备仍新增活跃故障”的竞争终态。

### 人工最终字段与诊断边界

`actual_cause,actual_solution,repair_result` 是维修结束必填的人工业务事实，`parts_replacement_notes` 可空。采纳诊断仅允许预填 `fault_type,actual_cause,actual_solution,parts_replacement_notes`，只读摘要仅允许 `symptom,key_evidence,verification_results,root_cause,recommendations`；未知字段、密钥、Token、附件正文和思维链不得进入维修记录。人工结束提交覆盖任何预填值。

`HistoricalRepairCase` 是 PostgreSQL 结构化事实源。相似案例只使用类型、型号、症状和完成时间确定性排序，不写入或调用 RAGFlow，不增加向量、embedding、引用或外部网络依赖。
