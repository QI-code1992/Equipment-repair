# Stage 6 Performance Evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bind Agent-success performance evidence to a fixture document/chunk pair and restore the missing test and security audit trail.

**Architecture:** The API exposes the identifiers already carried by `KnowledgeCitation`; the harness compares them with explicit expected values. JSON evidence and written test records retain the same identifiers and scan provenance.

**Tech Stack:** FastAPI/Pydantic response models, Python 3.13 unittest harness, Markdown, CodeQL, Semgrep, Gitleaks, Trivy.

## Global Constraints

- No new production dependency, compatibility layer, merge authorization, merge, or Stage 7 transition.
- Every regenerated performance/security artifact records SUT and evidence commit.

---

### Task 1: Fixture-pair response and harness contract

**Files:**
- Modify: `codebase/backend/app/modules/agents/router.py`
- Modify: `codebase/backend/tests/agents/test_operation_guidance.py`
- Modify: `06-testing/performance/stage6_performance.py`
- Modify: `06-testing/performance/test_stage6_performance.py`

- [ ] Write a failing API assertion for evidence `{document_id, chunk_id}` and a harness assertion that a matching marker with a mismatched ID pair is invalid.
- [ ] Run the focused backend and harness tests; confirm the new assertions fail because the API omits `document_id` and the harness does not compare the pair.
- [ ] Preserve the identifiers from `KnowledgeCitation` in the response and require the harness `--expected-document-id` plus `--expected-chunk-id` for fixture-bound Agent-success runs.
- [ ] Re-run the focused tests; confirm all pass.

### Task 2: Performance evidence and test records

**Files:**
- Modify: `06-testing/performance/results-agent-success-final-v2.json`
- Modify: `06-testing/TEST_PLAN.md`
- Modify: `06-testing/TEST_CASES.md`
- Modify: `06-testing/TEST_REPORT.md`

- [ ] Regenerate or update the Agent-success metadata with the expected document/chunk pair and pair-binding counts.
- [ ] Add dynamic performance and restore-time read-only cases with fixture, thresholds, result artifact, and executed status.
- [ ] Align the report with the pair contract and the explicit test cases.
- [ ] Parse the JSON and run the harness tests.

### Task 3: Current-SUT security evidence and PR description

**Files:**
- Create: `06-testing/security-artifacts/<evidence-commit>/metadata.json`
- Create: `06-testing/security-artifacts/<evidence-commit>/*`
- Modify: `06-testing/TEST_REPORT.md`

- [ ] Run CodeQL, Semgrep, Gitleaks, and Trivy against the current candidate; archive sanitized results with SUT, evidence commit, tool version, command, and outcome.
- [ ] Update the report to point at the fresh artifact directory and preserve any unresolved, approved risks.
- [ ] Update PR #63 body to cite the new evidence HEAD while retaining Draft and Stage 7 restrictions.
- [ ] Run JSON parsing, `git diff --check`, and the focused tests before publishing.
