import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { App } from "./App";

describe("App", () => {
  const config = {
    agent_id: "fault_reporting", enabled: true, model_binding_id: "binding-1",
    knowledge_dataset_ids: [], streaming_enabled: true, suggestions_enabled: true,
    sources_enabled: true, context_turns: 3, retrieval_limit: 6, similarity_threshold: 0.62,
    deep_thinking_enabled: false, deep_thinking_level: "medium", max_reply_tokens: 4096,
    model_capability: { binding_id: "binding-1", display_name: "GPT 推理模型", supports_reasoning: true },
  };

  it("loads an Agent configuration and saves only the selected Agent", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify([config]), { status: 200 }))
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
    expect(screen.getByRole("button", { name: "智能问数" })).toBeInTheDocument();

    fireEvent.click(screen.getByLabelText("启用深度思考"));
    fireEvent.click(screen.getByRole("button", { name: "保存配置" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    expect(fetchMock.mock.calls[1][0]).toBe("/api/agent-configs/fault_reporting");
    expect(screen.getByText("配置已保存")).toBeInTheDocument();
  });

  it("initializes only the Agent selected from an empty configuration list", async () => {
    const metricConfig = { ...config, agent_id: "metric_query" };
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(config), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(metricConfig), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    render(<MemoryRouter initialEntries={["/intelligent-config"]}><App /></MemoryRouter>);
    await screen.findByRole("heading", { name: "AI 故障上报" });
    fireEvent.click(screen.getByRole("button", { name: "智能问数" }));

    await screen.findByRole("heading", { name: "智能问数" });
    expect(fetchMock.mock.calls.map(([path]) => path)).toEqual([
      "/api/agent-configs", "/api/agent-configs/fault_reporting", "/api/agent-configs/metric_query",
    ]);
  });

  it("does not submit unsupported deep thinking configuration", async () => {
    const unsupported = { ...config, model_capability: { ...config.model_capability, supports_reasoning: false } };
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify([unsupported]), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    render(<MemoryRouter initialEntries={["/intelligent-config"]}><App /></MemoryRouter>);
    await screen.findByRole("heading", { name: "AI 故障上报" });
    fireEvent.click(screen.getByLabelText("启用深度思考"));

    expect(screen.getByText("当前模型不支持深度思考，请关闭开关或改绑支持推理的模型。")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("routes the fault-report navigation to the formal submission page", () => {
    render(<MemoryRouter initialEntries={["/fault-report"]}><App /></MemoryRouter>);

    expect(screen.getByRole("heading", { name: "故障上报" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "提交故障" })).toBeInTheDocument();
    expect(screen.queryByText("业务内容将在对应任务中接入")).not.toBeInTheDocument();
  });
});
