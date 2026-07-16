# Task 3 Report: Fixed Roles and User Administration

## Status

PASS — TASK-002 CR-036 Task 3 is implemented on `codex/task-002-identity-equipment` from baseline `1c912da`.

## Scope delivered

- Removed dynamic `POST /api/roles`; role catalog exposes only the four `RoleCode` values.
- Added permission catalog, fixed-role catalog, user list/detail/create/update, and role permission update APIs.
- Added `ConfigDict(extra="forbid")` to Task 3 request models and login request model.
- Added protection for fixed `SYSTEM_ADMIN` permissions, self-disable, and removal/disable of the last enabled system administrator.
- Added unknown role/permission/user failures and unified audited failure responses.
- Kept routers responsible for idempotency replay/storage, success audit events, and commit.

## TDD evidence

- RED: `python -m pytest codebase/backend/tests/modules/test_task002_identity_admin.py -q`
  - Result: `7 failed`; expected causes were legacy `POST /roles` returning 201 and missing role-permission/user read-update routes returning 404/405.
- GREEN: same focused command after minimal implementation.
  - Result: `7 passed, 1 warning`.
- Related identity: Task 3 plus `test_identity_permissions.py`.
  - Result: `39 passed, 1 warning`.
- Full backend: `python -m pytest codebase/backend/tests -q`.
  - Initial result: `69 passed, 1 failed`; the sole failure was the obsolete audit route-name assertion for removed `POST /roles`.
  - Final result: `70 passed, 1 warning`.
- Compile: `python -m compileall -q codebase/backend/app` — exit 0.
- Static checks: `git diff --check` — exit 0; all `admin_router.py` route functions are under 60 lines.

The warning is the pre-existing Starlette `TestClient`/httpx deprecation warning.

## Independent acceptance review

- Modified production files: `admin_router.py`, `admin_service.py`, `schemas.py`, `bootstrap.py`, `router.py`.
- Modified/added tests: `test_task002_identity_admin.py`, `test_identity_permissions.py`, `test_task002_audit.py`.
- Compatibility code added: no. Assignment is restricted to the fixed role codes; legacy custom roles are not exposed or assignable.
- New abstraction layers: no general framework; one task-specific domain service and request-schema module were added as required by the brief.
- New dependencies: none.
- Unrelated changes: none observed in the final diff.
- Not verified: PostgreSQL concurrency behavior was not integration-tested; the last-admin query was exercised against SQLite through the backend suite.

## Concerns

- No functional blocker. The existing Starlette/httpx deprecation warning remains outside Task 3 scope.

## Important review fix: system administrator concurrency

- Root cause: `update_user` previously read the target and enabled system administrator count without serializing concurrent transactions. Two administrators could both observe a count of two and each remove the other, leaving zero enabled administrators.
- Fix: every user update now obtains the fixed PostgreSQL transaction advisory lock `IDENTITY_ADMIN_LOCK_ID` before reading the target, requested roles, or enabled administrator count. SQLite explicitly performs no lock SQL.
- RED: focused Task 3 tests produced `3 failed, 7 passed`; all three failures showed the missing `acquire_identity_admin_lock` boundary.
- GREEN: focused Task 3 tests produced `10 passed, 1 warning`.
- Related identity: `42 passed, 1 warning`.
- Full backend: `73 passed, 1 warning`.
- Task 7 remaining verification: run a real PostgreSQL two-transaction concurrency test to prove the advisory lock serializes competing administrator reductions end to end.
