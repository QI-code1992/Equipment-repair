export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string | null,
  ) {
    super(code ?? `HTTP_${status}`);
  }
}

const accessTokenStorageKey = "access_token";

function withAuthorization(init?: RequestInit, useSession = true): RequestInit | undefined {
  const token = window.sessionStorage.getItem(accessTokenStorageKey);
  if (!useSession || !token) return init;
  const headers = new Headers(init?.headers);
  headers.set("Authorization", `Bearer ${token}`);
  return { ...init, headers };
}

export async function requestJson<T>(path: string, init?: RequestInit, useSession = true): Promise<T> {
  const response = await fetch(path, withAuthorization(init, useSession));

  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: { code?: string } } | null;
    throw new ApiError(response.status, body?.detail?.code ?? null);
  }

  return response.json() as Promise<T>;
}

export function hasActiveSession() {
  return Boolean(window.sessionStorage.getItem(accessTokenStorageKey)?.trim());
}

export function clearActiveSession() {
  window.sessionStorage.removeItem(accessTokenStorageKey);
}

export type CurrentUser = { id: string; username: string; enabled: boolean; permission_codes: string[] };
export const getCurrentUser = () => requestJson<CurrentUser>("/api/auth/me");

export async function login(username: string, password: string) {
  const response = await requestJson<{ access_token: string }>("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  }, false);
  window.sessionStorage.setItem(accessTokenStorageKey, response.access_token);
}

export async function logout() {
  try {
    await requestJson<unknown>("/api/auth/session", {
      method: "DELETE",
      headers: { "Idempotency-Key": crypto.randomUUID() },
    });
  } finally {
    clearActiveSession();
  }
}

export type DeepThinkingLevel = "low" | "medium" | "high";

export type FaultReportCreate = {
  equipment_id: string;
  urgency: string;
  symptom: string;
  occurred_at: string;
  possible_location?: string;
  description?: string;
  attachment_refs: Array<{ object_key: string; filename: string; size_bytes: number; content_type: string }>;
};

export type FaultReport = FaultReportCreate & { id: string; number: string; status: string };
export type AttachmentRef = { object_key: string; filename: string; size_bytes: number; content_type: string };

export type AgentFaultDraft = FaultReportCreate & { duration_minutes: number };
export type AgentFaultPreview = { agent_status: "PREVIEW"; draft: AgentFaultDraft; missing_fields: string[] };
export type AgentFaultSubmission = (FaultReport & { agent_status: string }) | AgentFaultPreview;

export type HealthScore = { status: string; score?: number };

export type StartRepairRequest =
  | { mode: "DIRECT"; diagnosis_draft_id?: never }
  | { mode: "ADOPTED"; diagnosis_draft_id: string };

export type RepairStart = {
  work_order_id: string;
  maintenance_record_id: string;
  start_mode: "DIRECT" | "ADOPTED";
  diagnosis_draft_id: string | null;
};

export type RepairResult = {
  actual_cause: string;
  actual_solution: string;
  repair_result: string;
  parts_replacement_notes?: string;
};

export type DiagnosisResponse = {
  state: "OPEN_LOADING" | "QUESTIONING" | "EVIDENCE_PENDING" | "DIAGNOSIS_READY" | "UNAVAILABLE";
  question: string | null;
  evidence: Array<{ category: string; detail: string }>;
  prefill: Record<string, unknown> | null;
  summary: Record<string, unknown> | null;
  steps: number;
  questions: number;
  diagnosis_draft_id: string | null;
};

export type GuidanceResponse = {
  state: "QUESTIONING" | "NO_EVIDENCE" | "UNAVAILABLE";
  question: string | null;
  evidence: Array<{ document_id: string; chunk_id: string; citation: string; text: string }>;
  manual_fallback: boolean;
  loading_seconds: number;
};

export type RuntimeEvent = { event: string; data: Record<string, unknown> };

export async function uploadAttachment(file: File): Promise<AttachmentRef> {
  const headers = new Headers();
  const token = window.sessionStorage.getItem(accessTokenStorageKey);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  headers.set("Idempotency-Key", crypto.randomUUID());
  const body = new FormData();
  body.append("file", file);
  const response = await fetch("/api/attachments", { method: "POST", headers, body });
  if (!response.ok) {
    const payload = await response.json().catch(() => null) as { detail?: { code?: string } } | null;
    throw new ApiError(response.status, payload?.detail?.code ?? null);
  }
  return response.json() as Promise<AttachmentRef>;
}

function postJson<T>(path: string, body: unknown): Promise<T> {
  return requestJson<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json", "Idempotency-Key": crypto.randomUUID() },
    body: JSON.stringify(body),
  });
}

export function createFaultReport(payload: FaultReportCreate) {
  return postJson<FaultReport>("/api/fault-reports", payload);
}

export function submitAgentFaultReport(payload: { draft: AgentFaultDraft; confirmed: boolean }) {
  return postJson<AgentFaultSubmission>("/api/agent/fault-reports/submit", payload);
}

export function getHealthScore(equipmentId: string) {
  return requestJson<HealthScore>(`/api/agent/health-score/${equipmentId}`);
}

export function startRepair(faultId: string, payload: StartRepairRequest) {
  return postJson<RepairStart>(`/api/fault-reports/${faultId}/start-repair`, payload);
}

export function completeRepair(workOrderId: string, payload: RepairResult) {
  return postJson<RepairResult>(`/api/work-orders/${workOrderId}/repair-result`, payload);
}

export function getOperationGuidance(payload: {
  equipment_id: string;
  equipment_model: string;
  symptom: string;
  description: string;
  dataset_ids?: string[];
}) {
  return postJson<GuidanceResponse>("/api/agent/operation-guidance", payload);
}

export function runFaultDiagnosis(payload: {
  action: "start" | "answer" | "evidence";
  fault_report_id?: string;
  alarm_code_present?: boolean;
  diagnosis_draft_id?: string;
  answer?: string;
  category?: string;
  detail?: string;
}) {
  return postJson<DiagnosisResponse>("/api/agent/fault-diagnosis", payload);
}

export async function readRunEvents(runId: string): Promise<RuntimeEvent[]> {
  const response = await fetch(`/api/agent/runs/${runId}/events`, withAuthorization());
  if (!response.ok || !response.body) throw new ApiError(response.status, null);
  const text = await response.text();
  return text.split("\n\n").flatMap((block) => {
    const event = block.match(/^event: (.+)$/m)?.[1];
    const data = block.match(/^data: (.+)$/m)?.[1];
    if (!event || !data) return [];
    try {
      return [{ event, data: JSON.parse(data) as Record<string, unknown> }];
    } catch {
      return [];
    }
  });
}

export async function startAgentRun(agentId: string, businessContext: Record<string, unknown>, text: string) {
  const thread = await postJson<{ thread_id: string }>("/api/agent/threads", {
    agent_id: agentId,
    business_context: businessContext,
  });
  const run = await postJson<{ run_id: string }>(`/api/agent/threads/${thread.thread_id}/messages`, { text, attachment_refs: [] });
  return { thread_id: thread.thread_id, run_id: run.run_id };
}

export type AgentThread = { thread_id: string; agent_id: string; status: string; messages: Array<Record<string, unknown>>; runs: Array<{ run_id: string; status: string; state: Record<string, unknown> }> };
export type AgentThreadSummary = { thread_id: string; agent_id: string; status: string; created_at: string; updated_at: string };
export const getAgentThreads = () => requestJson<{ items: AgentThreadSummary[]; count: number }>("/api/agent/threads");
export const getAgentThread = (threadId: string) => requestJson<AgentThread>(`/api/agent/threads/${threadId}`);
export const resumeAgentThread = (threadId: string, payload: { resume: boolean; confirmation: Record<string, unknown> }) => postJson<{ run_id: string; thread_id: string; status: string }>(`/api/agent/threads/${threadId}/resume`, payload);

export type AgentConfig = {
  agent_id: string;
  enabled: boolean;
  model_binding_id: string | null;
  knowledge_dataset_ids: string[];
  streaming_enabled: boolean;
  suggestions_enabled: boolean;
  sources_enabled: boolean;
  context_turns: number;
  retrieval_limit: number;
  similarity_threshold: number;
  deep_thinking_enabled: boolean;
  deep_thinking_level: DeepThinkingLevel;
  max_reply_tokens: number;
  model_capability: {
    binding_id: string;
    display_name: string;
    supports_reasoning: boolean;
  } | null;
};

export type ModelProvider = { id: string; name: string; enabled: boolean };
export type ModelProviderWrite = { name: string; secret_ref: string; enabled: boolean };
export type ModelBinding = {
  id: string;
  provider_id: string;
  name: string;
  model_name: string;
  supports_reasoning: boolean;
  enabled: boolean;
};
export type ModelBindingWrite = Omit<ModelBinding, "id">;

export async function getAgentConfigs(): Promise<AgentConfig[]> {
  return requestJson<AgentConfig[]>("/api/agent-configs");
}

export async function getAgentConfig(agentId: string): Promise<AgentConfig> {
  return requestJson<AgentConfig>(`/api/agent-configs/${agentId}`);
}

export async function saveAgentConfig(config: Omit<AgentConfig, "model_capability">): Promise<AgentConfig> {
  return requestJson<AgentConfig>(`/api/agent-configs/${config.agent_id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      "Idempotency-Key": crypto.randomUUID(),
    },
    body: JSON.stringify(config),
  });
}

function putJson<T>(path: string, body: unknown): Promise<T> {
  return requestJson<T>(path, {
    method: "PUT",
    headers: { "Content-Type": "application/json", "Idempotency-Key": crypto.randomUUID() },
    body: JSON.stringify(body),
  });
}

function deleteJson<T>(path: string): Promise<T> {
  return requestJson<T>(path, {
    method: "DELETE",
    headers: { "Idempotency-Key": crypto.randomUUID() },
  });
}

export const getModelProviders = () => requestJson<ModelProvider[]>("/api/model-providers");
export const createModelProvider = (body: ModelProviderWrite) => postJson<ModelProvider>("/api/model-providers", body);
export const updateModelProvider = (id: string, body: ModelProviderWrite) => putJson<ModelProvider>(`/api/model-providers/${id}`, body);
export const deleteModelProvider = (id: string) => deleteJson<{ id: string }>(`/api/model-providers/${id}`);
export const getModelBindings = () => requestJson<ModelBinding[]>("/api/model-bindings");
export const createModelBinding = (body: ModelBindingWrite) => postJson<ModelBinding>("/api/model-bindings", body);
export const updateModelBinding = (id: string, body: ModelBindingWrite) => putJson<ModelBinding>(`/api/model-bindings/${id}`, body);
export const deleteModelBinding = (id: string) => deleteJson<{ id: string }>(`/api/model-bindings/${id}`);

export type PageResult<T> = { items: T[]; count: number; page: number; page_size: number };
export type Equipment = { id: string; code: string; name: string; model: string; type: string; manufacturer: string; status: string; organization_id: string; owner_user_id: string | null; operating_hours: number };
export type WorkOrder = { id: string; number: string; fault_report_id: string; equipment_id: string; status: string; repairer_user_id: string | null; symptom: string; started_at: string | null; completed_at: string | null };
export type MaintenanceRecord = { maintenance_record_id: string; work_order_id: string; fault_report_id?: string; equipment_id: string; work_order_number: string; status: string; symptom: string; actual_cause: string | null; actual_solution: string | null; repair_result: string | null; completed_at: string | null; knowledge_status: string; start_mode?: string; parts_replacement_notes?: string | null; created_at?: string; updated_at?: string };
export type AuditEvent = { id: string; actor_user_id: string | null; action: string; resource_type: string; resource_id: string | null; result: string; created_at: string };
export type BiDashboard = { summary: { fault_count: number; active_fault_count: number; completed_work_order_count: number; completion_rate: number }; trend: Array<{ date: string; fault_count: number; completed_work_order_count: number }>; efficiency: { completed_work_order_count: number; average_completion_hours: number | null }; organization_ranking: Array<{ organization_id: string; organization_name: string; fault_count: number }>; history_comparison: { current_fault_count: number; previous_fault_count: number } };
export type IntelligenceUsage = { items: Array<{ agent_id: string; status: string; run_count: number; configured_max_reply_tokens: number }>; count: number; retention_days: number; token_measurement: "configured_max_reply_tokens_not_actual_usage" };

export const getBiDashboard = (organizationId?: string, period?: "day" | "week" | "month") => {
  const query = new URLSearchParams();
  if (organizationId) query.set("organization_id", organizationId);
  if (period) query.set("period", period);
  return requestJson<BiDashboard>(`/api/bi/dashboard${query.size ? `?${query}` : ""}`);
};
export const getWorkbenchTodos = () => requestJson<{ items: Array<{ id: string; number: string; equipment_name: string; urgency: string; symptom: string; status: string }>; count: number }>("/api/workbench/todos");
export const getWorkbenchAlertSummary = () => requestJson<{ active_fault_count: number; status_counts: Array<{ status: string; count: number }>; urgency_counts: Array<{ urgency: string; count: number }> }>("/api/workbench/alert-summary");
export const getWorkbenchShortcuts = () => requestJson<{ items: Array<{ id: string; label: string; path: string }> }>("/api/workbench/shortcuts");
export const getEquipment = () => requestJson<Equipment[]>("/api/equipment");
export const getEquipmentDetail = (id: string) => requestJson<Equipment>(`/api/equipment/${id}`);
export const getEquipmentHistory = (id: string) => requestJson<PageResult<MaintenanceRecord> & { trend: Array<{ date: string; completed_count: number }> }>(`/api/maintenance-history/equipment/${id}`);
export const getMaintenanceRecords = (params?: { page?: number; pageSize?: number; equipmentId?: string; knowledgeStatus?: string }) => {
  const query = new URLSearchParams();
  if (params?.page && params.page !== 1) query.set("page", String(params.page));
  if (params?.pageSize && params.pageSize !== 20) query.set("page_size", String(params.pageSize));
  if (params?.equipmentId) query.set("equipment_id", params.equipmentId);
  if (params?.knowledgeStatus) query.set("knowledge_status", params.knowledgeStatus);
  return requestJson<PageResult<MaintenanceRecord>>(`/api/maintenance-records${query.size ? `?${query}` : ""}`);
};
export const getMaintenanceRecord = (id: string) => requestJson<MaintenanceRecord>(`/api/maintenance-records/${id}`);
export const getWorkOrders = (params?: { status?: string; page?: number; pageSize?: number }) => {
  const query = new URLSearchParams();
  if (params?.status) query.set("status", params.status);
  if (params?.page && params.page !== 1) query.set("page", String(params.page));
  if (params?.pageSize && params.pageSize !== 20) query.set("page_size", String(params.pageSize));
  return requestJson<PageResult<WorkOrder>>(`/api/work-orders${query.size ? `?${query}` : ""}`);
};
export const getWorkOrder = (id: string) => requestJson<WorkOrder & { pending_inspection_at: string | null }>(`/api/work-orders/${id}`);
export const getAuditEvents = (params?: { action?: string; page?: number; pageSize?: number }) => {
  const query = new URLSearchParams();
  if (params?.action) query.set("action", params.action);
  if (params?.page && params.page !== 1) query.set("page", String(params.page));
  if (params?.pageSize && params.pageSize !== 20) query.set("page_size", String(params.pageSize));
  return requestJson<PageResult<AuditEvent>>(`/api/audit-events${query.size ? `?${query}` : ""}`);
};
export const getIntelligenceUsage = () => requestJson<IntelligenceUsage>("/api/intelligence/usage");
export const getKnowledgeDocuments = (params?: { page?: number; pageSize?: number }) => {
  const query = new URLSearchParams();
  if (params?.page) query.set("page", String(params.page));
  if (params?.pageSize) query.set("page_size", String(params.pageSize));
  return requestJson<PageResult<{ id: string; filename: string; status: string; failure_reason: string | null; retry_available: boolean }>>(`/api/intelligence/knowledge-documents${query.size ? `?${query}` : ""}`);
};

export async function uploadKnowledgeDocument(datasetId: string, file: File): Promise<{ id: string; filename: string; status: string }> {
  const headers = new Headers();
  const token = window.sessionStorage.getItem(accessTokenStorageKey);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  headers.set("Idempotency-Key", crypto.randomUUID());
  const body = new FormData();
  body.append("dataset_id", datasetId);
  body.append("file", file);
  const response = await fetch("/api/knowledge/documents", { method: "POST", headers, body });
  if (!response.ok) {
    const payload = await response.json().catch(() => null) as { detail?: { code?: string } } | null;
    throw new ApiError(response.status, payload?.detail?.code ?? null);
  }
  return response.json() as Promise<{ id: string; filename: string; status: string }>;
}
export const getOrganizations = () => requestJson<Array<{ id: string; type: string; code: string; name: string; parent_id: string | null; enabled: boolean }>>("/api/organizations");
export const getUsers = () => requestJson<Array<{ id: string; username: string; enabled: boolean; role_ids: string[] }>>("/api/users");
export const retryKnowledgeDocument = (id: string) => postJson<{ id: string; status: string }>(`/api/knowledge/documents/${id}/retry`, { document_id: id });
export const getRoles = () => requestJson<Array<{ id: string; code: string; name: string; permission_codes: string[] }>>("/api/roles");
export const getPermissions = () => requestJson<Array<{ code: string }>>("/api/permissions");
export const createOrganization = (body: { type: string; code: string; name: string; parent_id: string; sort_order: number; enabled: boolean; remark: string }) => postJson<{ id: string }>("/api/organizations", body);
export const updateOrganization = (id: string, body: { code: string; name: string; sort_order: number; enabled: boolean; remark: string }) => requestJson(`/api/organizations/${id}`, { method: "PATCH", headers: { "Content-Type": "application/json", "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify(body) });
export const deleteOrganization = (id: string) => requestJson(`/api/organizations/${id}`, { method: "DELETE" });
export const createUser = (body: { username: string; password: string; role_ids: string[] }) => postJson<{ id: string }>("/api/users", body);
export const updateUser = (id: string, body: { enabled: boolean; role_ids: string[] }) => requestJson(`/api/users/${id}`, { method: "PATCH", headers: { "Content-Type": "application/json", "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify(body) });
export const updateRolePermissions = (id: string, permission_codes: string[]) => requestJson(`/api/roles/${id}/permissions`, { method: "PATCH", headers: { "Content-Type": "application/json", "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify({ permission_codes }) });
