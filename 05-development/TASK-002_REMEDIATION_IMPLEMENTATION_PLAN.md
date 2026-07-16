# TASK-002 正式审核阻断项修复实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不改变已批准产品范围和技术栈的前提下，补齐 TASK-002 的设备、组织、身份权限、失败审计、脱敏和 API 契约，使 PR #15 形成可重新提交 DEV-002 审核的新候选 Commit。

**Architecture:** 保留现有 FastAPI 路由、同步 SQLAlchemy Session、Alembic 和 PostgreSQL；新增仅服务于当前领域的 schema/service 文件，将层级和状态规则移出超长路由。失败审计由 FastAPI 异常处理器统一落库，业务成功审计继续与主事务原子提交；公开契约同步到 `API_SPEC.md`。

**Tech Stack:** Python 3.13.14、FastAPI 0.115+、SQLAlchemy 2.x、Alembic 1.x、psycopg 3、PostgreSQL 17、Redis 7、pytest 9、Docker Compose。

## Global Constraints

- 修复来源为 `CR-036`，被拒绝候选为 `cfb8ed9b99b5e440b3c0bf4a8652f4f7d233ee77`，书面设计为 `05-development/TASK-002_REMEDIATION_DESIGN.md`。
- 不修改 PRD、SPEC、AC 或 Stage 3 原型；不提前实现 TASK-003、TASK-004 或附件存储任务。
- PRD FR-010、DEV-002 审核和 CR-036 确认的“四个固定角色”控制后端实现；现有 Stage 3 原型仍含“新增自定义角色”旧交互，登记为 TASK-010 前必须由产品侧纠正的原型差异，本次不得据此恢复动态角色 API。
- 不新增生产依赖，不建立组织/设备行级授权，不增加通用 CRUD、Repository、Manager、Factory 或兼容层。
- 设备只保存图片对象引用元数据；密码、Token、Cookie、密钥及敏感附件正文不得进入审计或日志。
- 所有新增或修复行为必须先有失败测试并观察 RED，再做最小实现转为 GREEN。
- 普通函数目标不超过 40 行；超过 60 行必须在本任务内按职责拆分；不向现有 600 行测试文件继续增加新业务场景。
- 每个任务只提交本任务列出的文件；每次提交前运行最小相关测试和 `git diff --check`。

---

## 文件结构与职责

- `codebase/backend/app/modules/audit/http.py`：统一受保护写操作异常映射和失败审计。
- `codebase/backend/app/modules/identity/schemas.py`：用户和角色权限请求模型。
- `codebase/backend/app/modules/identity/admin_service.py`：固定角色、用户启停及授权规则。
- `codebase/backend/app/modules/equipment/schemas.py`：组织和设备请求/响应字段。
- `codebase/backend/app/modules/equipment/organization_service.py`：组织层级、唯一性、级联停用和删除保护。
- `codebase/backend/app/modules/equipment/service.py`：设备字段、组织和负责人校验。
- `codebase/backend/tests/modules/support.py`：本次新增测试共享的 SQLite app、用户、角色和请求头工厂。
- `codebase/backend/tests/modules/conftest.py`：向本次新增模块测试暴露隔离的 `client` fixture。
- `codebase/backend/tests/__init__.py`、`codebase/backend/tests/modules/__init__.py`：固定测试包导入路径，使 `tests.modules.support` 不依赖 pytest 的临时导入模式。
- `codebase/backend/tests/modules/test_task002_*.py`：按审核阻断领域拆分的新测试，不继续扩大旧测试文件。
- `codebase/backend/alembic/versions/0002_task002_contract_completion.py`：从已发布 `0001` 前向迁移到完整 TASK-002 数据契约。

---

### Task 1: 完整模型与 0002 前向迁移

**Files:**
- Create: `codebase/backend/tests/modules/support.py`
- Create: `codebase/backend/tests/modules/conftest.py`
- Create: `codebase/backend/tests/__init__.py`
- Create: `codebase/backend/tests/modules/__init__.py`
- Create: `codebase/backend/tests/modules/test_task002_schema.py`
- Modify: `codebase/backend/tests/modules/test_identity_permissions.py`
- Modify: `codebase/backend/app/modules/identity/models.py`
- Modify: `codebase/backend/app/modules/identity/bootstrap.py`
- Modify: `codebase/backend/app/modules/equipment/models.py`
- Create: `codebase/backend/alembic/versions/0002_task002_contract_completion.py`

**Interfaces:**
- Produces: `RoleCode`, `OrganizationType`, `EquipmentStatus` 字符枚举。
- Produces: `ensure_identity_catalog(db: Session) -> dict[RoleCode, Role]`。
- Produces: revision `0002` with `down_revision = "0001"`。
- Consumed later by identity, organization and equipment services.

- [ ] **Step 1: 建立新测试支持文件**

```python
# codebase/backend/tests/modules/support.py
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import Base
from app.main import create_app
from app.modules.identity.models import Permission, Role, User
from app.modules.identity.security import hash_password


def build_client() -> TestClient:
    app = create_app(
        postgres_dsn="sqlite+pysqlite:///:memory:",
        redis_url="redis://redis:6379/0",
    )
    Base.metadata.create_all(app.state.engine)
    return TestClient(app)


def create_user_token(
    client: TestClient,
    *,
    username: str,
    role_code: str,
    permission_codes: list[str],
) -> tuple[str, str]:
    with client.app.state.session_factory() as db:
        permissions = []
        for code in permission_codes:
            permission = db.scalar(select(Permission).where(Permission.code == code))
            if permission is None:
                permission = Permission(code=code)
                db.add(permission)
            permissions.append(permission)
        role = db.scalar(select(Role).where(Role.code == role_code))
        if role is None:
            role = Role(code=role_code, name=role_code, built_in=True)
            db.add(role)
        role.permissions = permissions
        user = User(username=username, password_hash=hash_password("correct-password"), roles=[role])
        db.add(user)
        db.commit()
        user_id = user.id
    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": "correct-password"},
    )
    assert response.status_code == 200
    return user_id, response.json()["access_token"]
```

```python
# codebase/backend/tests/modules/conftest.py
import pytest
from fastapi.testclient import TestClient

from tests.modules.support import build_client


@pytest.fixture
def client() -> TestClient:
    return build_client()
```

Create the two `__init__.py` files as empty package markers; they contain no runtime behavior.

- [ ] **Step 2: 写模型与目录 RED 测试**

```python
# codebase/backend/tests/modules/test_task002_schema.py
from sqlalchemy import UniqueConstraint

from app.modules.equipment.models import Equipment, EquipmentStatus, Organization, OrganizationType
from app.modules.identity.bootstrap import FIXED_ROLE_CODES
from app.modules.identity.models import RoleCode


def test_task002_models_expose_full_contract() -> None:
    assert set(Equipment.__table__.c.keys()) >= {
        "id", "code", "name", "model", "type", "manufacturer",
        "manufactured_at", "commissioned_at", "operating_hours", "status",
        "organization_id", "owner_user_id", "image_refs", "created_at", "updated_at",
    }
    assert "enabled" not in Equipment.__table__.c
    assert set(Organization.__table__.c.keys()) >= {
        "id", "type", "code", "name", "parent_id", "sort_order",
        "enabled", "remark", "created_at", "updated_at",
    }
    assert set(FIXED_ROLE_CODES) == set(RoleCode)
    assert EquipmentStatus.DISABLED.value == "DISABLED"
    assert OrganizationType.LINE.value == "LINE"


def test_organization_has_global_code_and_sibling_name_constraints() -> None:
    names = {
        constraint.name
        for constraint in Organization.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    assert {"uq_organizations_code", "uq_organizations_parent_name"} <= names
```

- [ ] **Step 3: 运行 RED**

Run:

```powershell
D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m pytest codebase/backend/tests/modules/test_task002_schema.py -q
```

Expected: FAIL during import because `EquipmentStatus`、`OrganizationType` and `RoleCode` do not exist.

- [ ] **Step 4: 实现枚举和完整 SQLAlchemy 模型**

```python
class RoleCode(StrEnum):
    SYSTEM_ADMIN = "SYSTEM_ADMIN"
    EQUIPMENT_ADMIN = "EQUIPMENT_ADMIN"
    REPAIR_WORKER = "REPAIR_WORKER"
    LINE_OPERATOR = "LINE_OPERATOR"


class OrganizationType(StrEnum):
    ROOT = "ROOT"
    FACTORY = "FACTORY"
    WORKSHOP = "WORKSHOP"
    LINE = "LINE"


class EquipmentStatus(StrEnum):
    NORMAL = "NORMAL"
    FAULT = "FAULT"
    REPAIRING = "REPAIRING"
    DISABLED = "DISABLED"
```

Use SQLAlchemy `Enum(..., native_enum=False)`, `Numeric(12, 2)`, `Date`, `JSON`, explicit UTC timestamps and these constraints:

```python
class Organization(Base):
    __tablename__ = "organizations"
    __table_args__ = (
        UniqueConstraint("code", name="uq_organizations_code"),
        UniqueConstraint("parent_id", "name", name="uq_organizations_parent_name"),
    )


class Equipment(Base):
    __tablename__ = "equipment"
    __table_args__ = (
        CheckConstraint("operating_hours >= 0", name="ck_equipment_operating_hours_nonnegative"),
    )
```

Add `Role.code` unique/non-null and `Role.built_in` non-null. Update old test constructors to provide canonical organization/equipment fields and `Role.code`; do not add new scenarios to the old file.

- [ ] **Step 5: 实现固定目录初始化和 0002**

```python
FIXED_ROLE_CODES = tuple(RoleCode)
API_PERMISSION_CODES = (
    "identity:read", "identity:write", "equipment:read", "equipment:write",
    "organization:read", "organization:write",
)
MENU_ACTION_PERMISSION_CODES = (
    "workbench:view", "workbench:export", "bi:view", "bi:export",
    "factory:view", "factory:manage", "equipment:view", "equipment:create",
    "equipment:edit", "equipment:delete", "fault:view", "fault:create",
    "fault:repair", "fault:close", "maintenance:view", "maintenance:detail",
    "maintenance:export", "system:role", "system:user",
    "user_management.view_all", "system:org", "system:audit",
    "intelligence:view", "intelligence:model", "intelligence:agent",
    "intelligence:knowledge", "intelligence:audit",
)
PERMISSION_CODES = API_PERMISSION_CODES + MENU_ACTION_PERMISSION_CODES

DEFAULT_ROLE_PERMISSIONS = {
    RoleCode.EQUIPMENT_ADMIN: {
        "identity:read", "equipment:read", "equipment:write", "organization:read",
        "workbench:view", "bi:view", "factory:view", "equipment:view",
        "equipment:create", "equipment:edit", "fault:view", "fault:create",
        "maintenance:view", "maintenance:detail",
    },
    RoleCode.REPAIR_WORKER: {
        "equipment:read", "workbench:view", "equipment:view", "fault:view",
        "fault:repair", "fault:close", "maintenance:view", "maintenance:detail",
    },
    RoleCode.LINE_OPERATOR: {
        "equipment:read", "workbench:view", "equipment:view", "fault:view", "fault:create",
    },
}


def ensure_identity_catalog(db: Session) -> dict[RoleCode, Role]:
    permissions = {
        code: db.scalar(select(Permission).where(Permission.code == code)) or Permission(code=code)
        for code in PERMISSION_CODES
    }
    roles: dict[RoleCode, Role] = {}
    for code in FIXED_ROLE_CODES:
        role = db.scalar(select(Role).where(Role.code == code.value))
        if role is None:
            role = Role(code=code.value, name=code.value, built_in=True)
            db.add(role)
        roles[code] = role
    roles[RoleCode.SYSTEM_ADMIN].permissions = list(permissions.values())
    for code, defaults in DEFAULT_ROLE_PERMISSIONS.items():
        if not roles[code].permissions:
            roles[code].permissions = [permissions[item] for item in sorted(defaults)]
    db.flush()
    return roles
```

Revision `0002` must: add nullable columns, backfill deterministic values, create one `ROOT`, reparent legacy top-level organizations, infer depth 1/2/3, abort depth greater than 3, map equipment `enabled` to status, seed fixed roles, map `system-administrator` to `SYSTEM_ADMIN`, then make required columns non-null and add constraints. Downgrade must state its destructive nature in the module docstring and reverse only schema introduced by `0002`; it must never drop `0001` tables.

- [ ] **Step 6: 运行 GREEN 和旧回归**

Run:

```powershell
D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m pytest codebase/backend/tests/modules/test_task002_schema.py codebase/backend/tests/modules/test_identity_permissions.py -q
```

Expected: PASS; existing behavior remains covered after model constructor updates.

- [ ] **Step 7: 提交模型和迁移**

```powershell
git add codebase/backend/app/modules/identity codebase/backend/app/modules/equipment/models.py codebase/backend/alembic/versions/0002_task002_contract_completion.py codebase/backend/tests/modules
git commit -m "feat(task-002): complete identity equipment schema"
```

---

### Task 2: 附件脱敏与统一失败审计

**Files:**
- Create: `codebase/backend/tests/modules/test_task002_audit.py`
- Modify: `codebase/backend/app/modules/audit/service.py`
- Create: `codebase/backend/app/modules/audit/http.py`
- Modify: `codebase/backend/app/modules/identity/dependencies.py`
- Modify: `codebase/backend/app/main.py`
- Modify: `codebase/backend/app/core/idempotency.py`

**Interfaces:**
- Produces: `sanitize_audit_metadata(value: object, *, context: tuple[str, ...] = ()) -> object`。
- Produces: `register_audit_exception_handlers(app: FastAPI) -> None`。
- Protected write route names use `resource.action`, for example `equipment.create`.

- [ ] **Step 1: 写脱敏和失败审计 RED 测试**

```python
def test_attachment_content_is_redacted_without_removing_metadata() -> None:
    value = sanitize_audit_metadata({
        "attachment": {"filename": "manual.pdf", "content": "secret-body"},
        "content": "ordinary-business-content",
        "content_base64": "c2VjcmV0",
    })
    assert value["attachment"] == {"filename": "manual.pdf", "content": "[REDACTED]"}
    assert value["content"] == "ordinary-business-content"
    assert value["content_base64"] == "[REDACTED]"


def test_failed_protected_write_returns_persisted_audit_id(client: TestClient) -> None:
    user_id, token = create_user_token(
        client, username="writer", role_code="EQUIPMENT_ADMIN",
        permission_codes=["equipment:write"],
    )
    response = client.post(
        "/api/equipment",
        headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "invalid-equipment"},
        json={"code": "", "name": ""},
    )
    assert response.status_code == 422
    event_id = response.json()["detail"]["audit_event_id"]
    with client.app.state.session_factory() as db:
        event = db.get(AuditEvent, event_id)
    assert event is not None
    assert event.actor_user_id == user_id
    assert event.result == "failure"
```

- [ ] **Step 2: 运行 RED**

Run:

```powershell
D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m pytest codebase/backend/tests/modules/test_task002_audit.py -q
```

Expected: FAIL because attachment content is retained and validation errors have no `audit_event_id`.

- [ ] **Step 3: 实现上下文脱敏**

```python
ATTACHMENT_CONTEXT_KEYS = {"attachment", "attachments", "file", "files", "upload", "document", "image"}
ATTACHMENT_CONTENT_KEYS = {"body", "content", "data", "bytes", "text", "base64"}
DIRECT_ATTACHMENT_CONTENT_KEYS = {"attachment_content", "file_content", "file_bytes", "content_base64"}


def sanitize_audit_metadata(value: object, *, context: tuple[str, ...] = ()) -> object:
    if isinstance(value, dict):
        result: dict[str, object] = {}
        attachment_context = any(part in ATTACHMENT_CONTEXT_KEYS for part in context)
        for key, item in value.items():
            normalized = normalize_key(key)
            redact = (
                is_sensitive_key(key)
                or normalized in DIRECT_ATTACHMENT_CONTENT_KEYS
                or (attachment_context and normalized in ATTACHMENT_CONTENT_KEYS)
            )
            result[key] = "[REDACTED]" if redact else sanitize_audit_metadata(
                item, context=(*context, normalized)
            )
        return result
    if isinstance(value, list):
        return [sanitize_audit_metadata(item, context=context) for item in value]
    if isinstance(value, str) and "bearer " in value.lower():
        return "[REDACTED]"
    return value
```

- [ ] **Step 4: 实现统一异常处理器**

`register_audit_exception_handlers()` must register async handlers for `HTTPException`, `RequestValidationError`, and `IdempotencyKeyReused`. For API writes except `/api/auth/login`, normalize the detail, reuse `request.state.audit_event_id` when present, otherwise open `request.app.state.session_factory()`, write a `failure` event using the route name, commit, and append `audit_event_id` to `detail`. Validation fields use the final string member of `error["loc"]` and the Pydantic error type.

```python
def protected_write(request: Request) -> bool:
    return request.url.path.startswith("/api/") and request.method in {
        "POST", "PUT", "PATCH", "DELETE"
    } and request.url.path != "/api/auth/login"


def route_action(request: Request) -> str:
    route = request.scope.get("route")
    return getattr(route, "name", None) or f"http.{request.method.lower()}"


def response_detail(detail: object, event_id: str | None) -> dict[str, object]:
    normalized = detail if isinstance(detail, dict) else {"code": "REQUEST_FAILED", "message": str(detail)}
    result = dict(normalized)
    if event_id is not None:
        result["audit_event_id"] = event_id
    return result
```

Update `get_current_user(request: Request, ...)` to set `request.state.current_user_id`. Update permission denial to set `request.state.audit_event_id` after committing its existing audit. Replace the old `IdempotencyKeyReused` handler in `main.py` with `register_audit_exception_handlers(app)`.

- [ ] **Step 5: 运行 GREEN 与认证回归**

Run:

```powershell
D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m pytest codebase/backend/tests/modules/test_task002_audit.py codebase/backend/tests/modules/test_identity_permissions.py -q
```

Expected: PASS; each failed protected write has exactly one persisted failure event.

- [ ] **Step 6: 提交审计切片**

```powershell
git add codebase/backend/app/modules/audit codebase/backend/app/modules/identity/dependencies.py codebase/backend/app/core/idempotency.py codebase/backend/app/main.py codebase/backend/tests/modules
git commit -m "fix(audit): persist protected write failures"
```

---

### Task 3: 固定角色与用户管理

**Files:**
- Create: `codebase/backend/tests/modules/test_task002_identity_admin.py`
- Create: `codebase/backend/app/modules/identity/schemas.py`
- Create: `codebase/backend/app/modules/identity/admin_service.py`
- Modify: `codebase/backend/app/modules/identity/admin_router.py`
- Modify: `codebase/backend/app/modules/identity/bootstrap.py`
- Modify: `codebase/backend/app/modules/identity/router.py`

**Interfaces:**
- Produces: `update_user(db, actor, user_id, payload) -> User`。
- Produces: `update_role_permissions(db, role_id, permission_codes) -> Role`。
- Freezes: fixed roles; no role create/delete endpoint.
- Test helper in this file: `seeded_system_admin(client: TestClient) -> tuple[str, str]` calls `bootstrap_admin()` through `client.app.state.session_factory()`, then logs in and returns `(user_id, token)`.

- [ ] **Step 1: 写固定角色和用户管理 RED 测试**

```python
def test_role_catalog_is_fixed_and_non_admin_permissions_are_editable(client: TestClient) -> None:
    _, token = seeded_system_admin(client)
    headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": "role-update"}
    assert client.post("/api/roles", headers=headers, json={"name": "custom", "permission_codes": []}).status_code == 405
    roles = client.get("/api/roles", headers=headers).json()
    target = next(role for role in roles if role["code"] == "EQUIPMENT_ADMIN")
    response = client.patch(
        f"/api/roles/{target['id']}/permissions",
        headers=headers,
        json={"permission_codes": ["equipment:read", "equipment:write"]},
    )
    assert response.status_code == 200
    assert response.json()["permission_codes"] == ["equipment:read", "equipment:write"]
    assert "audit_event_id" in response.json()


def test_user_cannot_disable_self_or_last_system_admin(client: TestClient) -> None:
    user_id, token = seeded_system_admin(client)
    response = client.patch(
        f"/api/users/{user_id}",
        headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "disable-self"},
        json={"enabled": False, "role_ids": []},
    )
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "USER_SELF_DISABLE_FORBIDDEN"
    assert "audit_event_id" in response.json()["detail"]
```

- [ ] **Step 2: 运行 RED**

Run:

```powershell
D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m pytest codebase/backend/tests/modules/test_task002_identity_admin.py -q
```

Expected: FAIL because custom role creation still exists and user PATCH is missing.

- [ ] **Step 3: 定义请求模型和领域规则**

```python
class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=200)
    role_ids: list[str] = Field(min_length=1)


class UserUpdate(BaseModel):
    enabled: bool
    role_ids: list[str] = Field(min_length=1)


class RolePermissionsUpdate(BaseModel):
    permission_codes: list[str]
```

`admin_service.py` must reject unknown roles/permissions, changes to `SYSTEM_ADMIN` permissions, self-disable, and removal/disable of the last enabled system administrator. It returns domain data; routers own idempotency, success audit and commit.

- [ ] **Step 4: 重写管理路由为完整契约**

Expose GET permissions/roles/users/user detail, POST users, PATCH users, and PATCH role permissions. Remove `RoleCreate` and `POST /roles`. Give writes explicit route names `user.create`, `user.update`, and `role.permissions.update`. Keep every route function below 60 lines by calling `admin_service`.

- [ ] **Step 5: 运行 GREEN 和登录回归**

Run:

```powershell
D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m pytest codebase/backend/tests/modules/test_task002_identity_admin.py codebase/backend/tests/modules/test_identity_permissions.py -q
```

Expected: PASS; password values are absent from responses and audit metadata.

- [ ] **Step 6: 提交身份管理切片**

```powershell
git add codebase/backend/app/modules/identity codebase/backend/tests/modules
git commit -m "feat(identity): complete fixed role user management"
```

---

### Task 4: 组织层级、启停和删除保护

**Files:**
- Create: `codebase/backend/tests/modules/test_task002_organizations.py`
- Create: `codebase/backend/app/modules/equipment/schemas.py`
- Create: `codebase/backend/app/modules/equipment/organization_service.py`
- Modify: `codebase/backend/app/modules/equipment/organization_router.py`

**Interfaces:**
- Produces: `create_organization`、`update_organization`、`delete_organization` domain functions.
- Consumes: `OrganizationType`, fixed ROOT record, audited error handler and idempotency functions.
- Test helpers in this file: `organization_writer_headers()` uses `create_user_token()` with organization read/write permissions; `root_organization()` reads the seeded ROOT; `create_organization_response()` performs one POST with a caller-supplied Key; `create_organization()` asserts 201 and returns JSON; `organization_tree()` creates ROOT/FAC/WS/LINE and returns the three business nodes plus headers.

- [ ] **Step 1: 写组织规则 RED 测试**

```python
def test_organization_hierarchy_and_sibling_rules(client: TestClient) -> None:
    headers = organization_writer_headers(client)
    root = root_organization(client, headers)
    factory = create_organization(client, headers, root["id"], "FACTORY", "FAC-001", "一厂")
    workshop = create_organization(client, headers, factory["id"], "WORKSHOP", "WS-001", "总装")
    line = create_organization(client, headers, workshop["id"], "LINE", "LINE-001", "一线")
    invalid = create_organization_response(client, headers, line["id"], "FACTORY", "FAC-002", "二厂")
    assert invalid.status_code == 422
    assert invalid.json()["detail"]["code"] == "ORGANIZATION_LEVEL_INVALID"
    duplicate = create_organization_response(client, headers, workshop["id"], "LINE", "LINE-002", "一线")
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"]["code"] == "ORGANIZATION_SIBLING_NAME_EXISTS"


def test_disabling_cascades_and_delete_is_protected(client: TestClient) -> None:
    factory, workshop, line, headers = organization_tree(client)
    response = client.patch(
        f"/api/organizations/{factory['id']}",
        headers={**headers, "Idempotency-Key": "disable-factory"},
        json={**factory, "enabled": False},
    )
    assert response.status_code == 200
    nodes = {item["id"]: item for item in client.get("/api/organizations", headers=headers).json()}
    assert not nodes[workshop["id"]]["enabled"] and not nodes[line["id"]]["enabled"]
    blocked = client.delete(f"/api/organizations/{factory['id']}", headers=headers)
    assert blocked.status_code == 409
    assert blocked.json()["detail"]["code"] == "ORGANIZATION_HAS_CHILDREN"
```

- [ ] **Step 2: 运行 RED**

Run:

```powershell
D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m pytest codebase/backend/tests/modules/test_task002_organizations.py -q
```

Expected: FAIL because type/code/status/delete behavior is absent.

- [ ] **Step 3: 实现组织 schema 和 service**

```python
class OrganizationWrite(BaseModel):
    type: OrganizationType
    code: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    parent_id: str
    sort_order: int = Field(ge=0)
    enabled: bool = True
    remark: str = Field(default="", max_length=1000)


ALLOWED_CHILD = {
    OrganizationType.ROOT: OrganizationType.FACTORY,
    OrganizationType.FACTORY: OrganizationType.WORKSHOP,
    OrganizationType.WORKSHOP: OrganizationType.LINE,
}
```

Service operations acquire the existing PostgreSQL advisory transaction lock before reading the tree. Validate fixed ROOT, exact child level, enabled parent, global code and sibling name. Disable descendants iteratively in the same transaction; enabling only updates the selected node. Delete rejects ROOT, children and equipment references.

- [ ] **Step 4: 缩短路由并固定动作名称**

Router exposes list/create/update/delete, delegates rules to `organization_service`, writes success audit and idempotency response, and assigns names `organization.create`, `organization.update`, and `organization.delete`. DELETE has no idempotency cache but always audits success/failure.

- [ ] **Step 5: 运行 GREEN 与旧组织回归**

Run:

```powershell
D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m pytest codebase/backend/tests/modules/test_task002_organizations.py codebase/backend/tests/modules/test_identity_permissions.py -q
```

Expected: PASS; no organization route function exceeds 60 lines.

- [ ] **Step 6: 提交组织切片**

```powershell
git add codebase/backend/app/modules/equipment codebase/backend/tests/modules
git commit -m "feat(organization): enforce approved hierarchy rules"
```

---

### Task 5: 完整设备主数据 API

**Files:**
- Create: `codebase/backend/tests/modules/test_task002_equipment.py`
- Modify: `codebase/backend/app/modules/equipment/schemas.py`
- Create: `codebase/backend/app/modules/equipment/service.py`
- Modify: `codebase/backend/app/modules/equipment/router.py`

**Interfaces:**
- Produces: list/detail/create/update equipment with full SPEC fields.
- Consumes: enabled LINE organization, enabled owner user, audit and idempotency services.
- Test helpers in this file: `valid_equipment_payload()` creates an enabled owner and legal ROOT/FAC/WS/LINE path through the public APIs, then returns the complete payload and writer headers; `invalid_equipment_facts()` additionally creates a disabled LINE and disabled owner and returns their IDs for table-driven validation.

- [ ] **Step 1: 写完整字段和校验 RED 测试**

```python
VALID_EQUIPMENT = {
    "code": "EQ-001", "name": "电驱装载机", "model": "ZL956EV",
    "type": "新能源装载机", "manufacturer": "示例制造商",
    "manufactured_at": "2026-01-10", "commissioned_at": "2026-02-01",
    "operating_hours": 128.5, "status": "NORMAL",
    "organization_id": "replace-with-line-id", "owner_user_id": "replace-with-user-id",
    "image_refs": [{"object_key": "equipment/EQ-001/front.jpg", "filename": "front.jpg"}],
}


def test_equipment_create_read_update_uses_full_contract(client: TestClient) -> None:
    payload, headers = valid_equipment_payload(client)
    created = client.post("/api/equipment", headers=headers, json=payload)
    assert created.status_code == 201
    body = created.json()
    assert {key: body[key] for key in payload} == payload
    assert "audit_event_id" in body
    detail = client.get(f"/api/equipment/{body['id']}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["code"] == payload["code"]


def test_equipment_rejects_non_line_disabled_org_and_disabled_owner(client: TestClient) -> None:
    payload, headers, factory_id, disabled_line_id, disabled_user_id = invalid_equipment_facts(client)
    cases = [
        ({**payload, "organization_id": factory_id}, "EQUIPMENT_ORGANIZATION_NOT_LINE"),
        ({**payload, "organization_id": disabled_line_id}, "EQUIPMENT_ORGANIZATION_DISABLED"),
        ({**payload, "owner_user_id": disabled_user_id}, "EQUIPMENT_OWNER_DISABLED"),
        ({**payload, "operating_hours": -0.01}, "VALIDATION_ERROR"),
    ]
    for index, (case, code) in enumerate(cases):
        response = client.post(
            "/api/equipment",
            headers={**headers, "Idempotency-Key": f"invalid-{index}"},
            json=case,
        )
        assert response.status_code in {409, 422}
        assert response.json()["detail"]["code"] == code
        assert "audit_event_id" in response.json()["detail"]
```

- [ ] **Step 2: 运行 RED**

Run:

```powershell
D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m pytest codebase/backend/tests/modules/test_task002_equipment.py -q
```

Expected: FAIL because the current request and response only expose code/name/organization/enabled.

- [ ] **Step 3: 实现设备 schema 和领域校验**

```python
class ImageRef(BaseModel):
    object_key: str = Field(min_length=1, max_length=500)
    filename: str = Field(min_length=1, max_length=255)


class EquipmentWrite(BaseModel):
    code: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    model: str = Field(min_length=1, max_length=200)
    type: str = Field(min_length=1, max_length=100)
    manufacturer: str = Field(min_length=1, max_length=200)
    manufactured_at: date | None = None
    commissioned_at: date | None = None
    operating_hours: Decimal = Field(ge=0)
    status: EquipmentStatus
    organization_id: str
    owner_user_id: str | None = None
    image_refs: list[ImageRef] = Field(default_factory=list)
```

`equipment.service` validates unique code on create, enabled LINE organization and optional enabled owner. It maps `ImageRef` objects to JSON-safe dictionaries and never accepts content/body/data fields in image references.

- [ ] **Step 4: 实现短路由和完整序列化**

Expose list, detail, create and update. Use explicit names `equipment.create` and `equipment.update`; keep code immutable on update unless the SPEC explicitly includes it in the update body. Translate database uniqueness races to `409 EQUIPMENT_CODE_EXISTS`; successful writes include persisted `audit_event_id` and cache the response in the same transaction.

- [ ] **Step 5: 运行 GREEN 和全模块回归**

Run:

```powershell
D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m pytest codebase/backend/tests/modules/test_task002_equipment.py codebase/backend/tests/modules/test_task002_audit.py codebase/backend/tests/modules/test_identity_permissions.py -q
```

Expected: PASS; equipment router functions are below 60 lines and no attachment body is stored.

- [ ] **Step 6: 提交设备切片**

```powershell
git add codebase/backend/app/modules/equipment codebase/backend/tests/modules
git commit -m "feat(equipment): complete approved master data contract"
```

---

### Task 6: API 契约同步与静态一致性测试

**Files:**
- Modify: `04-architecture-plan/API_SPEC.md`
- Modify: `04-architecture-plan/DATA_MODEL.md`
- Create: `codebase/backend/tests/modules/test_task002_api_contract.py`

**Interfaces:**
- Freezes: TASK-002 endpoints, fields, permissions, error codes, idempotency and audit response semantics.

- [ ] **Step 1: 写 API 文档一致性 RED 测试**

```python
def test_task002_public_routes_are_documented() -> None:
    api_spec = Path("04-architecture-plan/API_SPEC.md").read_text(encoding="utf-8")
    required = {
        "PATCH /api/roles/{role_id}/permissions",
        "PATCH /api/users/{user_id}",
        "DELETE /api/organizations/{organization_id}",
        "GET /api/equipment/{equipment_id}",
        "IDEMPOTENCY_KEY_REUSED",
        "audit_event_id",
    }
    assert all(item in api_spec for item in required)


def test_removed_dynamic_role_route_is_absent(client: TestClient) -> None:
    paths = client.app.openapi()["paths"]
    assert "post" not in paths["/api/roles"]
```

- [ ] **Step 2: 运行 RED**

Run:

```powershell
D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m pytest codebase/backend/tests/modules/test_task002_api_contract.py -q
```

Expected: FAIL because `API_SPEC.md` has no TASK-002 route section.

- [ ] **Step 3: 更新 API_SPEC 和 DATA_MODEL**

Add one canonical TASK-002 section documenting every route from the approved design, request/response fields, permission code, `Idempotency-Key` requirement, error status/code/fields, success audit and failure `audit_event_id`. State that successful responses are replayed, failures are not cached, and Key/body conflicts are audited. Update data model fields, fixed roles, organization hierarchy and explicit TASK-003/TASK-004 deferrals; do not change PRD/SPEC/AC. Record the Stage 3 custom-role controls as stale against FR-010/CR-036 and as a required product-side correction before TASK-010, without modifying prototype source in this backend repair.

- [ ] **Step 4: 运行 GREEN 和完整 Python 回归**

Run:

```powershell
D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m pytest codebase/backend/tests -q
D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m compileall -q codebase/backend/app codebase/backend/alembic
git diff --check
```

Expected: all tests PASS; compileall and diff check exit 0.

- [ ] **Step 5: 提交契约冻结**

```powershell
git add 04-architecture-plan/API_SPEC.md 04-architecture-plan/DATA_MODEL.md codebase/backend/tests/modules/test_task002_api_contract.py
git commit -m "docs(api): freeze complete task-002 contract"
```

---

### Task 7: PostgreSQL、Compose、Review 与正式交接

**Files:**
- Modify: `04-architecture-plan/DEVELOPMENT_TASK_BOOK.md`
- Modify: `05-development/SELF_TEST.md`
- Modify: `05-development/CODE_REVIEW.md`
- Modify: `05-development/CHECKPOINTS.md`
- Modify: `05-development/COMMIT_LOG.md`
- Modify: `06-testing/DEFECTS.md`
- Modify: `workflow/CHANGE_REQUESTS.md`
- Modify: `workflow/DEV_TO_PM_HANDOFF.md`
- Modify: `workflow/state.json`

**Interfaces:**
- Produces: exact new review candidate SHA and reproducible evidence for PR #15.
- Does not mark TASK-002 accepted; DEV-002 review remains the external gate.

- [ ] **Step 1: 在 PostgreSQL 17 验证连续迁移**

Run from repository root:

```powershell
docker compose -p equipment-task2 --env-file codebase/infra/.env.example -f codebase/infra/docker-compose.yml up -d --build postgres redis
docker compose -p equipment-task2 --env-file codebase/infra/.env.example -f codebase/infra/docker-compose.yml run --rm api alembic downgrade 0001
docker compose -p equipment-task2 --env-file codebase/infra/.env.example -f codebase/infra/docker-compose.yml run --rm api alembic upgrade head
docker compose -p equipment-task2 --env-file codebase/infra/.env.example -f codebase/infra/docker-compose.yml run --rm api alembic current
```

Expected: commands exit 0 and final revision is `0002 (head)`. Do not execute `downgrade base`; `0001` is the retained foundation and `0002` downgrade is destructive.

- [ ] **Step 2: 执行完整运行验证**

```powershell
D:\codex\tools\equipment-task1-py313\Scripts\python.exe --version
D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m pytest codebase/backend/tests -q
D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m compileall -q codebase/backend/app codebase/backend/alembic
docker compose --env-file codebase/infra/.env.example -f codebase/infra/docker-compose.yml config --quiet
docker compose -p equipment-task2 --env-file codebase/infra/.env.example -f codebase/infra/docker-compose.yml up -d --build
docker compose -p equipment-task2 --env-file codebase/infra/.env.example -f codebase/infra/docker-compose.yml ps
docker compose -p equipment-task2 --env-file codebase/infra/.env.example -f codebase/infra/docker-compose.yml exec -T api python -c "import json,urllib.request; print(json.load(urllib.request.urlopen('http://127.0.0.1:8000/healthz')))"
git diff --check
```

Expected: Python is `3.13.14`; all tests pass; Compose config exits 0; PostgreSQL and Redis are healthy; API `/healthz` returns `{"status": "ok", "service": "equipment-operations-platform"}`; diff check exits 0.

- [ ] **Step 3: 独立 Review**

Review exact range `53e01e6b9f212c6965414654805979bdd59838ce..HEAD`. Check PRD/SPEC/API field coverage, all failure branches, transaction rollback before audit, exactly-one audit events, idempotency races, migration safety, sensitive data, route/function sizes and absence of TASK-003/TASK-004 scope. Critical/Important findings must be fixed with new RED/GREEN evidence before continuing.

- [ ] **Step 4: 更新正式工件**

Record every command and real result in `SELF_TEST.md`; Review range and findings in `CODE_REVIEW.md`; new remote FCP in `CHECKPOINTS.md`; all new commits in `COMMIT_LOG.md`; PR #15 and TASK-002 as “修复完成、待 DEV-002 复审” in the task book and handoff. Update `CR-036` to `Ready For Verification` and `workflow/state.json` to `READY_FOR_ACCEPTANCE` only after the exact candidate Commit and all mandatory evidence exist. Close or update any newly found defect; do not erase earlier review history.

- [ ] **Step 5: 提交交接候选**

```powershell
git add 04-architecture-plan/DEVELOPMENT_TASK_BOOK.md 05-development 06-testing/DEFECTS.md workflow
git commit -m "docs(task-002): record review remediation handoff"
git rev-parse HEAD
```

Expected: a new exact SHA different from `cfb8ed9`; working tree is clean.

- [ ] **Step 6: 推送并重新请求审核**

```powershell
git push origin codex/task-002-identity-equipment
```

Update PR #15 description/comment with CR-036 scope, exact candidate SHA, test/Compose/migration/health evidence, residual deferrals and rollback note; then request DEV-002 re-review. Do not merge and do not mark TASK-002 accepted until DEV-002 changes the review gate to approved.

---

## 计划自检结果

- 设计第 3—12 节均映射到 Task 1—7，无未覆盖阻断项。
- 新增文件职责单一；路由业务规则分别下沉到身份、组织和设备领域服务。
- 所有生产行为都有先 RED、后 GREEN 的命令和预期结果。
- `RoleCode`、`OrganizationType`、`EquipmentStatus`、路由名和错误响应字段在各任务间一致。
- 未增加生产依赖、兼容层、行级授权或后续任务事实模型。
- 最终状态只到“待 DEV-002 复审”，不越权宣称审核通过或任务接受。
