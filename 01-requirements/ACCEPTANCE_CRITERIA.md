# Acceptance Criteria

- Baseline: Candidate v1.0
- Status: Awaiting Stage 1 user approval
- Format: Given / When / Then

## Account, permission and audit

### AC-001 Login
Given an active user with valid credentials, when they submit login, then the system opens only authorized menus.

### AC-002 Disabled account
Given a disabled account, when it submits login, then access is denied and no session is created.

### AC-003 Agent permission
Given a user without AI floating-Agent permission, when any business page loads, then no Agent entry is shown or callable.

### AC-004 Fault permission
Given a user with Agent permission but without fault-report permission, when they request an AI draft, then the Agent explains the restriction and creates no draft.

### AC-005 Audit
Given an administrator changes a permission or equipment owner, when save succeeds, then an audit event records actor, action, target, time and result.

## Equipment and knowledge

### AC-006 Equipment create
Given required equipment fields are valid, when the user saves, then a unique equipment record is created.

### AC-007 Duplicate equipment code
Given an existing equipment code, when another record uses it, then save is blocked with a field-level error.

### AC-008 Deactivation guard
Given an equipment has a pending or repairing fault, when a user attempts to deactivate it, then the operation is blocked with the active-fault reason.

### AC-009 Knowledge failure
Given a document fails parsing or indexing in RAGFlow, when an Agent searches knowledge, then the failed document is absent from citations and its failure reason is visible to an authorized operator.

## Fault and Agent

### AC-010 Manual validation
Given a manual fault form lacks equipment, urgency or symptom, when submit is pressed, then submission is blocked and each missing field is identified.

### AC-011 AI equipment scope
Given the Agent fault flow, when the user selects multiple equipment, then the Agent rejects the selection and requests exactly one equipment.

### AC-012 AI preview
Given required AI fault fields are complete, when the user requests preview, then a readonly structured preview is shown and optional omissions are disclosed once.

### AC-013 AI draft submit
Given a readonly preview is confirmed, when draft creation succeeds, then an AI draft number appears in the fault page and remains editable there before formal submit.

### AC-014 Fault status
Given an AI draft is formally submitted, when the business API succeeds, then status becomes pending acceptance, and the record transitions only through pending acceptance, in repair and processed.

### AC-015 Attachment failure
Given a valid text collection and an attachment upload failure, when the Agent continues, then text is retained and the attachment failure is retryable.

## Intelligent query and health

### AC-016 Fixed metric catalog
Given the metric catalog page, when an authorized user views it, then all 40 built-in metrics show name, definition, formula, period, dimensions and examples, with no create/edit/delete/enable/disable/version controls.

### AC-017 Metric query
Given a query uses a catalog metric and allowed dimensions, when the backend returns data, then the Agent summarizes the returned values and states the query period.

### AC-018 Metric restriction
Given an unknown metric or disallowed dimension, when a query is submitted, then the backend rejects it and the Agent does not invent a result.

### AC-019 Query failure
Given a previous successful result, when the next query API fails, then the previous result remains visible with a not-updated error and retry action.

### AC-020 Health service consistency
Given workbench, BI, ledger, equipment detail and intelligent query request health data, when the service responds, then all surfaces show the same score, grade, period and components.

### AC-021 Health service failure
Given health calculation fails, when a page renders, then it shows calculation failure and no cached, zero or empty score.

### AC-022 Score launch baseline
Given an equipment existed before formal launch, when the health service initializes it, then the internal baseline is 100 and pre-launch events are excluded from scoring and the public timeline.

### AC-023 Score snapshot
Given a score or component changes, when calculation completes, then one snapshot records before/after values, trigger, deductions/recoveries, references and calculation time.

## Diagnosis, work order and maintenance

### AC-024 Diagnosis evidence
Given a complete fault, when diagnosis returns, then it shows fault type, risk, possible causes, confidence and RAG citations.

### AC-025 Safety review
Given a high-voltage or brake-related fault or low confidence, when advice is shown, then safety/stop-work guidance and human-review status are visible.

### AC-026 Draft work order
Given a repair recommendation, when a draft is generated, then it cannot be dispatched until an equipment administrator confirms it.

### AC-027 Work-order close
Given a work order lacks actual cause, actual solution or repair result, when close is attempted, then close is blocked.

### AC-028 Knowledge sedimentation
Given a work order closes with complete repair data, when sedimentation runs, then a historical case or review-needed knowledge entry is created.

## Resilience and repeated operations

### AC-029 Agent outage fallback
Given Agent or RAGFlow is unavailable, when a user reports a fault, then manual reporting remains available and the unavailable capability is explained.

### AC-030 Repeated submit
Given a fault or work-order submit request has already succeeded, when the same request is retried with the same idempotency key, then no duplicate business record is created.

### AC-031 Empty/loading/error states
Given any P0 list or dashboard page, when data is empty, loading, or fails, then the corresponding state is explicit and offers the permitted next action.
