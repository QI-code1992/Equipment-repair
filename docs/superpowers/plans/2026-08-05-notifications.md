# Notifications Backend Implementation Plan

> **For agentic workers:** Implement task-by-task with TDD and verify each slice before committing.

**Goal:** Add authenticated notification persistence and read-state APIs for the shared shell.

**Architecture:** Global notification records are stored separately from per-user read markers. FastAPI routes query the current user through the existing identity dependency and use SQLAlchemy sessions; Alembic adds the PostgreSQL-compatible schema.

**Tech Stack:** FastAPI, SQLAlchemy 2, Alembic, PostgreSQL/SQLite test database, pytest.

## Global Constraints

- Reuse existing authentication; no notification-specific permission.
- Do not add dependencies or modify public contracts outside the notification endpoints.
- Keep credentials and business mock data out of production code.

### Task 1: Contract Tests

**Files:** Create `codebase/backend/tests/modules/test_notifications_api.py`.

- [ ] Add tests for unauthenticated access, list/unread count, user isolation, single-read idempotency, and read-all isolation.
- [ ] Run the new test file and confirm failures are caused by missing notification routes.

### Task 2: Models and Routes

**Files:** Create `codebase/backend/app/modules/notifications/models.py`, `schemas.py`, `router.py`; modify `app/main.py` and `alembic/env.py`.

- [ ] Implement the two SQLAlchemy tables and authenticated route handlers.
- [ ] Run the notification tests until green.

### Task 3: Migration and Verification

**Files:** Create `codebase/backend/alembic/versions/0007_task013_notifications.py`.

- [ ] Add upgrade/downgrade operations matching the models and indexes.
- [ ] Run focused backend tests, migration checks, and `git diff --check`.
- [ ] Commit the stable backend slice.
