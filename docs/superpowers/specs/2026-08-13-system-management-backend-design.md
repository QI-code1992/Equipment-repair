# System Management Backend Design

Approved by the project owner on 2026-08-13. Built-in roles remain protected; custom roles are mutable only while unbound. User deletion is not exposed: disabling is the supported lifecycle. Every protected write requires `identity:write`, an idempotency key, and success/failure audit. Log reads require `system:audit`. This change requires a manual ECS migration deployment with backup and smoke testing.
