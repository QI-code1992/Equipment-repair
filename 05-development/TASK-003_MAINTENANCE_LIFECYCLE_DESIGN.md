# TASK-003 故障、工单、维修与结构化案例闭环设计

## 1. 文档状态

- 任务：`TASK-003` — 故障、工单、维修与结构化案例闭环
- 状态：已由项目负责人确认范围，进入书面设计复核检查点
- 设计确认日期：2026-07-20
- 任务开发者：`DEV-001`
- 指定审核者：`DEV-002`
- 输入基线：`codex/stage-05-integration@b29c69d13c3d1c81f01023152eabf0c0f2d02741`
- 任务分支：`codex/task-003-maintenance-lifecycle`
- PR 目标分支：`codex/stage-05-integration`
- 需求映射：FR-003、FR-008、FR-RA-003；AC-010、AC-014、AC-026—028、AC-030、AC-043

## 2. 目标与边界

本任务建立 PostgreSQL 中故障、工单、维修和历史案例的唯一业务事实闭环，并向后续诊断 Agent 提供已认证、可审计、可幂等调用的业务契约。

包含：

- 人工故障上报及待接单状态；
- 直接开始维修和采纳已确认诊断后开始维修的业务入口；
- 工单与维修记录的合法状态迁移；
- 维修人员最终字段校验、维修完成和结构化案例沉淀；
- PostgreSQL 结构化相似案例查询；
- 活跃故障对设备停用操作的保护；
- 写操作权限、幂等、成功/失败审计和事务回滚。

不包含：

- RAGFlow 文档上传、检索、引用或知识生命周期；
- 诊断 Agent、LLM、LangGraph、动态追问或诊断草稿生成逻辑；
- 前端页面、SSE、健康评分和通知；
- 二进制附件上传、扫描、下载或对象存储生命周期；
- TASK-004、TASK-005、TASK-006 或 TASK-008 的代码和治理台账。

故障附件只接收已存在对象的引用元数据，不接收二进制正文。诊断采纳入口只消费服务端已经确认的诊断草稿，不在本任务中生成或推断诊断内容。

## 3. 聚合与数据模型

### 3.1 FaultReport

`FaultReport` 保存正式故障事实：编号、设备、上报组织快照、紧急程度、故障现象、发生时间、可能位置、说明、附件引用、状态、上报人和时间戳。

- 状态固定为 `PENDING_ACCEPT`、`IN_REPAIR`、`PROCESSED`。
- 设备、紧急程度和故障现象必填，发生时间不得晚于服务端当前时间。
- 组织信息由设备所属产线向上解析并保存只读快照，客户端不得覆盖。
- 附件元素只允许 `object_key`、`filename`、`size_bytes`、`content_type`；单个引用声明的大小不得超过 100 MB。

### 3.2 WorkOrder

`WorkOrder` 关联一个故障单和一台设备，保存工单编号、状态、维修人员、开始/待验收/完成时间及创建时间。

- 状态固定为 `DRAFT`、`PENDING_ACCEPT`、`IN_REPAIR`、`PENDING_INSPECTION`、`COMPLETED`。
- TASK-003 的人工直接开始或采纳开始会创建或复用该故障唯一的未关闭工单，并进入 `IN_REPAIR`。
- `DRAFT` 与 `PENDING_ACCEPT` 为后续草稿/派发契约保留的正式状态；TASK-003 不实现 Agent 草稿生成逻辑。
- 同一故障最多存在一个未关闭工单，数据库约束和事务锁共同防止并发重复创建。

### 3.3 MaintenanceRecord

`MaintenanceRecord` 与工单一对一，保存开始方式、允许的诊断预填、只读 AI 摘要、维修人员最终提交字段、备件说明及时间戳。

- 开始方式固定为 `DIRECT` 或 `ADOPTED`。
- `DIRECT` 必须把诊断草稿引用、预填和 AI 摘要保存为 `null`。
- `ADOPTED` 只能使用状态为 `DIAGNOSIS_READY` 且属于同一故障的服务端诊断草稿。
- `actual_cause`、`actual_solution`、`repair_result` 只能由维修结果接口最终提交；它们覆盖任何可编辑预填，构成最终业务事实。
- 只读摘要只保存允许字段，不保存原始思维链、Token、Cookie、密钥或附件正文。

### 3.4 DiagnosisDraft 边界记录

`DiagnosisDraft` 是 TASK-008 后续写入的可丢弃诊断草稿契约。本任务只提供最小持久化边界和采纳校验：故障引用、状态、允许预填、只读摘要和时间戳，不实现生成、追问、工具调用或状态机推进。

只有 `DIAGNOSIS_READY` 草稿可以被一次性采纳。直接开始维修不读取、不复制且不保留草稿内容。

### 3.5 HistoricalRepairCase

工单完成时，在同一事务中从最终维修事实生成一条 `HistoricalRepairCase`。案例保存设备型号/类型、故障现象、实际原因、实际方案、维修结果、工单和故障来源 ID 及完成时间。

- 一个完成工单只生成一个案例，使用唯一来源约束防止重复沉淀。
- 案例只存 PostgreSQL，不写入 RAGFlow。
- 相似查询只根据结构化字段进行确定性过滤和排序，不使用模型生成相似度。

## 4. 状态与事务规则

### 4.1 故障闭环

```text
创建正式故障 -> PENDING_ACCEPT
PENDING_ACCEPT --直接开始或采纳开始--> IN_REPAIR
IN_REPAIR --提交完整维修结果--> PROCESSED
```

不允许跳过、反向或重复产生副作用的迁移。相同幂等请求重放原响应；使用新幂等键重复执行已经完成的状态迁移，返回稳定冲突错误，不新增业务记录。

### 4.2 工单闭环

```text
DRAFT -> PENDING_ACCEPT -> IN_REPAIR -> PENDING_INSPECTION -> COMPLETED
                         \-------------------------------> COMPLETED
```

TASK-003 对外共享的开始维修入口最终进入 `IN_REPAIR`。维修结果接口要求完整人工字段，并在同一事务内完成 `IN_REPAIR -> PENDING_INSPECTION -> COMPLETED`；中间状态用于保存明确的验收边界，不对本任务增加独立前端接口。

### 4.3 原子性

- 创建故障：故障、设备状态、成功审计、幂等响应同一事务提交。
- 开始维修：故障状态、工单、维修记录、设备状态、诊断采纳标记、成功审计、幂等响应同一事务提交。
- 提交维修结果：人工最终字段、工单/故障完成状态、历史案例、设备状态、成功审计、幂等响应同一事务提交。
- 任一步失败先回滚主事务，再通过现有独立失败审计路径记录脱敏失败事件；不得返回伪造的 `audit_event_id`。

设备状态随业务事实更新：正式故障进入 `FAULT`，开始维修进入 `REPAIRING`；最后一个活跃故障完成后恢复 `NORMAL`。如果设备仍有其他待接单或维修中故障，不得提前恢复正常。

## 5. API 契约

### 5.1 `POST /api/fault-reports`

- 权限：`fault:create`
- `Idempotency-Key`：必填
- 请求：`equipment_id`、`urgency`、`symptom`、`occurred_at`、可选 `possible_location`、`description`、`attachment_refs`
- 成功：201，返回正式故障字段及 `audit_event_id`
- 关键失败：设备不存在/停用、未来时间、缺少必填字段、幂等冲突

### 5.2 `POST /api/fault-reports/{id}/start-repair`

- 权限：`fault:repair`
- `Idempotency-Key`：必填
- 请求：`mode`；`ADOPTED` 时必须提供属于该故障且可采纳的 `diagnosis_draft_id`，`DIRECT` 时禁止该字段
- 成功：200，返回故障、工单、维修记录标识、状态、开始方式及 `audit_event_id`
- 关键失败：故障不存在、非法状态、草稿不存在/不属于故障/未就绪/已采纳、并发工单冲突

### 5.3 `POST /api/work-orders/{id}/repair-result`

- 权限：`fault:close`
- `Idempotency-Key`：必填
- 请求：`actual_cause`、`actual_solution`、`repair_result`，可选 `parts_replacement_notes`
- 成功：200，返回最终工单/维修事实、历史案例 ID 及 `audit_event_id`
- 关键失败：工单不存在、非法状态、三个最终字段任一为空、重复关闭冲突

### 5.4 `GET /api/repair-cases/similar`

- 权限：`maintenance:view`
- 查询：至少提供 `equipment_type`、`equipment_model` 或 `symptom` 之一；支持受限 `limit`
- 成功：200，按设备类型/型号精确匹配优先、故障现象文本匹配次之、完成时间倒序返回结构化案例
- 禁止：调用 RAGFlow、LLM 或返回知识文档引用

所有请求模型拒绝额外字段。写失败响应沿用 TASK-002 的 `detail.code,message,fields,audit_event_id` 契约。

## 6. 权限、幂等与审计

- 复用 TASK-002 固定权限目录，不新增动态权限。
- 幂等作用域继续使用用户、HTTP 方法、实际路径和 Key；请求体规范化后参与比较。
- 成功审计动作固定为 `fault_report.create`、`repair.start`、`repair.complete`。
- 失败审计保存业务错误码和递归脱敏后的请求摘要，不保存附件正文或诊断原始内容。
- 查询接口不产生成功审计；权限拒绝由现有依赖统一审计。

## 7. 设备停用保护

设备更新为 `DISABLED` 前，设备服务查询是否存在 `PENDING_ACCEPT` 或 `IN_REPAIR` 的故障。存在任一活跃故障时返回 `409 EQUIPMENT_ACTIVE_FAULT`，字段原因固定为 `status=active_fault`。

保护检查与设备更新使用同一数据库事务；PostgreSQL 真实验证覆盖并发创建故障与停用设备的竞争条件。TASK-003 不增加设备删除接口。

## 8. 迁移顺序

当前集成基线的 Alembic head 为 `0002`，但 DEV-002 的 TASK-006 候选已占用 `0003`。TASK-003 不复制或修改 TASK-006 迁移，也不把未获批 TASK-006 提交合入本任务分支。

开发期间 TASK-003 使用独立候选 revision 标识并保持从当前正式 head 可验证。提交正式审核前必须先合并最新 `codex/stage-05-integration`：

- 若 TASK-006 的 `0003` 已正式集成，TASK-003 迁移调整为其后的单一线性 head；
- 若 TASK-006 尚未集成，TASK-003 保持唯一候选 head，并在集成核查中明确迁移顺序；
- 不允许两个未解释的 Alembic head 进入集成分支。

迁移必须验证空库升级、`0002 -> TASK-003 head` 升级、downgrade 回退和再次升级。downgrade 会删除 TASK-003 业务表，属于开发验证数据破坏；只在隔离测试数据库执行。

## 9. 代码边界

规范位置：

```text
codebase/backend/app/modules/maintenance/
  __init__.py
  models.py
  schemas.py
  service.py
  router.py
codebase/backend/tests/modules/test_maintenance_lifecycle.py
codebase/backend/alembic/versions/<task-003-revision>.py
```

`app/main.py` 只注册 maintenance router。设备模块只增加活跃故障停用保护，不进行无关重构。继续复用现有数据库、认证、权限、幂等和审计设施，不新增生产依赖、兼容层、通用 manager/factory 或第二套错误处理框架。

## 10. TDD 与验证矩阵

每个行为严格执行 RED—GREEN—REFACTOR：先运行新测试并确认因功能缺失而失败，再写最小实现。

自动化测试至少覆盖：

- 人工故障必填字段、未来发生时间、停用设备和附件引用限制；
- 故障创建后状态、设备状态、审计和幂等原样重放；
- 直接开始不保留诊断草稿、预填或 AI 摘要；
- 采纳开始只接受同故障、已就绪且未采纳的草稿；
- 非法、重复和并发状态迁移不产生重复工单/维修记录；
- 缺少实际原因、方案或结果不能完成维修；
- 人工最终字段覆盖预填，完成事务只沉淀一条历史案例；
- 相似案例只查询 PostgreSQL，空结果不伪造案例；
- 活跃故障阻止设备停用，全部完成后允许停用；
- 主事务失败时业务数据回滚，失败审计仍可追踪且已脱敏；
- Alembic 升级、降级和单一 head。

最低验证命令：

```powershell
python -m pytest codebase/backend/tests/modules/test_maintenance_lifecycle.py -q
python -m pytest codebase/backend/tests/modules -q
python -m compileall -q codebase/backend/app codebase/backend/alembic
git diff --check
```

正式候选还必须由 DEV-001 在 PostgreSQL 17 上执行事务、并发和迁移升降级验证。SQLite 测试不能替代 PostgreSQL 约束和锁验证。

## 11. 错误处理与回滚

- 业务校验使用稳定错误码，不泄露 SQL、堆栈或敏感字段。
- 数据库唯一键/并发冲突映射为稳定 409，不静默吞掉 `IntegrityError`。
- 失败审计无法持久化时返回现有 `AUDIT_PERSIST_FAILED`，不伪造事件 ID。
- 应用回滚使用回退任务 Commit；数据库按已验证 downgrade 或前向修复执行。
- 已产生正式维修数据后不得擅自 downgrade 或删除表，必须单独获得数据变更授权。

## 12. 完成判定

TASK-003 只有同时满足以下条件才可转 Ready 并请求 DEV-002 审核精确 HEAD：

- 四个共享 API、状态机、设备保护和结构化案例闭环全部实现；
- Python 3.13 模块/回归测试和 PostgreSQL 17 事务、并发、迁移验证通过；
- 直接开始边界、人工最终字段和不调用 RAGFlow 均有失败先行测试；
- Alembic 在最新集成基线上保持可解释的单一 head；
- API_SPEC、DATA_MODEL、测试证据、Review、Commit Log、检查点和交接记录一致；
- 未实现 RAGFlow、诊断 Agent、前端或其他任务代码；
- 未新增生产依赖、兼容代码、多余抽象或无关修改；
- 同一 Draft PR 目标为 `codex/stage-05-integration`，描述绑定当前完整 HEAD 和真实验证证据。
