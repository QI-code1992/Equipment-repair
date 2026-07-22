import { describe, expect, it, vi } from "vitest";

import { getAgentConfig, getAgentConfigs, requestJson, saveAgentConfig } from "./api";

describe("requestJson", () => {
  it("uses the browser fetch boundary and returns JSON", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ status: "ok" }), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(requestJson<{ status: string }>("/healthz")).resolves.toEqual({ status: "ok" });
    expect(fetchMock).toHaveBeenCalledWith("/healthz", undefined);
  });
});

describe("agent configuration API", () => {
  it("loads the independent Agent configuration collection", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify([{ agent_id: "fault_reporting" }]), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(getAgentConfigs()).resolves.toEqual([{ agent_id: "fault_reporting" }]);
    expect(fetchMock).toHaveBeenCalledWith("/api/agent-configs", undefined);
  });

  it("saves one Agent configuration with an idempotency key", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ agent_id: "fault_reporting" }), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await saveAgentConfig({
      agent_id: "fault_reporting", enabled: true, model_binding_id: "binding-1",
      knowledge_dataset_ids: [], streaming_enabled: true, suggestions_enabled: true,
      sources_enabled: true, context_turns: 3, retrieval_limit: 6, similarity_threshold: 0.62,
      deep_thinking_enabled: false, deep_thinking_level: "medium", max_reply_tokens: 4096,
    });

    expect(fetchMock).toHaveBeenCalledWith("/api/agent-configs/fault_reporting", expect.objectContaining({
      method: "PUT", headers: expect.objectContaining({ "Content-Type": "application/json", "Idempotency-Key": expect.any(String) }),
    }));
  });

  it("loads only the Agent selected for first initialization", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ agent_id: "metric_query" }), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await getAgentConfig("metric_query");
    expect(fetchMock).toHaveBeenCalledWith("/api/agent-configs/metric_query", undefined);
  });
});
