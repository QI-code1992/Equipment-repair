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

  it("fails closed to login when the current session cannot be loaded", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: { code: "UNAUTHENTICATED" } }), { status: 401 })));

    render(<MemoryRouter initialEntries={["/bi-dashboard"]}><App /></MemoryRouter>);

    expect(await screen.findByRole("heading", { name: "欢迎回来" })).toBeInTheDocument();
    expect(screen.queryByRole("navigation", { name: "主导航" })).not.toBeInTheDocument();
    expect(window.sessionStorage.getItem("access_token")).toBeNull();
  });

  it("guards the root workbench and global Agent entry with formal permissions", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ id: "user-1", username: "limited", enabled: true, permission_codes: ["equipment:read"] }), { status: 200 })));

    render(<MemoryRouter initialEntries={["/"]}><App /></MemoryRouter>);

    expect(await screen.findByText("你没有访问此页面的权限。")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "全局 Agent" })).not.toBeInTheDocument();
  });

  it("uses the approved operations-console navigation shell for an authorized page", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "user-1", username: "operator", enabled: true, permission_codes: ["workbench:view"] }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [], count: 0 }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ active_fault_count: 0, status_counts: [], urgency_counts: [] }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [] }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    render(<MemoryRouter initialEntries={["/"]}><App /></MemoryRouter>);

    expect(await screen.findByRole("navigation", { name: "业务导航" })).toBeInTheDocument();
    expect(screen.getByText("新能源装载机智能运维平台")).toBeInTheDocument();
    expect(screen.getByText("工作台 / 运维工作台")).toBeInTheDocument();
  });

  it("requires every formal dependency permission before opening equipment creation", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ id: "user-1", username: "reader", enabled: true, permission_codes: ["equipment:read"] }), { status: 200 })));

    render(<MemoryRouter initialEntries={["/equipment/new"]}><App /></MemoryRouter>);

    expect(await screen.findByText("你没有访问此页面的权限。")).toBeInTheDocument();
    expect(screen.queryByLabelText("设备编码")).not.toBeInTheDocument();
  });

  it("keeps the contextual topbar title on nested equipment routes", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "user-1", username: "operator", enabled: true, permission_codes: ["equipment:read", "equipment:write", "organization:read", "identity:read"] }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([{ id: "line-1", type: "LINE", code: "LINE-01", name: "一线", parent_id: "factory-1", enabled: true }]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([{ id: "user-2", username: "owner", enabled: true, role_ids: [] }]), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    render(<MemoryRouter initialEntries={["/equipment/new"]}><App /></MemoryRouter>);

    expect(await screen.findByText("资产管理 / 新增设备")).toBeInTheDocument();
  });

  it("loads an Agent configuration and saves only the selected Agent", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "user-1", username: "admin", enabled: true, permission_codes: ["bi:view", "organization:read", "organization:write", "equipment:read", "equipment:write", "intelligence:model", "intelligence:audit", "intelligence:agent", "intelligence:knowledge", "fault:create", "maintenance:view", "maintenance:detail", "fault:repair", "fault:close", "identity:read", "identity:write", "system:audit", "workbench:view"] }), { status: 200 }))
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

    expect(screen.getByRole("navigation", { name: "业务导航" })).toBeInTheDocument();
    await screen.findByRole("tab", { name: "智能体配置" });
    fireEvent.click(screen.getByRole("tab", { name: "智能体配置" }));
    expect(await screen.findByRole("heading", { name: "AI 故障上报" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "智能配置", level: 1 })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "AI 故障上报" })).toBeInTheDocument();

    fireEvent.click(screen.getByLabelText("启用深度思考"));
    fireEvent.click(screen.getByRole("button", { name: "保存 Agent 配置" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(5));
    expect(fetchMock.mock.calls[4][0]).toBe("/api/agent-configs/fault_reporting");
    expect(screen.getByText("Agent 配置已保存。")).toBeInTheDocument();
  });

  it("shows a controlled empty state when the formal Agent catalogue is empty", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "user-1", username: "admin", enabled: true, permission_codes: ["intelligence:model", "intelligence:agent", "intelligence:knowledge"] }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    render(<MemoryRouter initialEntries={["/intelligent-config"]}><App /></MemoryRouter>);
    await screen.findByRole("tab", { name: "智能体配置" });
    fireEvent.click(screen.getByRole("tab", { name: "智能体配置" }));
    expect(await screen.findByText("尚无可配置的 Agent。")).toBeInTheDocument();
    expect(fetchMock.mock.calls.map(([path]) => path)).toEqual([
      "/api/auth/me", "/api/agent-configs", "/api/model-providers", "/api/model-bindings",
    ]);
  });

  it("does not submit unsupported deep thinking configuration", async () => {
    const unsupported = { ...config, model_capability: { ...config.model_capability, supports_reasoning: false } };
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "user-1", username: "admin", enabled: true, permission_codes: ["intelligence:model", "intelligence:agent", "intelligence:knowledge"] }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([unsupported]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([provider]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([{ ...binding, supports_reasoning: false }]), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    render(<MemoryRouter initialEntries={["/intelligent-config"]}><App /></MemoryRouter>);
    await screen.findByRole("tab", { name: "智能体配置" });
    fireEvent.click(screen.getByRole("tab", { name: "智能体配置" }));
    await screen.findByRole("heading", { name: "AI 故障上报" });
    fireEvent.click(screen.getByLabelText("启用深度思考"));

    expect(screen.getByText("当前模型不支持深度思考，请关闭开关或改绑支持推理的模型。")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(4);
  });

  it("routes the fault-report navigation to the formal submission page", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ id: "user-1", username: "admin", enabled: true, permission_codes: ["fault:create", "intelligence:agent"] }), { status: 200 })));
    render(<MemoryRouter initialEntries={["/fault-report"]}><App /></MemoryRouter>);

    expect(await screen.findByRole("heading", { name: "故障上报" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "提交故障" })).toBeInTheDocument();
    expect(screen.queryByText("业务内容将在对应任务中接入")).not.toBeInTheDocument();
  });

  it("redirects an unauthenticated visitor to the login page", () => {
    window.sessionStorage.clear();
    render(<MemoryRouter initialEntries={["/fault-report"]}><App /></MemoryRouter>);

    expect(screen.getByRole("heading", { name: "欢迎回来" })).toBeInTheDocument();
  });

  it("stores a successful login then sends its Bearer token on the protected page request", async () => {
    window.sessionStorage.clear();
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ access_token: "session-token", token_type: "bearer" }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "user-1", username: "repairer", enabled: true, permission_codes: ["intelligence:model", "intelligence:agent", "intelligence:knowledge"] }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([config]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([provider]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([binding]), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    render(<MemoryRouter initialEntries={["/intelligent-config"]}><App /></MemoryRouter>);

    fireEvent.change(screen.getByLabelText("用户名"), { target: { value: "repairer" } });
    fireEvent.change(screen.getByLabelText("密码"), { target: { value: "correct-password" } });
    fireEvent.click(screen.getByRole("button", { name: "登录系统" }));

    expect(await screen.findByRole("heading", { name: "智能配置" })).toBeInTheDocument();
    const [, init] = fetchMock.mock.calls[1] as [string, RequestInit];
    expect(new Headers(init.headers).get("Authorization")).toBe("Bearer session-token");
  });

  it("loads authenticated Agent thread history and never renders raw message text", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "user-1", username: "admin", enabled: true, permission_codes: ["intelligence:agent", "workbench:view"] }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [], count: 0 }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ active_fault_count: 0, status_counts: [], urgency_counts: [] }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [] }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }))
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

  it("opens the notification panel, filters unread items, and marks an item read", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "user-1", username: "operator", enabled: true, permission_codes: ["workbench:view"] }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [], count: 0 }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ active_fault_count: 0, status_counts: [], urgency_counts: [] }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [] }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ unread_count: 2 }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [{ id: "notice-1", type: "FAULT", title: "Fault submitted", body: "Pump alarm", level: "WARNING", action_url: "/fault-report", related_object_id: "fault-1", created_at: "2026-08-01T00:00:00Z", is_read: false }], total: 1, unread_count: 2 }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ unread_count: 2 }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [{ id: "notice-1", type: "FAULT", title: "Fault submitted", body: "Pump alarm", level: "WARNING", action_url: "/fault-report", related_object_id: "fault-1", created_at: "2026-08-01T00:00:00Z", is_read: false }], total: 1, unread_count: 2 }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "notice-1", is_read: true }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    render(<MemoryRouter initialEntries={["/"]}><App /></MemoryRouter>);
    fireEvent.click(await screen.findByRole("button", { name: "Notifications" }));

    expect(await screen.findByRole("dialog", { name: "Notifications" })).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "未读" }));
    expect(await screen.findByText("Fault submitted")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Fault submitted/ }));
    await waitFor(() => expect(fetchMock.mock.calls.some(([path]) => path === "/api/notifications/notice-1/read")).toBe(true));
  });

  it("keeps the mobile navigation and Agent drawer mutually layered", async () => {
    vi.stubGlobal("fetch", vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "user-1", username: "operator", enabled: true, permission_codes: ["workbench:view", "intelligence:agent"] }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [], count: 0 }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ active_fault_count: 0, status_counts: [], urgency_counts: [] }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [] }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [], count: 0 }), { status: 200 })));

    render(<MemoryRouter initialEntries={["/"]}><App /></MemoryRouter>);
    fireEvent.click(await screen.findByRole("button", { name: "打开导航" }));
    expect(screen.getByRole("button", { name: "关闭导航" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "全局 Agent" }));
    expect(screen.getByRole("dialog", { name: "全局 Agent" })).toBeInTheDocument();
  });

  it("renders a semantic breadcrumb for the active route", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ id: "user-1", username: "operator", enabled: true, permission_codes: ["workbench:view"] }), { status: 200 })));

    render(<MemoryRouter initialEntries={["/"]}><App /></MemoryRouter>);

    const breadcrumb = await screen.findByRole("navigation", { name: "面包屑" });
    expect(breadcrumb).toHaveTextContent("工作台");
    expect(breadcrumb).toHaveTextContent("运维工作台");
  });

  it("exposes the Agent drawer as a modal with an accessible close action", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ id: "user-1", username: "operator", enabled: true, permission_codes: ["workbench:view", "intelligence:agent"] }), { status: 200 })));

    render(<MemoryRouter initialEntries={["/"]}><App /></MemoryRouter>);
    fireEvent.click(await screen.findByRole("button", { name: "全局 Agent" }));

    expect(screen.getByRole("dialog", { name: "全局 Agent" })).toHaveAttribute("aria-modal", "true");
    fireEvent.click(screen.getByRole("button", { name: "关闭" }));
    expect(screen.queryByRole("dialog", { name: "全局 Agent" })).not.toBeInTheDocument();
  });
});
