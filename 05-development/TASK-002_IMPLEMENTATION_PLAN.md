# TASK-002 认证、权限、审计与设备基础实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立可迁移、可撤销会话、按操作权限保护并具备审计与幂等能力的身份和设备基础。

**Architecture:** 使用同步 SQLAlchemy 2.0 模型和 Alembic 管理 PostgreSQL；FastAPI 依赖从 Bearer 会话令牌恢复用户并校验 `resource:action` 权限。写 API 通过同一幂等服务保存响应，通过审计服务写入净化后的事件；组织和设备不做行级授权。

**Tech Stack:** Python 3.13、FastAPI、SQLAlchemy 2.x、Alembic 1.x、psycopg 3、PostgreSQL 17、pytest。

## Global Constraints

- 基线为 `42098613ffa20faed3bb0dcb842a0121722565bd`，分支为 `codex/task-002-identity-equipment`。
- 仅增加获批技术基线中的 SQLAlchemy、Alembic 与 PostgreSQL 驱动，不增加认证框架。
- 不建立 `EquipmentGrant` 或任何工厂/设备行级授权关系。
- 密码使用 Python 标准库 `hashlib.scrypt`；数据库只保存密码摘要和会话令牌摘要。
- 活跃故障设备停用保护归 TASK-003，本任务不预建故障或维修模型。
- 每个生产行为必须先有失败测试并观察到预期失败。

---

### Task 1: 数据库基础、模型与可逆迁移

**Files:**
- Modify: `codebase/backend/pyproject.toml`
- Create: `codebase/backend/alembic.ini`
- Create: `codebase/backend/alembic/env.py`
- Create: `codebase/backend/alembic/versions/0001_identity_equipment_foundation.py`
- Create: `codebase/backend/app/core/database.py`
- Create: `codebase/backend/app/modules/identity/models.py`
- Create: `codebase/backend/app/modules/audit/models.py`
- Create: `codebase/backend/app/modules/equipment/models.py`
- Test: `codebase/backend/tests/modules/test_identity_permissions.py`

**Interfaces:**
- Produces: `Base`, `create_database_engine(database_url: str) -> Engine`, `session_factory(engine: Engine) -> sessionmaker[Session]`。
- Produces: `User`、`Role`、`Permission`、`UserRole`、`RolePermission`、`LoginSession`、`Organization`、`Equipment`、`AuditEvent`、`IdempotencyRecord`。

- [x] **Step 1: 写模型约束失败测试**

```python
def test_equipment_code_is_unique(db_session: Session) -> None:
    db_session.add_all([
        Equipment(code="EQ-001", name="A", organization_id=None),
        Equipment(code="EQ-001", name="B", organization_id=None),
    ])
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_schema_has_no_equipment_grant_table(engine: Engine) -> None:
    assert "equipment_grant" not in inspect(engine).get_table_names()
```

- [x] **Step 2: 运行 RED**

Run: `D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m pytest codebase/backend/tests/modules/test_identity_permissions.py -q`

Expected: collection fails because `app.core.database` and models do not exist.

- [x] **Step 3: 增加数据库依赖和基础接口**

```toml
dependencies = [
  "fastapi>=0.115,<1.0",
  "uvicorn[standard]>=0.34,<1.0",
  "sqlalchemy>=2.0,<3.0",
  "alembic>=1.14,<2.0",
  "psycopg[binary]>=3.2,<4.0",
]
```

```python
class Base(DeclarativeBase):
    pass


def create_database_engine(database_url: str) -> Engine:
    options: dict[str, object] = {"pool_pre_ping": True}
    if database_url == "sqlite+pysqlite:///:memory:":
        options.update(connect_args={"check_same_thread": False}, poolclass=StaticPool)
    return create_engine(database_url, **options)


def session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)
```

- [x] **Step 4: 实现模型与 revision**

Use SQLAlchemy 2 typed mappings. Required database constraints:

```python
class Permission(Base):
    __tablename__ = "permissions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)


class Equipment(Base):
    __tablename__ = "equipment"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    organization_id: Mapped[str | None] = mapped_column(ForeignKey("organizations.id"))
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
```

The revision creates all listed tables and association tables and has a complete `downgrade()` dropping them in reverse foreign-key order.

- [x] **Step 5: 运行 GREEN 与迁移回归**

Run: `D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m pytest codebase/backend/tests/modules/test_identity_permissions.py -q`

Run against Compose PostgreSQL: `docker compose -p equipment-task2 --env-file codebase/infra/.env.example -f codebase/infra/docker-compose.yml up -d postgres`

Run Alembic from the API container attached to the internal Compose network; do not expose a new host database port.

Expected: model tests pass; upgrade creates revision `0001`; downgrade and second upgrade both exit 0.

- [x] **Step 6: 提交数据库基础**

```powershell
git add codebase/backend/pyproject.toml codebase/backend/alembic.ini codebase/backend/alembic codebase/backend/app/core/database.py codebase/backend/app/modules codebase/backend/tests/modules/test_identity_permissions.py
git commit -m "feat(identity): add database foundation"
```

### Task 2: 密码、会话认证与操作权限依赖

**Files:**
- Create: `codebase/backend/app/modules/identity/security.py`
- Create: `codebase/backend/app/modules/identity/service.py`
- Create: `codebase/backend/app/modules/identity/dependencies.py`
- Create: `codebase/backend/app/modules/identity/router.py`
- Modify: `codebase/backend/app/main.py`
- Test: `codebase/backend/tests/modules/test_identity_permissions.py`

**Interfaces:**
- Produces: `hash_password(password: str) -> str`、`verify_password(password: str, encoded: str) -> bool`。
- Produces: `get_current_user(...) -> User`、`require_permission(code: str) -> Callable`。
- Produces: `POST /api/auth/login`、`DELETE /api/auth/session`、`GET /api/auth/me`。

- [x] **Step 1: 写认证与权限 RED 测试**

```python
def test_protected_request_requires_login(client: TestClient) -> None:
    assert client.get("/api/auth/me").status_code == 401


def test_user_without_operation_permission_is_forbidden(client: TestClient, user_token: str) -> None:
    response = client.get("/api/equipment", headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 403


def test_authorized_user_can_read_equipment(client: TestClient, equipment_reader_token: str) -> None:
    response = client.get("/api/equipment", headers={"Authorization": f"Bearer {equipment_reader_token}"})
    assert response.status_code == 200
```

- [x] **Step 2: 运行 RED**

Run: `D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m pytest codebase/backend/tests/modules/test_identity_permissions.py -q`

Expected: routes return 404 because identity router is not registered.

- [x] **Step 3: 实现密码和会话服务**

```python
def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"scrypt$16384$8$1${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    algorithm, n, r, p, salt_hex, digest_hex = encoded.split("$")
    if algorithm != "scrypt":
        return False
    actual = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt_hex), n=int(n), r=int(r), p=int(p))
    return hmac.compare_digest(actual.hex(), digest_hex)
```

Login creates a random `secrets.token_urlsafe(32)` token, stores only `sha256(token).hexdigest()`, and returns the raw token once. Logout sets `revoked_at`; `get_current_user` rejects missing, expired, revoked, or disabled sessions.

- [x] **Step 4: 实现权限依赖和路由注册**

```python
def require_permission(code: str) -> Callable[..., User]:
    def dependency(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
        if code not in permission_codes_for_user(db, user.id):
            raise HTTPException(status_code=403, detail={"code": "PERMISSION_DENIED"})
        return user
    return dependency
```

`create_app()` creates the engine without connecting, stores the session factory on `app.state`, includes identity and equipment routers, and preserves existing `/healthz` behavior.

- [x] **Step 5: 运行 GREEN 和健康回归**

Run: `D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m pytest codebase/backend/tests/modules/test_identity_permissions.py codebase/backend/tests/test_health.py -q`

Expected: authentication tests and all four health tests pass.

- [x] **Step 6: 提交认证切片**

```powershell
git add codebase/backend/app codebase/backend/tests/modules/test_identity_permissions.py
git commit -m "feat(identity): add session authentication and permissions"
```

### Task 3: 组织、设备、审计脱敏与幂等写入

**Files:**
- Create: `codebase/backend/app/modules/audit/service.py`
- Create: `codebase/backend/app/modules/equipment/service.py`
- Create: `codebase/backend/app/modules/equipment/router.py`
- Create: `codebase/backend/app/core/idempotency.py`
- Modify: `codebase/backend/app/main.py`
- Test: `codebase/backend/tests/modules/test_identity_permissions.py`

**Interfaces:**
- Produces: `sanitize_audit_metadata(value: object) -> object`、`write_audit_event(...) -> AuditEvent`。
- Produces: `execute_idempotent(...) -> tuple[int, dict[str, object]]`。
- Produces: protected organization/equipment list and create/update endpoints.

- [x] **Step 1: 写唯一性、审计和幂等 RED 测试**

```python
def test_duplicate_equipment_code_is_rejected(client: TestClient, equipment_writer_headers: dict[str, str]) -> None:
    payload = {"code": "EQ-001", "name": "A", "organization_id": None}
    assert client.post("/api/equipment", json=payload, headers=equipment_writer_headers).status_code == 201
    second = client.post("/api/equipment", json=payload, headers={**equipment_writer_headers, "Idempotency-Key": "second"})
    assert second.status_code == 409
    assert second.json()["detail"]["code"] == "EQUIPMENT_CODE_EXISTS"


def test_same_idempotency_key_replays_response(client: TestClient, equipment_writer_headers: dict[str, str]) -> None:
    payload = {"code": "EQ-002", "name": "B", "organization_id": None}
    first = client.post("/api/equipment", json=payload, headers=equipment_writer_headers)
    second = client.post("/api/equipment", json=payload, headers=equipment_writer_headers)
    assert second.status_code == first.status_code
    assert second.json() == first.json()


def test_audit_metadata_excludes_credentials(db_session: Session) -> None:
    event = db_session.scalars(select(AuditEvent).order_by(AuditEvent.created_at.desc())).first()
    rendered = json.dumps(event.metadata_json)
    assert "password" not in rendered.lower()
    assert "bearer" not in rendered.lower()
```

- [x] **Step 2: 运行 RED**

Run: `D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m pytest codebase/backend/tests/modules/test_identity_permissions.py -q`

Expected: organization/equipment routes are missing or do not enforce idempotency.

- [x] **Step 3: 实现审计净化与幂等服务**

```python
SENSITIVE_KEYS = {"password", "token", "authorization", "cookie", "secret", "api_key"}


def sanitize_audit_metadata(value: object) -> object:
    if isinstance(value, dict):
        return {key: "[REDACTED]" if key.lower() in SENSITIVE_KEYS else sanitize_audit_metadata(item)
                for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize_audit_metadata(item) for item in value]
    return value
```

`execute_idempotent` queries by `(user_id, method, path, key)`, replays the saved status/body when present, and saves the successful response in the same transaction as the audit event and equipment write.

- [x] **Step 4: 实现组织和设备 API**

Create/list/update organization and equipment endpoints. Every protected write requires `Idempotency-Key`; create/update equipment uses `equipment:write`, reads use `equipment:read`, and no query filters by organization membership. Duplicate code returns `409 EQUIPMENT_CODE_EXISTS`. Every successful write includes the persisted `audit_event_id`.

- [x] **Step 5: 运行 GREEN 与完整模块回归**

Run: `D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m pytest codebase/backend/tests/modules/test_identity_permissions.py codebase/backend/tests/test_health.py -q`

Expected: permissions, uniqueness, audit sanitization, idempotency, and health tests pass.

- [x] **Step 6: 提交业务基础切片**

```powershell
git add codebase/backend/app codebase/backend/tests/modules/test_identity_permissions.py
git commit -m "feat(equipment): add audited idempotent master data APIs"
```

### Task 4: Review 整改——引导、完整契约与安全边界

**Files:**
- Create: `codebase/backend/app/modules/identity/bootstrap.py`
- Modify: `codebase/backend/app/modules/identity/admin_router.py`
- Modify: `codebase/backend/app/modules/identity/router.py`
- Modify: `codebase/backend/app/modules/identity/service.py`
- Modify: `codebase/backend/app/modules/identity/dependencies.py`
- Modify: `codebase/backend/app/modules/equipment/router.py`
- Modify: `codebase/backend/app/modules/equipment/organization_router.py`
- Modify: `codebase/backend/app/core/idempotency.py`
- Modify: `codebase/backend/app/modules/audit/models.py`
- Modify: `codebase/backend/app/modules/audit/service.py`
- Modify: `codebase/backend/alembic/versions/0001_identity_equipment_foundation.py`
- Modify: `codebase/backend/Dockerfile`
- Test: `codebase/backend/tests/modules/test_identity_permissions.py`
- Test: `codebase/backend/tests/test_health.py`

**Interfaces:**
- Produces: `bootstrap_admin(db, username, password) -> User`，仅允许空用户库首次引导。
- Produces: permission/role queries, equipment/organization updates, idempotent audited logout.
- Freezes: `(user_id, idempotency_key)` global idempotency ownership and PostgreSQL advisory transaction lock.

- [x] **Step 1: 写首个管理员、查询和更新契约 RED 测试**

Assert that bootstrap creates fixed permissions and an admin able to log in; a second bootstrap is rejected; permission/role queries work; equipment and organization PATCH operations require idempotency and return `audit_event_id`.

- [x] **Step 2: 实现管理员引导和完整管理契约**

The CLI reads `POSTGRES_DSN`, `BOOTSTRAP_ADMIN_USERNAME`, and `BOOTSTRAP_ADMIN_PASSWORD`; it has no default credential and refuses to run when users already exist. Add protected queries and PATCH endpoints without row-level filtering.

- [x] **Step 3: 写登录/拒绝/登出审计和脱敏 RED 测试**

Assert login success/failure and permission denial create audit events; logout requires `Idempotency-Key`, returns `audit_event_id`, and replays after the token is revoked; keys such as `access_token`, `password_hash`, and Bearer strings are redacted.

- [x] **Step 4: 实现安全审计与恒定密码校验路径**

Use a dummy scrypt hash for unknown/disabled users, audit login and denial outcomes, and make logout resolve its session before revoked-state rejection so a saved response can replay.

- [x] **Step 5: 写全局幂等键和数据库竞态 RED 测试**

Assert reusing one key on another path returns `409 IDEMPOTENCY_KEY_REUSED`; verify PostgreSQL lock acquisition is called before lookup; duplicate database constraints are translated to stable 409 errors.

- [x] **Step 6: 实现全局键所有权、事务锁和唯一冲突映射**

Make `(user_id, idempotency_key)` unique, store method/path, acquire `pg_advisory_xact_lock` on PostgreSQL, reject mismatched target reuse, and catch `IntegrityError` around commits with rollback and stable 409 responses.

- [x] **Step 7: 修复两个 Minor 并执行回归**

Use explicit `DateTime(timezone=True)` for audit timestamps and `onupdate=utc_now` for `User.updated_at`; run all backend tests and migration upgrade/downgrade/upgrade.

- [x] **Step 8: 提交 Review 整改**

```powershell
git add codebase/backend 05-development/TASK-002_IMPLEMENTATION_PLAN.md
git commit -m "fix(identity): close bootstrap audit and idempotency gaps"
```

### Task 5: PostgreSQL 联调、契约冻结与正式交接

**Files:**
- Modify: `05-development/SELF_TEST.md`
- Modify: `05-development/CODE_REVIEW.md`
- Modify: `05-development/CHECKPOINTS.md`
- Modify: `05-development/COMMIT_LOG.md`
- Modify: `04-architecture-plan/DEVELOPMENT_TASK_BOOK.md`
- Modify: `workflow/DEV_TO_PM_HANDOFF.md`

**Interfaces:**
- Freezes: authentication dependency, permission code format, model/table names, audit fields, migration revision and TASK-003/TASK-006 consumption boundary.

- [x] **Step 1: 在真实 PostgreSQL 执行迁移升级/降级/升级**

Run within the API container or a temporary Python 3.13 container attached to `equipment-task2_platform`:

```powershell
alembic -c codebase/backend/alembic.ini upgrade head
alembic -c codebase/backend/alembic.ini downgrade base
alembic -c codebase/backend/alembic.ini upgrade head
```

Expected: all commands exit 0; the final current revision is `0001`.

- [x] **Step 2: 执行完整验证**

```powershell
D:\codex\tools\equipment-task1-py313\Scripts\python.exe -m pytest codebase/backend/tests -q
docker compose --env-file codebase/infra/.env.example -f codebase/infra/docker-compose.yml config --quiet
git diff --check
```

Expected: all backend tests pass, Compose config exits 0, and diff check exits 0.

- [x] **Step 3: 独立 Review**

Review exact range from the design commit through the final implementation commit. Reject Critical/Important findings before proceeding; record Minor findings and disposition.

- [x] **Step 4: 更新正式工件**

Record exact commands/results, migration revision, remote commits, FCP recovery point, no compatibility code, no extra abstraction, no unrelated changes, residual warning, rollback via application revert plus tested Alembic downgrade, and DEV-002 authentication-context handoff.

- [x] **Step 5: 提交并推送**

```powershell
git add 04-architecture-plan/DEVELOPMENT_TASK_BOOK.md 05-development workflow/DEV_TO_PM_HANDOFF.md
git commit -m "docs(task-002): record identity foundation handoff"
git push origin codex/task-002-identity-equipment
```

Expected: remote branch HEAD equals the local final handoff commit; PR target remains `codex/stage-05-integration`.
