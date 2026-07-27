export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string | null,
  ) {
    super(code ?? `HTTP_${status}`);
  }
}

export async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);

  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: { code?: string } } | null;
    throw new ApiError(response.status, body?.detail?.code ?? null);
  }

  return response.json() as Promise<T>;
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

export type AgentFaultDraft = FaultReportCreate & { duration_minutes: number };

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
  state: string;
  question: string | null;
  evidence: Array<{ citation: string; text: string }>;
  manual_fallback: boolean;
  loading_seconds: number;
};

export type RuntimeEvent = { event: string; data: Record<string, unknown> };

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
  return postJson<FaultReport & { agent_status: string }>("/api/agent/fault-reports/submit", payload);
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
  const response = await fetch(`/api/agent/runs/${runId}/events`);
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
