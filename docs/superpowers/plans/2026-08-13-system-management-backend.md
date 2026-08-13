# System Management Backend Implementation Plan

**Goal:** Complete the approved role, user, session, and audit-read backend gaps.

**Architecture:** Extend the existing FastAPI identity and audit modules, preserving built-in system-administrator protection while allowing enabled custom roles. One Alembic revision adds role metadata and user profile fields; login and audit lists are derived from immutable audit events.

## Work Packages

1. Update API/data contracts and CR record for custom roles, user profile/organization, reset-password, and audit reads.
2. Add migration and ORM/schema support; write role lifecycle route tests before implementation.
3. Add user profile, organization filtering, reset-password/session revocation tests and implementation.
4. Add permission-protected login-event and audit-event read APIs with stable filtering/pagination tests and implementation.
5. Run backend suite, compile, frontend contract suite/build, and diff check; prepare ECS manual-migration handoff.
