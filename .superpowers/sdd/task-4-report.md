# Task 4 报告：组织层级、启停和删除保护

## 状态

- Status：DONE
- 基线：`07b2551`
- 范围：组织列表、创建、更新、删除及组织领域规则；未进入完整设备 API 或交付文档。

## 上下文澄清

实施前按简报要求暂停并获得以下裁决：

1. 生产唯一 ROOT 只由 Alembic `0002` 创建；应用和领域层不得补建。SQLite `Base.metadata.create_all()` 测试夹具显式插入每 client 隔离的固定 ROOT：`type=ROOT`、`code=ROOT`、`name=根节点`、`parent_id=None`、`enabled=True`。
2. update 不允许改变 `type` 或 `parent_id`。创建与更新使用分离 schema，均设置 `extra="forbid"`；PATCH 携带这两个字段返回 `422 VALIDATION_ERROR`，并由统一失败审计记录。

## TDD 证据

### RED

命令：

```powershell
D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m pytest codebase/backend/tests/modules/test_task002_organizations.py -q
```

首次结果：退出码 1，`6 failed, 1 warning`。首个明确失败为组织列表缺少 `type`，其余场景同样在读取 ROOT 时失败；失败原因是组织完整合同尚未实现，而非测试导入或语法错误。

### GREEN 与回归

聚焦组织、动作名和旧 identity 回归：

```powershell
D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m pytest codebase/backend/tests/modules/test_task002_organizations.py codebase/backend/tests/modules/test_task002_audit.py::test_protected_write_routes_use_resource_action_names codebase/backend/tests/modules/test_identity_permissions.py -q
```

结果：退出码 0，`41 passed, 1 warning`。

完整后端：

```powershell
D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m pytest codebase/backend/tests -q
```

结果：退出码 0，`81 passed, 1 warning in 12.16s`。警告为已有 Starlette/httpx 弃用警告。

编译检查：

```powershell
D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m compileall -q codebase/backend/app codebase/backend/tests
```

结果：退出码 0。

## 实现与验收

- 新增 `OrganizationCreate` / `OrganizationUpdate` 严格写 schema；没有为旧请求体增加兼容分支。
- 新增组织领域服务，所有 create/update/delete 在读取组织树前复用 PostgreSQL advisory transaction lock `824003`。
- 强制固定层级 `ROOT -> FACTORY -> WORKSHOP -> LINE`、父节点启用、code 全局唯一、同级 name 唯一。
- ROOT 的更新、停用和删除统一返回 `ORGANIZATION_ROOT_PROTECTED`。
- 停用节点在同一事务内迭代停用全部后代；重新启用父节点只启用所选节点。
- 删除前检查直接子节点和设备引用，分别返回 `ORGANIZATION_HAS_CHILDREN` / `ORGANIZATION_HAS_EQUIPMENT`。
- 路由复用既有成功/失败审计和 POST/PATCH 幂等；DELETE 不使用幂等缓存，但成功和失败均审计，动作名为 `organization.delete`。
- 组织路由函数均少于 60 行；`git diff --check` 退出码 0。

## 文件

- 新增 `codebase/backend/app/modules/equipment/schemas.py`
- 新增 `codebase/backend/app/modules/equipment/organization_service.py`
- 修改 `codebase/backend/app/modules/equipment/organization_router.py`
- 新增 `codebase/backend/tests/modules/test_task002_organizations.py`
- 修改 `codebase/backend/tests/modules/support.py`
- 修改旧 identity/audit 测试以使用固定 ROOT 与新写合同。

## 独立自审

- 兼容代码：无。
- 抽象层：仅新增简报指定的组织领域 service；路由内两个私有 helper 用于复用既有幂等/审计收尾，没有新增通用层。
- 无关修改：无。
- 未验证：未连接实际 PostgreSQL 运行并发写；锁调用 SQL 和固定参数由现有 PostgreSQL recording-session 回归覆盖，SQLite 中按设计为 no-op。

## 审查修复追加记录

### 授权范围

- 按审查意见最小修改现有设备 create/update 控制器：仅在幂等查找和组织读取前获取组织树锁 `824003`，未改变设备字段、schema、响应或其他 Task 5 合同。
- 未新增通用锁层；设备路由直接复用 `organization_service.acquire_organization_tree_lock()`。

### RED / GREEN

1. 锁顺序：组织 create/update/delete 与设备 create/update 的 3 个序列测试首次 `3 failed`，实际序列缺少前置 tree lock；入口加锁后 `3 passed`，固定为 `tree -> idempotency/business`。
2. 更新唯一冲突与删除外键竞态：注入实际 SQLAlchemy `IntegrityError`，首次 `4 failed` 且异常穿透；增加 rollback 和约束映射后 `4 passed`。SQLite 唯一消息分别映射 code/name，未知唯一冲突映射 `ORGANIZATION_CONFLICT`；实现同时读取 PostgreSQL `diag.constraint_name`。删除外键冲突映射 `ORGANIZATION_HAS_EQUIPMENT`。所有 API 失败响应均断言含 `audit_event_id`。
3. 非法环：SQLite 旁路构造自环和三节点环，旧实现两项均在第 7 次后代查询被测试 guard 截断（`2 failed`）；加入 visited 集合后 `2 passed`，稳定返回 `422 ORGANIZATION_TREE_INVALID` 并写失败审计。

### 审查后验证

```powershell
D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m pytest codebase/backend/tests/modules/test_task002_organizations.py codebase/backend/tests/modules/test_identity_permissions.py codebase/backend/tests/modules/test_task002_audit.py -q
```

结果：退出码 0，`64 passed, 1 warning in 22.84s`。

```powershell
D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m pytest codebase/backend/tests -q
```

结果：退出码 0，`90 passed, 1 warning in 30.67s`。

```powershell
D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m compileall -q codebase/backend/app codebase/backend/tests
git diff --check
```

结果：均退出码 0。组织路由和组织 service 的所有函数均少于 60 行。
