# API 规格

- 基线：已批准 v2.1
- 状态：Stage 4 已批准；见 `workflow/STAGE_APPROVALS.md` 的 Gate-005 与 Gate-006

所有写请求要求平台账号认证；可重复写请求需携带 `Idempotency-Key`；响应包含字段级校验错误和 `audit_event_id`。权限仅校验角色、菜单和操作权限，不按工厂或设备进行数据行过滤。根据 CR-043，Agent 的授权详情保护不引入 `EquipmentGrant`；其边界为认证、路由权限、线程/诊断草稿创建者隔离、服务端业务事实绑定、非法对象不泄露详情和审计。

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

## 业务与知识工具 API

| Method | Endpoint | 用途 |
|---|---|---|
| POST | `/api/fault-reports` | 人工正式上报。 |
| POST | `/api/fault-reports/{id}/diagnosis-drafts` | 后台预诊断草稿任务。 |
| POST | `/api/fault-reports/{id}/start-repair` | 直接开始或采纳已确认诊断后开始维修。 |
| POST | `/api/work-orders/{id}/repair-result` | 提交维修人员最终处理结果。 |
| GET | `/api/repair-cases/similar` | 结构化同类设备相似案例查询。 |
| POST | `/api/agent/operation-guidance` | 操作指引，使用页面传入的设备/故障上下文进行受控知识检索；要求 `intelligence:agent`，不读取或判断设备行级授权。 |
| POST | `/api/agent/fault-diagnosis` | 维修前故障诊断；要求 `intelligence:agent` 与 `fault:repair`，`start` 只接受 `fault_report_id` 与报警码状态，诊断上下文由服务端 `FaultReport`、`Equipment` 和 `fault_diagnosis` Agent 配置生成。 |
| GET | `/api/metrics/catalog` | 固定指标目录。 |
| POST | `/api/metrics/query-batch` | 一次正式查询最多五个已校验指标。 |
| POST | `/api/knowledge/documents` | 上传并创建知识文档元数据。 |
| GET | `/api/knowledge/documents/{id}` | 查询 RAGFlow 生命周期状态。 |

## CR-044 附件上传与扫描契约

| Method | Endpoint | 权限码 | 请求/成功响应 |
|---|---|---|---|
| POST | `/api/attachments` | `fault:create` | `multipart/form-data` 中唯一 `file` 字段；必填 `Idempotency-Key`；201 返回 `object_key,filename,size_bytes,content_type`。 |

服务端按顺序读取文件、使用文件 SHA-256 与文件名、MIME、大小形成幂等请求摘要并回放同 Key 原响应；同 Key 不同摘要返回既有 `IDEMPOTENCY_KEY_REUSED` 409。随后校验文件存在、非空、最大 `104857600` 字节和明确允许的 MIME：`image/jpeg`、`image/png`、`image/webp`、`application/pdf`、`text/plain`、`text/csv`、`application/msword`、`application/vnd.openxmlformats-officedocument.wordprocessingml.document`、`application/vnd.ms-excel`、`application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`。`.zip` 等压缩包、宏格式和其他类型一律拒绝；再使用 ClamAV 扫描，最后写入 MinIO。若成功审计、幂等记录或数据库提交失败，服务端回滚数据库并删除刚写入对象。客户端不得指定 `object_key`，服务端以随机 UUID 生成键。成功响应可作为既有 `FaultReportCreate.attachment_refs` 项直接使用；故障上报 API 的字段、幂等和状态机不变。

| HTTP | code | 场景 |
|---|---|---|
| 422 | `ATTACHMENT_INVALID` | 缺失、空文件、大小或 MIME 不合法。 |
| 422 | `ATTACHMENT_INFECTED` | 病毒扫描明确判定感染。 |
| 503 | `ATTACHMENT_SCAN_UNAVAILABLE` | 扫描超时或扫描服务不可用。 |
| 503 | `ATTACHMENT_STORAGE_UNAVAILABLE` | 扫描成功后的对象存储写入失败。 |

失败不返回 `AttachmentRef`；临时文件必须清理。审计仅保存动作、结果、文件名、类型、大小与对象键，不保存正文、字节、Base64、密码、Token、Cookie 或连接串。

内部工具不直接暴露给浏览器：`retrieve_knowledge`、`get_similar_repair_cases`、`query_metric_batch`、`get_page_capability`、`get_operation_guidance`、`run_fault_diagnosis`、`create_fault_draft`、`submit_confirmed_business_action` 均经服务端参数模型、权限校验、超时和审计封装。禁止 Agent 生成 SQL 或任意文件系统命令。

## 诊断状态与错误契约

诊断运行状态：`QUEUED`、`OPEN_LOADING`、`QUESTIONING`、`EVIDENCE_PENDING`、`DIAGNOSIS_READY`、`ADOPTED`、`DIRECT_START`、`UNAVAILABLE`。仅 `DIAGNOSIS_READY` 可以返回“采纳 AI 建议并开始维修”。

`POST /api/agent/fault-diagnosis` 的客户端状态不是事实源。服务端以 `DiagnosisDraft` 保存诊断会话、创建者、故障绑定、知识数据集和证据进度；客户端后续步骤只提交 `diagnosis_draft_id`、回答或证据字段。READY 后重复提交必须幂等返回既有结果，不重复创建草稿或成功审计。缺少 `fault:repair`、草稿不存在、草稿不属于当前用户、故障/设备不存在或客户端提交服务端拥有的诊断上下文字段时，接口必须拒绝且不返回受保护业务详情。

| 错误码 | 场景 | 前台行为 |
|---|---|---|
| `AGENT_DISABLED` | Agent 未启用 | 提示 AI 暂不可用，保留人工流程。 |
| `AGENT_CONFIG_INVALID` | 模型/知识库/推理配置不完整 | 提示配置不可用，保留人工流程。 |
| `MODEL_REASONING_UNSUPPORTED` | 非推理模型开启深度思考 | 拒绝保存并要求改绑模型或关闭开关。 |
| `RAGFLOW_TIMEOUT`、`LLM_TIMEOUT` | 外部依赖超时 | 不伪造结果；诊断降级为不可用或继续人工。 |
| `EVIDENCE_INSUFFICIENT` | 证据未满足根因门槛 | 继续追问、上传附件或直接开始维修。 |

## TASK-002 正式契约

本节是 `CR-036` 修复后身份权限、组织和设备主数据 API 的唯一正式契约。所有接口均要求平台 Bearer 会话认证；权限只控制角色、菜单与操作，不增加工厂、组织或设备的行级过滤。动态角色创建接口 `POST /api/roles` 已移除。

### 路由矩阵

| Method | Endpoint | 权限码 | Idempotency-Key | 请求与成功响应 |
|---|---|---|---|---|
| GET | `/api/permissions` | `identity:read` | 不使用 | 返回 `[{code}]` 的固定权限目录。 |
| GET | `/api/roles` | `identity:read` | 不使用 | 返回四个固定角色的 `id,code,name,permission_codes`。 |
| PATCH | `/api/roles/{role_id}/permissions` | `identity:write` | 必填 | 请求 `permission_codes`；返回角色字段及 `audit_event_id`。 |
| GET | `/api/users` | `authenticated:self-or-user_management.view_all` | 不使用 | 有 `user_management.view_all` 时返回全量用户，否则仅返回本人 `id,username,enabled,role_ids`。 |
| GET | `/api/users/{user_id}` | `authenticated:self-or-user_management.view_all` | 不使用 | 返回本人；有 `user_management.view_all` 时可返回其他用户的 `id,username,enabled,role_ids`。 |
| POST | `/api/users` | `identity:write` | 必填 | 请求 `username,password,role_ids`；201 返回用户字段及 `audit_event_id`，不返回密码。 |
| PATCH | `/api/users/{user_id}` | `identity:write` | 必填 | 请求完整 `enabled,role_ids`；返回用户字段及 `audit_event_id`。 |
| GET | `/api/organizations` | `organization:read` | 不使用 | 返回完整组织节点字段列表，调用方按 `parent_id` 构树。 |
| POST | `/api/organizations` | `organization:write` | 必填 | 请求组织创建字段；201 返回组织字段及 `audit_event_id`。 |
| PATCH | `/api/organizations/{organization_id}` | `organization:write` | 必填 | 请求完整可变字段；返回组织字段及 `audit_event_id`。 |
| DELETE | `/api/organizations/{organization_id}` | `organization:write` | 不使用 | 物理删除无引用的非根叶节点；返回被删除组织字段及 `audit_event_id`。 |
| GET | `/api/equipment` | `equipment:read` | 不使用 | 返回完整设备字段列表。 |
| GET | `/api/equipment/{equipment_id}` | `equipment:read` | 不使用 | 返回完整设备字段。 |
| POST | `/api/equipment` | `equipment:write` | 必填 | 请求完整设备写字段；201 返回设备字段及 `audit_event_id`。 |
| PATCH | `/api/equipment/{equipment_id}` | `equipment:write` | 必填 | 请求完整设备写字段；返回设备字段及 `audit_event_id`。 |

### 写请求字段矩阵

| Method | Endpoint | 必填字段 | 可选字段 |
|---|---|---|---|
| POST | `/api/users` | `username`,`password`,`role_ids` | 无 |
| PATCH | `/api/users/{user_id}` | `enabled`,`role_ids` | 无 |
| PATCH | `/api/roles/{role_id}/permissions` | `permission_codes` | 无 |
| POST | `/api/organizations` | `type`,`code`,`name`,`parent_id`,`sort_order` | `enabled`,`remark` |
| PATCH | `/api/organizations/{organization_id}` | `code`,`name`,`sort_order`,`enabled` | `remark` |
| POST | `/api/equipment` | `code`,`name`,`model`,`type`,`manufacturer`,`operating_hours`,`status`,`organization_id` | `manufactured_at`,`commissioned_at`,`owner_user_id`,`image_refs` |
| PATCH | `/api/equipment/{equipment_id}` | `code`,`name`,`model`,`type`,`manufacturer`,`operating_hours`,`status`,`organization_id` | `manufactured_at`,`commissioned_at`,`owner_user_id`,`image_refs` |

### 成功响应字段矩阵

| Method | Endpoint | 字段 |
|---|---|---|
| GET | `/api/permissions` | `code` |
| GET | `/api/roles` | `id`,`code`,`name`,`permission_codes` |
| PATCH | `/api/roles/{role_id}/permissions` | `id`,`code`,`name`,`permission_codes`,`audit_event_id` |
| GET | `/api/users` | `id`,`username`,`enabled`,`role_ids` |
| GET | `/api/users/{user_id}` | `id`,`username`,`enabled`,`role_ids` |
| POST | `/api/users` | `id`,`username`,`enabled`,`role_ids`,`audit_event_id` |
| PATCH | `/api/users/{user_id}` | `id`,`username`,`enabled`,`role_ids`,`audit_event_id` |
| GET | `/api/organizations` | `id`,`type`,`code`,`name`,`parent_id`,`sort_order`,`enabled`,`remark` |
| POST | `/api/organizations` | `id`,`type`,`code`,`name`,`parent_id`,`sort_order`,`enabled`,`remark`,`audit_event_id` |
| PATCH | `/api/organizations/{organization_id}` | `id`,`type`,`code`,`name`,`parent_id`,`sort_order`,`enabled`,`remark`,`audit_event_id` |
| DELETE | `/api/organizations/{organization_id}` | `id`,`type`,`code`,`name`,`parent_id`,`sort_order`,`enabled`,`remark`,`audit_event_id` |
| GET | `/api/equipment` | `id`,`code`,`name`,`model`,`type`,`manufacturer`,`manufactured_at`,`commissioned_at`,`operating_hours`,`status`,`organization_id`,`owner_user_id`,`image_refs`,`created_at`,`updated_at` |
| GET | `/api/equipment/{equipment_id}` | `id`,`code`,`name`,`model`,`type`,`manufacturer`,`manufactured_at`,`commissioned_at`,`operating_hours`,`status`,`organization_id`,`owner_user_id`,`image_refs`,`created_at`,`updated_at` |
| POST | `/api/equipment` | `id`,`code`,`name`,`model`,`type`,`manufacturer`,`manufactured_at`,`commissioned_at`,`operating_hours`,`status`,`organization_id`,`owner_user_id`,`image_refs`,`created_at`,`updated_at`,`audit_event_id` |
| PATCH | `/api/equipment/{equipment_id}` | `id`,`code`,`name`,`model`,`type`,`manufacturer`,`manufactured_at`,`commissioned_at`,`operating_hours`,`status`,`organization_id`,`owner_user_id`,`image_refs`,`created_at`,`updated_at`,`audit_event_id` |

### 默认值、可空性与约束矩阵

| Model | Field | 可空 | 默认值 | 约束 |
|---|---|---|---|---|
| UserCreate | `username` | 否 | 无 | `minLength=1;maxLength=100` |
| UserCreate | `password` | 否 | 无 | `minLength=8;maxLength=200` |
| UserCreate | `role_ids` | 否 | 无 | `minItems=1` |
| OrganizationCreate | `code` | 否 | 无 | `minLength=1;maxLength=100` |
| OrganizationCreate | `name` | 否 | 无 | `minLength=1;maxLength=200` |
| OrganizationCreate | `sort_order` | 否 | 无 | `minimum=0` |
| OrganizationCreate | `enabled` | 否 | `true` | `boolean` |
| OrganizationCreate | `remark` | 否 | `""` | `maxLength=1000` |
| OrganizationUpdate | `code` | 否 | 无 | `minLength=1;maxLength=100` |
| OrganizationUpdate | `name` | 否 | 无 | `minLength=1;maxLength=200` |
| OrganizationUpdate | `sort_order` | 否 | 无 | `minimum=0` |
| OrganizationUpdate | `remark` | 否 | `""` | `maxLength=1000` |
| EquipmentWrite | `code` | 否 | 无 | `minLength=1;maxLength=100` |
| EquipmentWrite | `name` | 否 | 无 | `minLength=1;maxLength=200` |
| EquipmentWrite | `model` | 否 | 无 | `minLength=1;maxLength=200` |
| EquipmentWrite | `type` | 否 | 无 | `minLength=1;maxLength=100` |
| EquipmentWrite | `manufacturer` | 否 | 无 | `minLength=1;maxLength=200` |
| EquipmentWrite | `manufactured_at` | 是 | `null` | `format=date` |
| EquipmentWrite | `commissioned_at` | 是 | `null` | `format=date` |
| EquipmentWrite | `operating_hours` | 否 | 无 | `minimum=0;maxDigits=12;decimalPlaces=2` |
| EquipmentWrite | `owner_user_id` | 是 | `null` | `string` |
| EquipmentWrite | `image_refs` | 否 | `[]` | `items=ImageRef` |
| ImageRef | `object_key` | 否 | 无 | `minLength=1;maxLength=500` |
| ImageRef | `filename` | 否 | 无 | `minLength=1;maxLength=255` |

### 请求与响应字段

写请求均拒绝未声明字段。`role_ids` 至少包含一个固定角色 ID；`permission_codes` 只能取固定权限目录。用户创建的 `password` 长度为 8–200，只用于生成密码哈希，不得出现在查询、响应或审计元数据中。用户更新不修改 `username` 或密码，只完整替换 `enabled` 和 `role_ids`。

组织创建请求为 `type,code,name,parent_id,sort_order,enabled,remark`；组织更新请求为 `code,name,sort_order,enabled,remark`，不允许修改 `type` 或 `parent_id`。组织响应为 `id,type,code,name,parent_id,sort_order,enabled,remark`；`type` 只能是 `ROOT,FACTORY,WORKSHOP,LINE`。

设备创建和更新均使用完整写模型：`code,name,model,type,manufacturer,manufactured_at,commissioned_at,operating_hours,status,organization_id,owner_user_id,image_refs`。其中 `model,type,manufacturer` 为非空字符串，两个日期可为 `null`，`operating_hours >= 0`，`status` 只能是 `NORMAL,FAULT,REPAIRING,DISABLED`，`owner_user_id` 可为 `null`。每个 `image_refs` 元素严格为 `object_key,filename`，仅保存对象引用与展示元数据，不接收文件正文。设备响应额外包含 `id,created_at,updated_at`；写成功再包含 `audit_event_id`。

### 固定权限目录

API 权限码固定为 `identity:read,identity:write,equipment:read,equipment:write,organization:read,organization:write`。菜单与操作权限码固定为 `workbench:view,workbench:export,bi:view,bi:export,factory:view,factory:manage,equipment:view,equipment:create,equipment:edit,equipment:delete,fault:view,fault:create,fault:repair,fault:close,maintenance:view,maintenance:detail,maintenance:export,system:role,system:user,user_management.view_all,system:org,system:audit,intelligence:view,intelligence:model,intelligence:agent,intelligence:knowledge,intelligence:audit`。权限实体不提供动态增删 API。

### 错误响应

受保护写操作失败统一返回 `code`、`message`、`fields`、`audit_event_id` 四个 `detail` 字段。`fields` 是字段到稳定原因的对象；没有字段级原因时为空对象。主业务事务先回滚，再由独立事务写一条脱敏失败审计；只有审计提交成功才返回真实 `audit_event_id`。查询失败仍使用相同的 `detail.code,message,fields` 形状，但不承诺失败审计 ID。不得向客户端暴露 SQL、堆栈、密码、令牌、Cookie 或附件正文。

### 错误矩阵

| HTTP | code | 适用场景与 fields |
|---|---|---|
| 422 | `VALIDATION_ERROR` | 请求字段缺失、类型、长度、枚举、额外字段或头字段校验失败；`fields` 标识各字段。 |
| 403 | `PERMISSION_DENIED` | 缺少路由要求的权限码。 |
| 404 | `RESOURCE_NOT_FOUND` | 查询类通用资源不存在。 |
| 409 | `IDEMPOTENCY_KEY_REUSED` | 同一用户、方法、路径和 Key 携带不同请求体；`fields.idempotency_key=conflict`。 |
| 500 | `INTERNAL_SERVER_ERROR` | 未预期的业务或数据库错误；受保护写操作在主事务回滚后以独立事务记录失败审计并返回真实 `audit_event_id`。 |
| 503 | `AUDIT_PERSIST_FAILED` | 失败审计无法持久化；不伪造 `audit_event_id`。 |
| 404 | `USER_NOT_FOUND` | 用户不存在。 |
| 422 | `ROLE_NOT_FOUND` | 用户写请求含未知或非固定角色 ID。 |
| 409 | `USERNAME_EXISTS` | 用户名重复；`fields.username=duplicate`。 |
| 409 | `USER_SELF_DISABLE_FORBIDDEN` | 操作者尝试停用自己。 |
| 409 | `LAST_SYSTEM_ADMIN_REQUIRED` | 停用或移除角色会失去最后一个有效系统管理员。 |
| 404 | `ROLE_NOT_FOUND` | 目标角色不存在。 |
| 422 | `PERMISSION_NOT_FOUND` | `permission_codes` 含目录外代码。 |
| 409 | `SYSTEM_ADMIN_PERMISSIONS_FIXED` | 尝试削弱系统管理员权限。 |
| 404 | `ORGANIZATION_NOT_FOUND` | 目标组织不存在。 |
| 404 | `ORGANIZATION_PARENT_NOT_FOUND` | 父组织不存在。 |
| 422 | `ORGANIZATION_LEVEL_INVALID` | 组织层级不是 `ROOT -> FACTORY -> WORKSHOP -> LINE`。 |
| 422 | `ORGANIZATION_TREE_INVALID` | 检测到组织环或非法树数据。 |
| 409 | `ORGANIZATION_CODE_EXISTS` | `code` 全局重复；`fields.code=duplicate`。 |
| 409 | `ORGANIZATION_SIBLING_NAME_EXISTS` | 同父节点名称重复；`fields.name=duplicate`。 |
| 409 | `ORGANIZATION_PARENT_DISABLED` | 在停用父节点下创建或重新启用子节点。 |
| 409 | `ORGANIZATION_ROOT_PROTECTED` | 尝试停用、更新或删除固定根节点。 |
| 409 | `ORGANIZATION_HAS_CHILDREN` | 删除仍有子节点的组织。 |
| 409 | `ORGANIZATION_HAS_EQUIPMENT` | 删除仍被设备引用的组织。 |
| 409 | `ORGANIZATION_CONFLICT` | 数据库约束竞争导致的其他组织写冲突。 |
| 404 | `EQUIPMENT_NOT_FOUND` | 设备不存在。 |
| 409 | `EQUIPMENT_CODE_EXISTS` | 设备 `code` 全局重复；`fields.code=duplicate`。 |
| 404 | `EQUIPMENT_ORGANIZATION_NOT_FOUND` | 所属组织不存在。 |
| 409 | `EQUIPMENT_ORGANIZATION_NOT_LINE` | 所属组织不是 `LINE`。 |
| 409 | `EQUIPMENT_ORGANIZATION_DISABLED` | 所属产线已停用。 |
| 404 | `EQUIPMENT_OWNER_NOT_FOUND` | 负责人用户不存在。 |
| 409 | `EQUIPMENT_OWNER_DISABLED` | 负责人用户已停用。 |
| 409 | `EQUIPMENT_CONFLICT` | 数据库约束竞争导致的其他设备写冲突。 |

### 幂等与审计

要求 `Idempotency-Key` 的写接口在同一用户范围内保持 Key 全局唯一。首次成功在同一事务内保存业务变更、成功审计和响应；相同 Key 的 HTTP 方法、实际路径和规范化请求体均一致时，成功响应连同原 `audit_event_id` 原样重放，不产生第二条成功审计。方法、路径或请求体任一不一致均视为 Key 冲突，返回 `409 IDEMPOTENCY_KEY_REUSED` 并写入一条失败审计。失败响应一律不缓存，调用方修正请求后应使用新 Key。组织删除不缓存幂等响应，但仍写成功或失败审计。

成功审计动作固定为 `role.permissions.update,user.create,user.update,organization.create,organization.update,organization.delete,equipment.create,equipment.update`。失败审计记录对应动作、操作者、资源、`failure`、业务错误码和递归脱敏后的请求摘要；权限依赖已经产生拒绝审计时复用其事件，避免重复。

### 延后边界与产品侧修正

TASK-002 不根据当时尚不存在的业务事实推测状态；TASK-003 负责建立故障、工单和维修事实，并已据此实现活跃故障设备停用保护。TASK-002 不提供设备物理删除接口，也不实现附件上传、对象存储、扫描、下载和生命周期。

Stage 3 原型中的动态自定义角色控件与 FR-010 及 CR-036 的固定四角色规则冲突，必须在 TASK-010 前由产品侧修正。本次后端修复不修改原型、PRD、SPEC 或验收标准。

## TASK-003 正式契约

本节冻结故障上报、开始维修、维修结束和结构化案例查询契约。附件字段只接受对象引用及元数据；TASK-003 不上传、解析或下载文件，不调用 RAGFlow、Agent 或向量服务。

### 路由与权限

| Method | Endpoint | 权限 | Idempotency-Key | 请求与成功响应 |
|---|---|---|---|---|
| POST | `/api/fault-reports` | `fault:create` | 必填 | 请求 `equipment_id,urgency,symptom,occurred_at`，可选 `possible_location,description,attachment_refs`；201 返回故障字段及 `audit_event_id`。 |
| POST | `/api/fault-reports/{fault_id}/start-repair` | `fault:repair` | 必填 | 请求 `mode=DIRECT` 或 `mode=ADOPTED,diagnosis_draft_id`；200 返回故障、工单、维修记录和开始模式字段及 `audit_event_id`。 |
| POST | `/api/work-orders/{work_order_id}/repair-result` | `fault:close` | 必填 | 请求人工最终字段 `actual_cause,actual_solution,repair_result`，可选 `parts_replacement_notes`；200 返回完成状态、结构化案例 ID 及 `audit_event_id`。 |
| GET | `/api/repair-cases/similar` | `maintenance:view` | 不使用 | 查询至少包含 `equipment_type,equipment_model,symptom` 之一，`limit` 为 1–100、默认 20；200 返回 `items,count`。 |

`attachment_refs` 每项严格包含 `object_key,filename,size_bytes,content_type`，不接受正文、Base64 或任意额外字段。`occurred_at` 必须携带时区且不得晚于当前时间。`DIRECT` 禁止携带诊断草稿；`ADOPTED` 必须引用同一故障、状态为 `DIAGNOSIS_READY` 且从未被采纳的草稿。采纳只复制批准字段中类型正确的字符串或字符串列表，并丢弃未知字段与非预期嵌套值；直接开始不保存 AI 摘要。维修结束始终以维修人员本次提交的最终字段覆盖草稿预填值。

### 状态、幂等、审计与并发

故障只允许 `PENDING_ACCEPT -> IN_REPAIR -> PROCESSED`，工单在本契约中由开始维修建立为 `IN_REPAIR`，结束维修经 `PENDING_INSPECTION` 同事务收口为 `COMPLETED`。新 Key 对已迁移状态重复操作返回 409；同一 Key、方法、路径和请求体重放原成功响应，不重复创建故障、工单、维修记录、案例或成功审计。

三个写接口的业务变更、成功审计与幂等记录同事务提交；任一步失败则业务事务回滚，再由独立事务写脱敏失败审计。成功审计动作分别为 `fault_report.create,repair.start,repair.complete`。PostgreSQL 使用设备、故障、工单及诊断草稿行锁协调竞争；设备更新为 `DISABLED` 时也锁定同一设备行。存在 `PENDING_ACCEPT` 或 `IN_REPAIR` 故障时返回 `409 EQUIPMENT_ACTIVE_FAULT` 和 `fields.status=active_fault`，不改变设备。

### 稳定业务错误

| HTTP | code | 场景 |
|---|---|---|
| 404 | `FAULT_EQUIPMENT_NOT_FOUND`, `FAULT_REPORT_NOT_FOUND`, `WORK_ORDER_NOT_FOUND`, `DIAGNOSIS_DRAFT_NOT_FOUND` | 对应资源不存在。 |
| 409 | `FAULT_EQUIPMENT_DISABLED` | 停用设备不可新建故障。 |
| 422 | `FAULT_OCCURRENCE_IN_FUTURE` | 故障发生时间在未来；`fields.occurred_at=future`。 |
| 409 | `FAULT_STATE_CONFLICT`, `WORK_ORDER_STATE_CONFLICT` | 当前状态不允许迁移；`fields.status` 返回当前状态。 |
| 409 | `DIAGNOSIS_DRAFT_FAULT_MISMATCH`, `DIAGNOSIS_DRAFT_NOT_READY`, `DIAGNOSIS_DRAFT_ALREADY_ADOPTED` | 草稿不属于该故障、未就绪或已采纳。 |
| 409 | `EQUIPMENT_ACTIVE_FAULT` | 活跃故障存在时禁止停用；`fields.status=active_fault`。 |

相似案例查询只访问 PostgreSQL `historical_repair_cases`：类型与型号精确匹配优先，其次为单字段或症状字面文本匹配，同优先级按完成时间倒序；查询中的 `%`、`_` 不具备通配符含义。空结果返回 `items=[]`；不产生成功审计，不进行网络请求，也不返回知识库引用。
