import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";

describe("App", () => {
  const config = {
    agent_id: "fault_reporting", enabled: true, model_binding_id: "binding-1",
    knowledge_dataset_ids: [], streaming_enabled: true, suggestions_enabled: true,
    sources_enabled: true, context_turns: 3, retrieval_limit: 6, similarity_threshold: 0.62,
    deep_thinking_enabled: false, deep_thinking_level: "medium", max_reply_tokens: 4096,
    model_capability: { binding_id: "binding-1", display_name: "GPT 推理模型", supports_reasoning: true },
  };
  const provider = { id: "provider-1", name: "内部模型服务", enabled: true };
  const binding = { id: "binding-1", provider_id: "provider-1", name: "GPT 推理模型", model_name: "gpt-ops", supports_reasoning: true, enabled: true };

  beforeEach(() => window.sessionStorage.setItem("access_token", "existing-session-token"));

  it("loads an Agent configuration and saves only the selected Agent", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "user-1", username: "admin", enabled: true, permission_codes: ["bi:view", "organization:read", "equipment:read", "intelligence:model", "intelligence:audit", "fault:create", "intelligence:agent", "maintenance:view", "fault:repair", "identity:read"] }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([config]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([provider]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([binding]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(config), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    render(
      <MemoryRouter initialEntries={["/intelligent-config"]}>
        <App />
      </MemoryRouter>,
    );

    expect(screen.getByRole("navigation", { name: "主导航" })).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "AI 故障上报" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "智能配置" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "AI 故障上报" })).toBeInTheDocument();

    fireEvent.click(screen.getByLabelText("启用深度思考"));
    fireEvent.click(screen.getByRole("button", { name: "保存 Agent 配置" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(5));
    expect(fetchMock.mock.calls[4][0]).toBe("/api/agent-configs/fault_reporting");
    expect(screen.getByText("Agent 配置已保存。")).toBeInTheDocument();
  });

  it("shows a controlled empty state when the formal Agent catalogue is empty", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "user-1", username: "admin", enabled: true, permission_codes: ["intelligence:model"] }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    render(<MemoryRouter initialEntries={["/intelligent-config"]}><App /></MemoryRouter>);
    expect(await screen.findByText("尚无可配置的 Agent。")).toBeInTheDocument();
    expect(fetchMock.mock.calls.map(([path]) => path)).toEqual([
      "/api/auth/me", "/api/agent-configs", "/api/model-providers", "/api/model-bindings",
    ]);
  });

  it("does not submit unsupported deep thinking configuration", async () => {
    const unsupported = { ...config, model_capability: { ...config.model_capability, supports_reasoning: false } };
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "user-1", username: "admin", enabled: true, permission_codes: ["intelligence:model"] }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([unsupported]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([provider]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([{ ...binding, supports_reasoning: false }]), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    render(<MemoryRouter initialEntries={["/intelligent-config"]}><App /></MemoryRouter>);
    await screen.findByRole("heading", { name: "AI 故障上报" });
    fireEvent.click(screen.getByLabelText("启用深度思考"));

    expect(screen.getByText("当前模型不支持深度思考，请关闭开关或改绑支持推理的模型。")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(4);
  });

  it("routes the fault-report navigation to the formal submission page", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ id: "user-1", username: "admin", enabled: true, permission_codes: ["fault:create"] }), { status: 200 })));
    render(<MemoryRouter initialEntries={["/fault-report"]}><App /></MemoryRouter>);

    expect(await screen.findByRole("heading", { name: "故障上报" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "提交故障" })).toBeInTheDocument();
    expect(screen.queryByText("业务内容将在对应任务中接入")).not.toBeInTheDocument();
  });

  it("redirects an unauthenticated visitor to the login page", () => {
    window.sessionStorage.clear();
    render(<MemoryRouter initialEntries={["/fault-report"]}><App /></MemoryRouter>);

    expect(screen.getByRole("heading", { name: "登录" })).toBeInTheDocument();
  });

  it("stores a successful login then sends its Bearer token on the protected page request", async () => {
    window.sessionStorage.clear();
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ access_token: "session-token", token_type: "bearer" }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "user-1", username: "repairer", enabled: true, permission_codes: ["intelligence:model"] }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([config]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([provider]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([binding]), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    render(<MemoryRouter initialEntries={["/intelligent-config"]}><App /></MemoryRouter>);

    fireEvent.change(screen.getByLabelText("用户名"), { target: { value: "repairer" } });
    fireEvent.change(screen.getByLabelText("密码"), { target: { value: "correct-password" } });
    fireEvent.click(screen.getByRole("button", { name: "登录" }));

    expect(await screen.findByRole("heading", { name: "智能配置" })).toBeInTheDocument();
    const [, init] = fetchMock.mock.calls[1] as [string, RequestInit];
    expect(new Headers(init.headers).get("Authorization")).toBe("Bearer session-token");
  });

  it("loads authenticated Agent thread history and never renders raw message text", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "user-1", username: "admin", enabled: true, permission_codes: ["intelligence:agent"] }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [], count: 0 }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ active_fault_count: 0, status_counts: [], urgency_counts: [] }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [] }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [{ thread_id: "thread-1", agent_id: "operation_guidance", status: "OPEN", created_at: "2026-07-31T00:00:00Z", updated_at: "2026-07-31T00:01:00Z" }], count: 1 }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ thread_id: "thread-1", agent_id: "operation_guidance", status: "OPEN", messages: [{ role: "user", text: "secret internal text" }], runs: [] }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    render(<MemoryRouter initialEntries={["/"]}><App /></MemoryRouter>);
    fireEvent.click(await screen.findByRole("button", { name: "全局 Agent" }));
    fireEvent.click(screen.getByRole("button", { name: "线程历史" }));
    expect(await screen.findByRole("button", { name: /operation_guidance/ })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /operation_guidance/ }));
    expect(await screen.findByText("消息已记录（内容受保护）")).toBeInTheDocument();
    expect(screen.queryByText("secret internal text")).not.toBeInTheDocument();
  });
});
