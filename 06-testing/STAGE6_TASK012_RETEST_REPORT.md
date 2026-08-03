# Stage 6 TASK-012 Isolated Retest Report

- Evidence subject commit: `6fbb9e5be6267851482fda425c704acdada92c50`
- Target: `codex/stage-05-integration`
- Environment: Windows Docker Desktop 4.83.0, Docker Engine 29.6.2, Compose v5.3.1
- Date: 2026-08-03
- Status: **NOT PASSED; Stage 7 remains locked**

## Passed

- `docker compose ... config --quiet` passed.
- Isolated Compose stack started with PostgreSQL 17, Redis 7, MinIO, ClamAV, API, Worker, Validator and Nginx.
- Alembic migration to `0006_task005` passed on a dedicated validation database.
- PostgreSQL, Redis, MinIO and ClamAV reported healthy.
- API-container RAGFlow probe authenticated successfully against the temporary RAGFlow service.
- HTTPS `GET /healthz` returned HTTP 200; Nginx served JavaScript as `application/javascript` and CSS as `text/css` during the stack run.
- API restart recovered and `/healthz` returned HTTP 200 after restart.
- Python 3.13 backend: `333 passed, 13 skipped, 2 warnings`.
- Frontend: `65 passed`; `npm run build` passed.
- Node static regression: `15 passed`; compileall, workflow JSON parsing and diff checks passed.

## Failed or Incomplete

- `tests/integration/test_task005_live_stack.py` did not produce a valid pass on this SUT. The first run failed because the dedicated database was not initialized; after creating the dedicated database, initializing the MinIO bucket and rerunning, the test exceeded the 180-second execution limit without a result. No live lifecycle PASS is claimed.
- Browser E2E could not be completed in the in-app browser. The browser rejected the disposable local certificate with `ERR_CERT_AUTHORITY_INVALID`; the certificate was removed after the attempt. Command-line HTTPS checks do not substitute for browser E2E.
- The required 1/2/5/10 concurrency performance reruns, backup/restore, and read-only load during recovery were not completed in this run.
- Windows validation host did not have CodeQL or Semgrep. A separate, read-only scan of the same exact SUT completed on macOS; its raw SARIF/JSON artifacts are included below. This does not replace the Windows live-stack evidence.

## Security Scan Results

Artifacts are stored under `06-testing/security-artifacts/6fbb9e5be6267851482fda425c704acdada92c50/`.

- Gitleaks working-tree and full-history scans each reported the same two historical `curl-auth-user` findings in `codebase/infra/ragflow/scripts/verify-persistence.ps1` (commits `8af62abe...` and `0ff29ed...`). Secret values are not copied into this report.
- Trivy completed with no secret findings. It reported HIGH `GHSA-qwww-vcr4-c8h2` in `codebase/frontend/package-lock.json` and LOW `DS-0026` for the backend Dockerfile healthcheck configuration. These remain open risk items and are not marked remediated.
- CodeQL scanned 142 Python files. It returned 63 quality findings (unused imports/variables and ineffectual statements) and no security-query finding. JavaScript/TypeScript security-extended scanning returned 19 findings: one identity-replacement and 18 DOM-XSS alerts, all in the Stage 3 static prototype (`03-ui-prototype/prototype/`), not in `codebase/frontend`. They remain prototype-scope findings and must not be represented as production-frontend findings.
- Semgrep `p/default` scanned 281 tracked files with 520 applicable rules and returned 15 findings. Two are ERROR severity: the explicitly opt-in `--insecure-tls` performance-harness path and a Dockerfile root-process heuristic. The Dockerfile finding is not yet a confirmed production defect because its final `production` stage declares `USER appuser`; a live `id -u` check is required. It also reports dynamic URL/proxy warnings requiring boundary review, plus five partial-parser warnings; the raw JSON records the affected files and parser limits.

## Gate Decision

This report is bound to `6fbb9e5...` and records reproducible evidence, including failures and missing tools. Stage 6 is **not approved**. The project owner must decide remediation/acceptance for the live lifecycle timeout, browser trust setup, performance and recovery evidence, scanner findings, and Trivy/Gitleaks findings before any Stage 6 gate recommendation. Stage 7 and release work remain locked.
