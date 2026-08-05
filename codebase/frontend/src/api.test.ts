import { afterEach, describe, expect, it, vi } from "vitest";

import {
  ApiError,
  createFaultReport,
  getHealthScore,
  login,
  logout,
  readRunEvents,
  startAgentRun,
  getAgentConfig,
  getAgentConfigs,
  requestJson,
  saveAgentConfig,
  submitAgentFaultReport,
  startRepair,
  getBiDashboard,
  getKnowledgeDocuments,
  getAgentThreads,
  getAgentThread,
  resumeAgentThread,
  retryKnowledgeDocument,
  getNotifications,
  getNotificationUnreadCount,
  markNotificationRead,
  markAllNotificationsRead,
} from "./api";

afterEach(() => window.sessionStorage.clear());

describe("requestJson", () => {
  it("uses the browser fetch boundary and returns JSON", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ status: "ok" }), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(requestJson<{ status: string }>("/healthz")).resolves.toEqual({ status: "ok" });
    expect(fetchMock).toHaveBeenCalledWith("/healthz", undefined);
  });

  it("adds the active login token to JSON requests", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ status: "ok" }), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetchMock);
    window.sessionStorage.setItem("access_token", "active-login-token");

    await requestJson<{ status: string }>("/api/agent-configs");

    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(new Headers(init.headers).get("Authorization")).toBe("Bearer active-login-token");
  });

  it("stores only the successful login access token in the browser session", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ access_token: "session-token", token_type: "bearer" }), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await login("repairer", "correct-password");

    expect(window.sessionStorage.getItem("access_token")).toBe("session-token");
    expect(fetchMock).toHaveBeenCalledWith("/api/auth/login", expect.objectContaining({
      method: "POST", body: JSON.stringify({ username: "repairer", password: "correct-password" }),
    }));
  });

  it("clears the browser session after requesting logout", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response("null", { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    window.sessionStorage.setItem("access_token", "session-token");

    await logout();

    expect(window.sessionStorage.getItem("access_token")).toBeNull();
    expect(fetchMock).toHaveBeenCalledWith("/api/auth/session", expect.objectContaining({ method: "DELETE" }));
    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(new Headers(init.headers).get("Idempotency-Key")).toBeTruthy();
  });
});

describe("notifications API", () => {
  it("loads paged notifications with unread filtering", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ items: [], total: 0, unread_count: 0 }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    await getNotifications({ page: 2, pageSize: 10, unreadOnly: true });

    expect(fetchMock).toHaveBeenCalledWith("/api/notifications?page=2&page_size=10&unread_only=true", undefined);
  });

  it("reads the unread count and marks one or all notifications read", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ unread_count: 3 }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "notice-1", is_read: true }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ updated_count: 3 }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(getNotificationUnreadCount()).resolves.toEqual({ unread_count: 3 });
    await markNotificationRead("notice-1");
    await markAllNotificationsRead();

    expect(fetchMock.mock.calls.map(([path]) => path)).toEqual([
      "/api/notifications/unread-count",
      "/api/notifications/notice-1/read",
      "/api/notifications/read-all",
    ]);
    expect((fetchMock.mock.calls[1][1] as RequestInit).method).toBe("PATCH");
    expect((fetchMock.mock.calls[2][1] as RequestInit).method).toBe("POST");
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

describe("maintenance API", () => {
  it("reads dashboard and knowledge status through the authenticated API boundary", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ summary: {} }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [], count: 0, page: 1, page_size: 20 }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    window.sessionStorage.setItem("access_token", "active-login-token");

    await getBiDashboard();
    await getKnowledgeDocuments();

    expect(fetchMock.mock.calls.map(([path]) => path)).toEqual(["/api/bi/dashboard", "/api/intelligence/knowledge-documents"]);
    expect(new Headers((fetchMock.mock.calls[0][1] as RequestInit).headers).get("Authorization")).toBe("Bearer active-login-token");
  });

  it("sends a knowledge retry with an idempotency key", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ id: "doc-1", status: "UPLOADING" }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    await retryKnowledgeDocument("doc-1");

    expect(fetchMock).toHaveBeenCalledWith("/api/knowledge/documents/doc-1/retry", expect.objectContaining({
      method: "POST", headers: expect.objectContaining({ "Idempotency-Key": expect.any(String) }),
    }));
  });

  it("sends adopted repair start with an idempotency key", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ work_order_id: "wo-1" }), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await startRepair("fault-1", { mode: "ADOPTED", diagnosis_draft_id: "draft-1" });

    expect(fetchMock).toHaveBeenCalledWith("/api/fault-reports/fault-1/start-repair", expect.objectContaining({
      method: "POST",
      headers: expect.objectContaining({ "Idempotency-Key": expect.any(String) }),
      body: JSON.stringify({ mode: "ADOPTED", diagnosis_draft_id: "draft-1" }),
    }));
  });

  it("throws a public ApiError for a forbidden response", async () => {
    const fetchMock = vi.fn().mockImplementation(() => Promise.resolve(
      new Response(JSON.stringify({ detail: { code: "FORBIDDEN" } }), { status: 403 }),
    ));
    vi.stubGlobal("fetch", fetchMock);

    await expect(createFaultReport({
      equipment_id: "eq-1",
      urgency: "HIGH",
      symptom: "液压压力异常",
      occurred_at: "2026-07-27T10:00:00+08:00",
      attachment_refs: [],
    })).rejects.toBeInstanceOf(ApiError);
    await expect(createFaultReport({
      equipment_id: "eq-1",
      urgency: "HIGH",
      symptom: "液压压力异常",
      occurred_at: "2026-07-27T10:00:00+08:00",
      attachment_refs: [],
    })).rejects.toMatchObject({ status: 403, code: "FORBIDDEN" });
  });

  it("loads a health score and submits a confirmed AI fault draft", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ status: "READY", score: 91 }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "fault-1", agent_status: "AI_DRAFT" }), { status: 201 }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(getHealthScore("eq-1")).resolves.toMatchObject({ score: 91 });
    await expect(submitAgentFaultReport({
      draft: { equipment_id: "eq-1", urgency: "HIGH", symptom: "液压压力异常", occurred_at: "2026-07-27T10:00:00+08:00", duration_minutes: 10, attachment_refs: [] },
      confirmed: true,
    })).resolves.toMatchObject({ agent_status: "AI_DRAFT" });
    expect(fetchMock.mock.calls.map(([path]) => path)).toEqual([
      "/api/agent/health-score/eq-1",
      "/api/agent/fault-reports/submit",
    ]);
  });
});

describe("Agent Runtime SSE API", () => {
  it("loads thread history and resumes with the boolean contract", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [], count: 0 }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ thread_id: "thread-1", agent_id: "operation_guidance", status: "OPEN", messages: [], runs: [] }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ run_id: "run-2", thread_id: "thread-1", status: "RESUMED" }), { status: 202 }));
    vi.stubGlobal("fetch", fetchMock);
    await expect(getAgentThreads()).resolves.toEqual({ items: [], count: 0 });
    await expect(getAgentThread("thread-1")).resolves.toMatchObject({ thread_id: "thread-1" });
    await resumeAgentThread("thread-1", { resume: true, confirmation: { source: "user" } });
    expect(JSON.parse(String((fetchMock.mock.calls[2][1] as RequestInit).body))).toEqual({ resume: true, confirmation: { source: "user" } });
  });

  it("parses only real SSE event names and JSON data", async () => {
    const encoder = new TextEncoder();
    const body = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode('event: run_started\ndata: {"status":"RUNNING"}\n\n'));
        controller.enqueue(encoder.encode('event: run_waiting\ndata: {"status":"WAITING_FOR_MODEL"}\n\n'));
        controller.close();
      },
    });
    const fetchMock = vi.fn().mockResolvedValue(new Response(body, { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    window.sessionStorage.setItem("access_token", "active-login-token");

    await expect(readRunEvents("run-1")).resolves.toEqual([
      { event: "run_started", data: { status: "RUNNING" } },
      { event: "run_waiting", data: { status: "WAITING_FOR_MODEL" } },
    ]);
    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(new Headers(init.headers).get("Authorization")).toBe("Bearer active-login-token");
  });

  it("parses CRLF and multiline SSE data, including error events and a final incomplete block", async () => {
    const encoder = new TextEncoder();
    const body = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode('event: run_started\r\ndata: {"status":\r\ndata: "RUNNING"}\r\n\r\nevent: error\r\ndata: {"status":"FAILED"}\r\n\r\nevent: run_waiting\r\ndata: {"status":"WAITING"}'));
        controller.close();
      },
    });
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(body, { status: 200 })));

    await expect(readRunEvents("run-crlf")).resolves.toEqual([
      { event: "run_started", data: { status: "RUNNING" } },
      { event: "error", data: { status: "FAILED" } },
      { event: "run_waiting", data: { status: "WAITING" } },
    ]);
  });

  it("emits SSE events as chunks arrive before the stream closes", async () => {
    const encoder = new TextEncoder();
    let controller!: ReadableStreamDefaultController<Uint8Array>;
    const body = new ReadableStream<Uint8Array>({
      start(activeController) {
        controller = activeController;
        controller.enqueue(encoder.encode('event: run_started\ndata: {"status":"RUNNING"}\n\n'));
      },
    });
    const fetchMock = vi.fn().mockResolvedValue(new Response(body, { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    const seen: Array<{ event: string; data: Record<string, unknown> }> = [];

    const pending = readRunEvents("run-1", (event) => seen.push(event));
    for (let index = 0; index < 10 && seen.length === 0; index += 1) await new Promise((resolve) => setTimeout(resolve, 0));

    expect(seen).toEqual([{ event: "run_started", data: { status: "RUNNING" } }]);
    controller.enqueue(encoder.encode('event: run_completed\ndata: {"status":"COMPLETED"}\n\n'));
    controller.close();
    await expect(pending).resolves.toEqual([
      { event: "run_started", data: { status: "RUNNING" } },
      { event: "run_completed", data: { status: "COMPLETED" } },
    ]);
  });

  it("atomically starts an operation-guidance thread and run", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ thread_id: "thread-1", run_id: "run-1" }), { status: 202 }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(startAgentRun("operation_guidance", { equipment_id: "eq-1" }, "如何安全检查？")).resolves.toEqual({ thread_id: "thread-1", run_id: "run-1" });
    expect(fetchMock.mock.calls.map(([path]) => path)).toEqual(["/api/agent/threads/start"]);
    expect(new Headers((fetchMock.mock.calls[0][1] as RequestInit).headers).get("Idempotency-Key")).toBeTruthy();
    expect(JSON.parse((fetchMock.mock.calls[0][1] as RequestInit).body as string)).toEqual({
      agent_id: "operation_guidance", business_context: { equipment_id: "eq-1" }, text: "如何安全检查？", attachment_refs: [],
    });
  });
});
