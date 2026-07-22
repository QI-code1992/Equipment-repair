export async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export type DeepThinkingLevel = "low" | "medium" | "high";

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
