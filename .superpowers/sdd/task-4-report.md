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
