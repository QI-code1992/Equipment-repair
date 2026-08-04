# TASK-005 Live Lifecycle Retest

- Evidence subject: `eca714a6477028c47c5b020b93f96838e266cb03`
- Host: Windows Docker Desktop, Docker Engine `29.6.2`, Compose `v5.3.1`
- External dependency: dedicated RAGFlow instance at the configured host endpoint; the temporary API key was read from the operator-supplied local file and was not stored in Git.
- Isolation: disposable Compose project `equipment-task-005-validation`, dedicated PostgreSQL database, MinIO bucket, temporary TLS directory, and temporary RAGFlow dataset.

## Result

The stack built and started successfully. PostgreSQL migration, API RAGFlow probe, MinIO bucket initialization, ClamAV readiness, Worker startup, Nginx startup, and the live validator all completed. The validator reported `2 passed` (PostgreSQL contract and live lifecycle) and `TASK-005 live validation: PASS`.

The document lifecycle reached `READY`; the success path verified real RAGFlow citations and the unavailable fallback. The disposable Compose project and temporary environment were removed after the run; `docker ps -a` returned no validation containers.

## Prior timeout disposition

The earlier `UPLOADING` timeout on the same merged baseline was not reproduced. No code change was made during this retest, so the prior transient root cause remains unproven. This evidence narrows the reproducibility observation for `DEF-STAGE6-003`, but does not close that defect: the required timestamped segmented trace and unique blocker attribution are still absent. It does not by itself approve Stage 6 or replace the remaining browser, performance, backup/restore, and security evidence.

## Limitations

The stack was cleaned before a post-run HTTPS probe; HTTPS browser E2E and the remaining Stage 6 concurrency/recovery/security runs are separate gates and remain outstanding.
