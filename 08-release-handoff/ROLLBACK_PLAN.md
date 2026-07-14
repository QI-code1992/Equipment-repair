# Rollback Plan

Protect current state with a Commit/tag before any release. For a defect, revert the specific release commit or restore selected paths on a rollback branch; do not reset shared history. Validate that the target preserves all accepted features. Re-run affected tests and Stage 6/7 against the new exact SHA.

Current recovery target: `snapshot/legacy-import-20260714` (asset-import snapshot only; not a release target).
