# TASK-003 故障、工单、维修与结构化案例闭环实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use `executing-plans` for inline execution and `test-driven-development` for every behavior. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 PostgreSQL 中建立故障、工单、维修记录和结构化历史案例的唯一事实闭环，并交付已认证、可审计、可幂等的四个共享 API。

**Architecture:** 新增单一 `maintenance` 业务模块，使用同步 SQLAlchemy 2.0 模型和服务函数管理事务状态；FastAPI 路由复用 TASK-002 的认证、固定权限、幂等响应和审计设施。设备模块只增加基于真实活跃故障的停用保护。案例查询只访问 PostgreSQL，不连接 RAGFlow、LLM 或 TASK-008 Agent。

**Tech Stack:** Python 3.13、FastAPI、Pydantic 2、SQLAlchemy 2.x、Alembic 1.x、PostgreSQL 17、pytest。

## Global Constraints

- 输入基线：`codex/stage-05-integration@b29c69d13c3d1c81f01023152eabf0c0f2d02741`。
- 分支：`codex/task-003-maintenance-lifecycle`；目标：`codex/stage-05-integration`。
- 任务开发者：`DEV-001`；指定审核者：`DEV-002`。
- 只实现任务书 TASK-003 和已确认设计；不实现 RAGFlow、Agent 生成、前端、SSE、二进制附件或其他任务代码。
- 不新增生产依赖、兼容层、第二套错误框架或通用 manager/factory/adapter。
- 每项生产行为必须先写失败测试并观察 RED，再做最小 GREEN；不可先写实现再补测试。
- SQLite 用于快速 API/单元测试；PostgreSQL 17 是迁移、锁、并发和事务结论的唯一正式依据。
- 正式送审前必须合并最新集成基线并保持 Alembic 单一线性 head；不 rebase、不强推。

---

### Task 1：冻结模型、枚举和请求契约

**Files:**
- Create: `codebase/backend/app/modules/maintenance/__init__.py`
- Create: `codebase/backend/app/modules/maintenance/models.py`
- Create: `codebase/backend/app/modules/maintenance/schemas.py`
- Test: `codebase/backend/tests/modules/test_maintenance_lifecycle.py`

**Interfaces:**
- Produces: `FaultReport`、`WorkOrder`、`MaintenanceRecord`、`DiagnosisDraft`、`HistoricalRepairCase`。
- Produces: `FaultStatus`、`WorkOrderStatus`、`RepairStartMode`、`DiagnosisDraftStatus`。
- Produces strict request models: `FaultReportCreate`、`StartRepairRequest`、`RepairResultRequest`、`SimilarCaseQuery`。

- [x] **Step 1: 写表、枚举、必填字段和额外字段拒绝的失败测试**

```python
def test_maintenance_tables_and_constraints_exist(client: TestClient) -> None:
    names = set(inspect(client.app.state.engine).get_table_names())
    assert {
        "fault_reports", "work_orders", "maintenance_records",
        "diagnosis_drafts", "historical_repair_cases",
    } <= names


def test_fault_payload_rejects_extra_fields(client: TestClient, fault_headers: dict[str, str]) -> None:
    response = client.post(
        "/api/fault-reports",
        headers=fault_headers,
        json={**valid_fault_body(), "binaryAttachment": "secret"},
    )
    assert response.status_code == 422
    assert response.json()["detail"]["fields"]["binaryAttachment"] == "extra_forbidden"
```

- [x] **Step 2: 运行 RED**

Run:

```powershell
D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m pytest codebase/backend/tests/modules/test_maintenance_lifecycle.py -q
```

Expected: collection fails because `app.modules.maintenance` does not exist.

- [x] **Step 3: 实现最小模型和严格 schema**

```python
class FaultStatus(StrEnum):
    PENDING_ACCEPT = "PENDING_ACCEPT"
    IN_REPAIR = "IN_REPAIR"
    PROCESSED = "PROCESSED"


class WorkOrderStatus(StrEnum):
    DRAFT = "DRAFT"
    PENDING_ACCEPT = "PENDING_ACCEPT"
    IN_REPAIR = "IN_REPAIR"
    PENDING_INSPECTION = "PENDING_INSPECTION"
    COMPLETED = "COMPLETED"


class RepairStartMode(StrEnum):
    DIRECT = "DIRECT"
    ADOPTED = "ADOPTED"
```

模型约束必须包含：编号唯一；工单 `fault_report_id` 唯一；维修记录 `work_order_id` 唯一；案例 `source_work_order_id` 唯一；所有外键明确；枚举使用 `native_enum=False`；JSON 列只保存附件引用、允许预填和只读摘要。

- [x] **Step 4: 运行 GREEN 并检查 diff**

Run:

```powershell
D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m pytest codebase/backend/tests/modules/test_maintenance_lifecycle.py -q
git diff --check
```

Expected: Task 1 tests pass; no whitespace errors.

---

### Task 2：实现人工故障上报、设备状态、幂等和审计

**Files:**
- Create: `codebase/backend/app/modules/maintenance/service.py`
- Create: `codebase/backend/app/modules/maintenance/router.py`
- Modify: `codebase/backend/app/main.py`
- Modify: `codebase/backend/tests/modules/test_maintenance_lifecycle.py`

**Interface:** `POST /api/fault-reports`，权限 `fault:create`，`Idempotency-Key` 必填，成功返回 201 和真实 `audit_event_id`。

- [x] **Step 1: 写失败测试**

覆盖：缺少权限；设备不存在；设备为 `DISABLED`；未来 `occurred_at`；附件引用额外字段；单个 `size_bytes > 100 MiB`；创建成功后故障为 `PENDING_ACCEPT`、设备为 `FAULT`；相同幂等键原样重放且只有一条故障和一条成功审计；相同键不同请求返回 `IDEMPOTENCY_KEY_REUSED`；业务失败回滚并产生一条脱敏失败审计。

```python
def test_create_fault_is_idempotent_and_sets_equipment_fault(
    client: TestClient, fault_headers: dict[str, str], equipment_id: str
) -> None:
    body = valid_fault_body(equipment_id=equipment_id)
    first = client.post("/api/fault-reports", headers=fault_headers, json=body)
    replay = client.post("/api/fault-reports", headers=fault_headers, json=body)
    assert first.status_code == 201
    assert replay.json() == first.json()
    assert equipment_status(client, equipment_id) == "FAULT"
    assert count_rows(client, FaultReport) == 1
```

- [x] **Step 2: 运行 RED**

Expected: 404 because the route is not registered.

- [x] **Step 3: 实现最小事务路径**

路由顺序固定为：取得设备事务锁（PostgreSQL 使用 `SELECT ... FOR UPDATE`）→ 查幂等响应 → 校验请求和设备 → 创建故障并设设备为 `FAULT` → 写成功审计 → 保存幂等响应 → 单次提交。所有业务异常交给现有独立失败审计处理器，服务层不得静默提交或伪造事件 ID。

```python
@router.post("", status_code=201, name="fault_report.create")
def create_fault_report(
    payload: FaultReportCreate,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission("fault:create")),
) -> dict[str, object] | JSONResponse:
    ...
```

- [x] **Step 4: 运行 GREEN 和模块回归**

Run:

```powershell
D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m pytest codebase/backend/tests/modules/test_maintenance_lifecycle.py -q
D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m pytest codebase/backend/tests/modules/test_task002_equipment.py -q
```

---

### Task 3：实现直接开始和采纳诊断开始维修

**Files:**
- Modify: `codebase/backend/app/modules/maintenance/models.py`
- Modify: `codebase/backend/app/modules/maintenance/schemas.py`
- Modify: `codebase/backend/app/modules/maintenance/service.py`
- Modify: `codebase/backend/app/modules/maintenance/router.py`
- Modify: `codebase/backend/tests/modules/test_maintenance_lifecycle.py`

**Interface:** `POST /api/fault-reports/{fault_id}/start-repair`，权限 `fault:repair`，成功返回 200。

- [x] **Step 1: 写直接开始 RED 测试**

覆盖：仅 `PENDING_ACCEPT` 可开始；故障不存在；DIRECT 禁止 `diagnosis_draft_id`；创建唯一工单和唯一维修记录；故障/工单进入 `IN_REPAIR`；设备进入 `REPAIRING`；诊断引用、预填和 AI 摘要均为 `null`；幂等重放无重复副作用；新 Key 重复迁移返回稳定 409。

```python
assert maintenance_record.start_mode == RepairStartMode.DIRECT
assert maintenance_record.diagnosis_draft_id is None
assert maintenance_record.diagnosis_prefill is None
assert maintenance_record.ai_summary is None
```

- [x] **Step 2: 运行 RED；实现 DIRECT 最小路径；运行 GREEN**

开始事务必须锁定故障和设备。重复或并发请求依靠锁、故障状态和唯一约束共同阻止第二条工单。

- [x] **Step 3: 写采纳开始 RED 测试**

覆盖：ADOPTED 缺少草稿 ID；草稿不存在；属于其他故障；状态不是 `DIAGNOSIS_READY`；已经采纳；成功只复制 `allowed_prefill` 与 `read_only_summary`；不复制未知字段、原始思维链、附件正文或秘密；草稿标记为已采纳且只能采纳一次。

- [x] **Step 4: 实现 ADOPTED 最小路径并运行 GREEN**

```python
if payload.mode is RepairStartMode.DIRECT:
    assert payload.diagnosis_draft_id is None
else:
    draft = ready_unadopted_draft_for_fault(db, payload.diagnosis_draft_id, fault.id)
    record.diagnosis_prefill = draft.allowed_prefill
    record.ai_summary = draft.read_only_summary
    draft.adopted_at = utc_now()
```

实现不得生成诊断、调用模型、RAGFlow 或补全客户端未提供的诊断结果。

- [x] **Step 5: 运行状态、幂等、审计和并发回归**

Run:

```powershell
D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m pytest codebase/backend/tests/modules/test_maintenance_lifecycle.py -q -k "start_repair or diagnosis"
```

---

### Task 4：实现维修完成和结构化案例沉淀

**Files:**
- Modify: `codebase/backend/app/modules/maintenance/schemas.py`
- Modify: `codebase/backend/app/modules/maintenance/service.py`
- Modify: `codebase/backend/app/modules/maintenance/router.py`
- Modify: `codebase/backend/tests/modules/test_maintenance_lifecycle.py`

**Interface:** `POST /api/work-orders/{work_order_id}/repair-result`，权限 `fault:close`，成功返回 200。

- [x] **Step 1: 写 RED 测试**

覆盖：工单不存在；不是 `IN_REPAIR`；`actual_cause`、`actual_solution`、`repair_result` 任一缺失或空白；人工最终字段覆盖诊断预填；工单依次完成验收边界并最终为 `COMPLETED`；故障为 `PROCESSED`；每个工单只沉淀一条案例；仍有其他活跃故障时设备不得恢复；最后一个活跃故障完成后设备恢复 `NORMAL`；重放不重复案例；中途失败全部业务数据回滚且失败审计可追踪。

```python
assert record.actual_cause == submitted["actual_cause"]
assert record.actual_solution == submitted["actual_solution"]
assert record.repair_result == submitted["repair_result"]
assert case.actual_cause == submitted["actual_cause"]
assert count_rows(client, HistoricalRepairCase) == 1
```

- [x] **Step 2: 运行 RED**

Expected: 404 because repair-result route does not exist.

- [x] **Step 3: 实现单事务完成路径**

固定顺序：锁工单/故障/设备 → 校验 `IN_REPAIR` → 保存人工最终字段 → `PENDING_INSPECTION` → 生成唯一结构化案例 → `COMPLETED`/`PROCESSED` → 查询设备是否仍有活跃故障并决定 `FAULT` 或 `NORMAL` → 成功审计 → 幂等响应 → 提交。

- [x] **Step 4: 运行 GREEN 和回滚测试**

Run:

```powershell
D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m pytest codebase/backend/tests/modules/test_maintenance_lifecycle.py -q -k "repair_result or rollback or case"
```

---

### Task 5：实现 PostgreSQL 结构化相似案例查询

**Files:**
- Modify: `codebase/backend/app/modules/maintenance/schemas.py`
- Modify: `codebase/backend/app/modules/maintenance/service.py`
- Modify: `codebase/backend/app/modules/maintenance/router.py`
- Create: `codebase/backend/tests/modules/test_maintenance_cases.py`

**Interface:** `GET /api/repair-cases/similar`，权限 `maintenance:view`。

- [x] **Step 1: 写 RED 测试**

覆盖：无查询条件返回 422；`limit` 有边界；设备类型/型号精确匹配优先；症状文本匹配次之；完成时间倒序；空结果返回空列表；未授权返回 403；测试中将任何 RAGFlow/HTTP 客户端调用替换为立即失败，以证明查询只访问数据库。

- [x] **Step 2: 实现确定性查询**

```python
score = case(
    (and_(HistoricalRepairCase.equipment_type == equipment_type,
          HistoricalRepairCase.equipment_model == equipment_model), 3),
    (HistoricalRepairCase.equipment_type == equipment_type, 2),
    (HistoricalRepairCase.equipment_model == equipment_model, 2),
    else_=1,
)
```

症状仅做数据库文本匹配；不得引入向量列、embedding、外部适配器或网络请求。

- [x] **Step 3: 运行 GREEN**

Run:

```powershell
D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m pytest codebase/backend/tests/modules/test_maintenance_cases.py -q
```

---

### Task 6：实现活跃故障设备停用保护

**Files:**
- Modify: `codebase/backend/app/modules/equipment/service.py`
- Modify: `codebase/backend/app/modules/audit/http.py`
- Create: `codebase/backend/tests/modules/test_maintenance_equipment_protection.py`
- Regression: `codebase/backend/tests/modules/test_task002_equipment.py`

- [x] **Step 1: 写 RED 测试**

覆盖：`PENDING_ACCEPT` 或 `IN_REPAIR` 故障存在时，PATCH 设备为 `DISABLED` 返回 409 `EQUIPMENT_ACTIVE_FAULT`，`fields.status=active_fault`，设备保持原状态并生成失败审计；全部相关故障为 `PROCESSED` 后允许停用；更新为其他状态不误阻断。

- [x] **Step 2: 实现最小保护**

在 `update_equipment()` 写值之前，仅当目标状态为 `DISABLED` 时查询真实 `FaultReport` 活跃状态。增加稳定字段映射：

```python
"EQUIPMENT_ACTIVE_FAULT": {"status": "active_fault"},
```

PostgreSQL 验证使用设备行锁协调故障创建和停用；SQLite 测试只验证业务语义，不声称覆盖竞争条件。

- [x] **Step 3: 运行 GREEN 和设备全回归**

Run:

```powershell
D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m pytest codebase/backend/tests/modules/test_task002_equipment.py codebase/backend/tests/modules/test_maintenance_lifecycle.py -q
```

---

### Task 7：增加可逆 Alembic 迁移并冻结迁移顺序

**Files:**
- Create initially: `codebase/backend/alembic/versions/0003_task003_maintenance_lifecycle.py`
- Test: `codebase/backend/tests/modules/test_task003_migration.py`

**Candidate contract:** 开发期 `revision="0003_task003"`、`down_revision="0002"`。该标识与 TASK-006 的候选 `0003` 明确区分，但不得未经线性化进入集成分支。

- [x] **Step 1: 写迁移 RED 测试**

覆盖：从空库 upgrade 到 head；从 `0002` upgrade 到 TASK-003 head；五张表、索引、外键、唯一/检查约束存在；downgrade 回 `0002` 后五张表消失且 TASK-002 表保留；再次 upgrade 成功；`alembic heads` 只有一个可解释 head。

- [x] **Step 2: 运行 RED**

Expected: revision 不存在或 maintenance 表缺失。

- [x] **Step 3: 实现 upgrade/downgrade**

upgrade 按外键顺序创建：`fault_reports` → `diagnosis_drafts` → `work_orders` → `maintenance_records` → `historical_repair_cases`。downgrade 反序删除。枚举使用非原生约束，避免残留 PostgreSQL enum type。

- [x] **Step 4: 在隔离 PostgreSQL 17 数据库验证**

开发数据库必须使用独立数据库名；downgrade 会删除 TASK-003 表，禁止对共享或正式数据执行。

```powershell
$env:POSTGRES_DSN='postgresql+psycopg://<redacted>@127.0.0.1:<isolated-port>/task003_verify'
D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m alembic -c codebase/backend/alembic.ini upgrade head
D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m alembic -c codebase/backend/alembic.ini downgrade 0002
D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m alembic -c codebase/backend/alembic.ini upgrade head
```

- [x] **Step 5: 正式送审前线性化**

先用 Merge Commit 合并最新 `origin/codex/stage-05-integration`：

- 若正式 head 仍为 `0002`：保留文件名和 `revision="0003_task003"`，在 PR 描述明确 TASK-006 尚未集成及后续顺序责任。
- 若 TASK-006 的 `0003` 已集成：将文件改名为 `0004_task003_maintenance_lifecycle.py`，设置 `revision="0004"`、`down_revision="0003"`，同步迁移测试和文档。
- 运行 `alembic heads`；任何未解释多 head 均为阻断，不得转 Ready。

---

### Task 8：完成契约文档、全量验证和正式交付证据

**Files:**
- Modify: `04-architecture-plan/API_SPEC.md`
- Modify: `04-architecture-plan/DATA_MODEL.md`
- Modify: `05-development/SELF_TEST.md`
- Modify: `05-development/CODE_REVIEW.md`
- Modify: `05-development/COMMIT_LOG.md`
- Modify: `05-development/CHECKPOINTS.md`
- Modify: `06-testing/DEFECTS.md` only if a real defect is opened/closed
- Modify: `workflow/DEV_TO_PM_HANDOFF.md`
- Modify: `workflow/state.json` only for the actual TASK-003 handoff state permitted by the task book

- [x] **Step 1: 同步 API 和数据模型契约**

记录四个端点的权限、请求/响应字段、状态码、稳定错误、幂等和审计；记录五张表、约束、状态机、人工最终字段和 PostgreSQL-only 案例边界。不得改写 PRD、SPEC 或验收标准。

- [x] **Step 2: Python 3.13 验证**

```powershell
D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m pytest codebase/backend/tests/modules/test_maintenance_lifecycle.py -q
D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m pytest codebase/backend/tests/modules -q
D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m compileall -q codebase/backend/app codebase/backend/alembic
git diff --check
```

- [x] **Step 3: PostgreSQL 17 真实验证**

验证事务回滚、同 Key 并发故障创建、并发开始维修、故障创建与设备停用竞争、迁移空库升级/`0002` 升级/downgrade/再升级和单一 head。记录真实命令、容器/数据库版本、退出码和脱敏结果；不得用 SQLite 替代。

- [x] **Step 4: 独立三轮自查**

1. Spec：逐条映射 TASK-003 范围、AC 和四个 API。
2. Standards/Security：权限、幂等、成功/失败审计、脱敏、事务、迁移和秘密边界。
3. Scope/Diff：确认没有 RAGFlow、Agent、前端、TASK-004/005/006/008、生产依赖、兼容层、多余抽象或无关格式化。

发现 Critical/Important/Minor 均先修复并重新运行相关 RED/GREEN 与回归，不得只记录后送审。

本地验证记录（2026-07-20，未推送、未发起审核）：Python 3.13.14 模块测试 `168 passed`；PostgreSQL 17.10 隔离数据库迁移、事务与并发测试 `4 passed`；`compileall`、`git diff --check` 通过；`alembic heads` 为单一 `0003_task003`。远端集成分支仍为本任务基线 `b29c69d13c3d1c81f01023152eabf0c0f2d02741`，没有新的迁移需要合并，故无需制造空 Merge Commit。三轮自查发现的时区、诊断嵌套值、SQL 通配符、写权限和幂等冲突覆盖缺口均已修复并完成回归。

- [ ] **Step 5: 更新正式交付台账**

`SELF_TEST`、`CODE_REVIEW`、`COMMIT_LOG`、`CHECKPOINTS`、handoff 和 `state.json` 必须使用同一完整 HEAD、基线、测试结果、迁移 head、未验证项和下一动作。候选未审核前不得把 TASK-003 写成完成或解锁依赖。

- [ ] **Step 6: 推送同一 Draft PR 并请求 DEV-002 审核**

创建或维护 TASK-003 唯一 Draft PR，目标为 `codex/stage-05-integration`。PR 描述绑定完整 HEAD 和验证证据；只请求 `DEV-002` 审核该精确 HEAD。未经审核通过、DEV-001 集成核查和项目负责人对具体 PR/HEAD 的 Merge 授权，不得转交合并。

## 完成判定

只有以下条件同时成立，TASK-003 才可声明“开发候选完成”：

- 四个 API、状态机、人工最终字段、设备停用保护和 PostgreSQL 案例闭环全部通过测试；
- Python 3.13 与 PostgreSQL 17 的迁移、事务和并发证据完整；
- Alembic 在最新集成基线上为单一线性 head；
- 契约、实现、测试、Review、Commit Log、检查点、handoff 和机器状态一致；
- 精确 HEAD 已推送至同一 Draft PR，并等待 DEV-002 正式审核；
- 没有 TASK-003 范围外修改。
