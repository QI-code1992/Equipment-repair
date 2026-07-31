import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { createModelBinding, createModelProvider, getAgentConfigs, getModelBindings, getModelProviders, saveAgentConfig, updateModelBinding, updateModelProvider, uploadKnowledgeDocument } from "./api";
import { IntelligentConfigPage } from "./IntelligentConfigPage";

vi.mock("./api", async (importOriginal) => ({
  ...await importOriginal<typeof import("./api")>(),
  getAgentConfigs: vi.fn(),
  getAgentConfig: vi.fn(),
  getModelProviders: vi.fn(),
  getModelBindings: vi.fn(),
  createModelProvider: vi.fn(),
  createModelBinding: vi.fn(),
  updateModelProvider: vi.fn(),
  updateModelBinding: vi.fn(),
  saveAgentConfig: vi.fn(),
  uploadKnowledgeDocument: vi.fn(),
}));

const config = {
  agent_id: "fault_reporting", enabled: true, model_binding_id: "binding-1", knowledge_dataset_ids: [],
  streaming_enabled: true, suggestions_enabled: false, sources_enabled: true, context_turns: 3,
  retrieval_limit: 5, similarity_threshold: 0.7, deep_thinking_enabled: false, deep_thinking_level: "low" as const,
  max_reply_tokens: 512, model_capability: { binding_id: "binding-1", display_name: "运维模型", supports_reasoning: true },
};

describe("IntelligentConfigPage", () => {
  it("manages providers and bindings with the formal model catalog APIs without exposing a provider secret", async () => {
    vi.mocked(getAgentConfigs).mockResolvedValue([config]);
    vi.mocked(getModelProviders).mockResolvedValue([{ id: "provider-1", name: "内部模型服务", enabled: true }]);
    vi.mocked(getModelBindings).mockResolvedValue([{ id: "binding-1", provider_id: "provider-1", name: "运维模型", model_name: "ops-1", supports_reasoning: true, enabled: true }]);
    vi.mocked(createModelProvider).mockResolvedValue({ id: "provider-2", name: "备用模型服务", enabled: true });
    vi.mocked(createModelBinding).mockResolvedValue({ id: "binding-2", provider_id: "provider-2", name: "备用模型", model_name: "ops-2", supports_reasoning: false, enabled: true });
    vi.mocked(saveAgentConfig).mockResolvedValue(config);

    render(<IntelligentConfigPage />);

    expect(await screen.findByText("内部模型服务")).toBeInTheDocument();
    expect(screen.getByText("运维模型（ops-1）")).toBeInTheDocument();
    expect(screen.queryByText(/secret-ref-value/)).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("提供商名称"), { target: { value: "备用模型服务" } });
    fireEvent.change(screen.getByLabelText("密钥引用"), { target: { value: "vault://models/backup" } });
    fireEvent.click(screen.getByRole("button", { name: "新增模型提供商" }));
    await waitFor(() => expect(createModelProvider).toHaveBeenCalledWith({ name: "备用模型服务", secret_ref: "vault://models/backup", enabled: true }));

    fireEvent.change(screen.getByLabelText("绑定提供商"), { target: { value: "provider-2" } });
    fireEvent.change(screen.getByLabelText("绑定名称"), { target: { value: "备用模型" } });
    fireEvent.change(screen.getByLabelText("模型名称"), { target: { value: "ops-2" } });
    fireEvent.click(screen.getByRole("button", { name: "新增模型绑定" }));
    await waitFor(() => expect(createModelBinding).toHaveBeenCalledWith(expect.objectContaining({ name: "备用模型", model_name: "ops-2" })));
  });

  it("edits a provider and binding through the formal APIs without displaying its secret reference", async () => {
    vi.mocked(getAgentConfigs).mockResolvedValue([config]);
    vi.mocked(getModelProviders).mockResolvedValue([{ id: "provider-1", name: "内部模型服务", enabled: true }]);
    vi.mocked(getModelBindings).mockResolvedValue([{ id: "binding-1", provider_id: "provider-1", name: "运维模型", model_name: "ops-1", supports_reasoning: true, enabled: true }]);
    vi.mocked(updateModelProvider).mockResolvedValue({ id: "provider-1", name: "已更新模型服务", enabled: true });
    vi.mocked(updateModelBinding).mockResolvedValue({ id: "binding-1", provider_id: "provider-1", name: "已更新运维模型", model_name: "ops-2", supports_reasoning: false, enabled: true });

    render(<IntelligentConfigPage />);

    await screen.findByText("内部模型服务");
    fireEvent.click(screen.getByRole("button", { name: "编辑模型提供商：内部模型服务" }));
    fireEvent.change(screen.getByLabelText("编辑提供商名称"), { target: { value: "已更新模型服务" } });
    fireEvent.change(screen.getByLabelText("新的密钥引用"), { target: { value: "vault://models/replacement" } });
    fireEvent.click(screen.getByRole("button", { name: "保存模型提供商" }));
    await waitFor(() => expect(updateModelProvider).toHaveBeenCalledWith("provider-1", {
      name: "已更新模型服务", secret_ref: "vault://models/replacement", enabled: true,
    }));
    expect(screen.queryByText(/vault:|secret_ref/i)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "编辑模型绑定：运维模型" }));
    fireEvent.change(screen.getByLabelText("编辑绑定名称"), { target: { value: "已更新运维模型" } });
    fireEvent.change(screen.getByLabelText("编辑模型名称"), { target: { value: "ops-2" } });
    fireEvent.click(screen.getByLabelText("编辑绑定支持深度思考"));
    fireEvent.click(screen.getByRole("button", { name: "保存模型绑定" }));
    await waitFor(() => expect(updateModelBinding).toHaveBeenCalledWith("binding-1", expect.objectContaining({
      name: "已更新运维模型", model_name: "ops-2", supports_reasoning: false,
    })));
  });

  it("uploads a knowledge document only after a dataset is supplied", async () => {
    vi.mocked(getAgentConfigs).mockResolvedValue([config]);
    vi.mocked(getModelProviders).mockResolvedValue([]);
    vi.mocked(getModelBindings).mockResolvedValue([]);
    vi.mocked(uploadKnowledgeDocument).mockResolvedValue({ id: "doc-1", filename: "manual.pdf", status: "UPLOADING" });
    render(<IntelligentConfigPage />);
    await screen.findByText("暂无模型提供商。");
    fireEvent.change(screen.getByLabelText("正式 Dataset ID"), { target: { value: "dataset-1" } });
    fireEvent.change(screen.getByLabelText("上传知识文档"), { target: { files: [new File(["manual"], "manual.pdf", { type: "application/pdf" })] } });
    await waitFor(() => expect(uploadKnowledgeDocument).toHaveBeenCalledWith("dataset-1", expect.any(File)));
    expect(await screen.findByText("知识文档已提交，后续状态由正式 Worker 更新。")).toBeInTheDocument();
  });
});
