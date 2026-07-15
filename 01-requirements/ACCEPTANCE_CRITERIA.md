# Acceptance Criteria

- Baseline: Approved v1.1
- Status: Stage 1 approved; see Gate-002 in `workflow/STAGE_APPROVALS.md`
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

## 故障与 Agent

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

## 智能问数与健康分

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

## 诊断、工单与维修

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

## 容错与重复操作

### AC-029 Agent outage fallback
Given Agent or RAGFlow is unavailable, when a user reports a fault, then manual reporting remains available and the unavailable capability is explained.

### AC-030 Repeated submit
Given a fault or work-order submit request has already succeeded, when the same request is retried with the same idempotency key, then no duplicate business record is created.

### AC-031 Empty/loading/error states
Given any P0 list or dashboard page, when data is empty, loading, or fails, then the corresponding state is explicit and offers the permitted next action.

## AI 集成与交付基线

### AC-032 Missing model configuration
Given chat, Embedding or Rerank configuration is missing, when the AI health check runs, then it fails explicitly and no pseudo-answer is generated.

### AC-033 Citation integrity
Given a knowledge search returns results, when an Agent uses knowledge content, then every cited item includes a business document ID and chunk identifier; an empty result is stated as no citable evidence.

### AC-034 Agent thread isolation
Given two users create Agent threads, when either user reads or resumes a thread, then only the creator or system administrator can access it and the other user receives no messages, citations or business details.

### AC-035 Interrupt recovery
Given an AI fault report lacks occurrence time or duration, when the Agent interrupts, then the user can provide the missing fields and resume the same `thread_id`; formal submission remains blocked until explicit confirmation.

### AC-036 Tool boundary
Given an Agent attempts a non-allowlisted operation such as direct SQL, health-score write, user mutation or filesystem execution, when the request is evaluated, then it is rejected and audited.

### AC-037 Authorization detail protection
Given an Agent requests an equipment outside the current user's grant, when the backend checks the request, then it rejects the request without returning that equipment's business details.

### AC-038 Audit redaction
Given an Agent call completes or fails, when its audit event is stored, then tool/model/citation/timing/result/error metadata is traceable while secrets, passwords, cookies, tokens and sensitive attachment contents are absent.

### AC-039 Logout navigation
Given a signed-in user opens the global user menu, when the user confirms “退出登录”, then the session is ended for the prototype flow and the browser returns to `login.html`; cancelling keeps the current page and menu state closed.

## 接单前诊断 Agent

### AC-040 动态诊断追问
Given different equipment systems or different fault phenomena, when the repair Agent starts diagnosis, then it asks system-specific evidence questions and shows matching suggestions rather than a universal fixed sequence.

### AC-041 报警码必填追问
Given a user selects “有报警码”, when the Agent asks for the code, then the composer enters a required alarm-code mode and does not advance until a concrete code is entered or “暂无报码/未读取” is explicitly selected.

### AC-042 证据不足保护
Given the user only provides negative, missing or unverified information, when diagnosis continues, then the Agent requests another verifiable datum and does not generate a root-cause adoption action.

### AC-043 采纳与直接开始边界
Given diagnosis is ready, when the user adopts the AI suggestion, then end-repair fields and a readonly evidence-based summary are prefilled; when the user directly starts repair, then no AI summary or prefill is shown at end repair.

### AC-044 Agent 降级
Given the diagnosis Agent is disabled, incomplete, timed out or failed, when start repair opens, then the page explains that AI diagnosis is unavailable and preserves direct manual start repair.
