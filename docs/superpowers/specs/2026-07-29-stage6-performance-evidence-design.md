# Stage 6 Performance Evidence Design

## Goal

Make the PR #63 Agent-success performance evidence prove that every returned
RAGFlow citation belongs to the one controlled document and chunk fixture;
make the dynamic test records, security rescans, report, and PR description
traceable to the reviewed candidate.

## Design

The Agent response will expose `document_id` and `chunk_id` for each evidence
item. The performance harness accepts the expected document/chunk pair and
marks a successful response invalid unless every evidence item matches that
pair, in addition to the existing non-empty text and marker checks. Result
metadata records the expected pair and level statistics record fixture-pair
binding.

`TEST_PLAN.md` and `TEST_CASES.md` will explicitly define the four dynamic
performance scenarios and the restore-time read-only scenario, including
fixture, thresholds, evidence artifact, and execution status. Fresh CodeQL,
Semgrep, Gitleaks, and Trivy artifacts will identify the SUT, evidence commit,
tool version, command, and result. The report and PR body will cite the new
evidence commit without declaring Stage 6 passed.

## Constraints

- Keep PR #63 Draft; do not request merge authorization, merge, or enter Stage 7.
- Add no production dependency, compatibility branch, or unrelated refactor.
- Re-run only the checks necessary for the changed harness, Agent response,
  documentation, and security evidence.
