import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, createFaultReport, submitAgentFaultReport, uploadAttachment } from "./api";
import { FaultReportPage } from "./FaultReportPage";

vi.mock("./api", async (importOriginal) => ({
  ...await importOriginal<typeof import("./api")>(),
  createFaultReport: vi.fn(),
  submitAgentFaultReport: vi.fn(),
  uploadAttachment: vi.fn(),
}));

describe("FaultReportPage", () => {
  beforeEach(() => vi.clearAllMocks());
  it("preserves the approved fault-report module structure", () => {
    render(<FaultReportPage />);
    expect(screen.getByRole("heading", { name: "查询筛选" })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "故障上报列表" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "故障上报", level: 3 })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "新增故障上报" }));
    expect(screen.getByRole("heading", { name: "故障上报", level: 3 })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "基础信息" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "故障描述" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "现场附件" })).toBeInTheDocument();
  });
  it("keeps the prototype fault list columns and empty-state contract", () => {
    render(<FaultReportPage />);
    expect(screen.getByRole("region", { name: "故障上报列表" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "故障编号" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "设备名称" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "所属车间" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "所属产线" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "故障现象" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "紧急程度" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "上报时间" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "状态" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "操作" })).toBeInTheDocument();
    expect(screen.getByRole("status", { name: "故障列表状态" })).toBeInTheDocument();
  });
  it("shows an AI draft first and writes a formal fault only after explicit confirmation", async () => {
    const draft = {
      equipment_id: "eq-1", urgency: "HIGH", symptom: "液压压力异常", occurred_at: "2026-07-27T10:00:00+08:00",
      duration_minutes: 0, attachment_refs: [],
    };
    vi.mocked(submitAgentFaultReport)
      .mockResolvedValueOnce({ agent_status: "PREVIEW", draft, missing_fields: [] })
      .mockResolvedValueOnce({ id: "fault-1", number: "FR-001", status: "PENDING_ACCEPT", ...draft, agent_status: "AI_DRAFT" });
    render(<FaultReportPage />);

    fireEvent.click(screen.getByRole("button", { name: "新增故障上报" }));
    expect(screen.getByRole("heading", { name: "故障上报", level: 3 })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "AI 辅助与人工确认" })).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("设备 ID"), { target: { value: "eq-1" } });
    fireEvent.change(screen.getByLabelText("故障现象"), { target: { value: "液压压力异常" } });
    fireEvent.change(screen.getByLabelText("发生时间"), { target: { value: "2026-07-27T10:00" } });
    fireEvent.click(screen.getByRole("button", { name: "生成 AI 草稿" }));

    expect(await screen.findByText("请核对 AI 草稿后再正式提交。")).toBeInTheDocument();
    expect(submitAgentFaultReport).toHaveBeenCalledWith(expect.objectContaining({ confirmed: false }));
    fireEvent.click(screen.getByRole("button", { name: "确认并提交 AI 草稿" }));
    await waitFor(() => expect(submitAgentFaultReport).toHaveBeenLastCalledWith(expect.objectContaining({ confirmed: true })));
    expect(await screen.findByText("故障已提交：FR-001")).toBeInTheDocument();
  });

  it("keeps manual fault submission available when AI submission is unavailable", async () => {
    vi.mocked(submitAgentFaultReport).mockRejectedValue(new ApiError(503, "AGENT_CONFIG_INVALID"));
    vi.mocked(createFaultReport).mockResolvedValue({
      id: "fault-1", number: "FR-001", status: "PENDING_ACCEPT",
      equipment_id: "eq-1", urgency: "HIGH", symptom: "液压压力异常",
      occurred_at: "2026-07-27T10:00:00+08:00", attachment_refs: [],
    });
    render(<FaultReportPage />);

    fireEvent.click(screen.getByRole("button", { name: "新增故障上报" }));

    fireEvent.change(screen.getByLabelText("设备 ID"), { target: { value: "eq-1" } });
    fireEvent.change(screen.getByLabelText("故障现象"), { target: { value: "液压压力异常" } });
    fireEvent.change(screen.getByLabelText("发生时间"), { target: { value: "2026-07-27T10:00" } });
    fireEvent.click(screen.getByRole("button", { name: "生成 AI 草稿" }));

    expect(await screen.findByText("AI 故障上报暂不可用，请继续人工填写。")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "提交故障" })).toBeEnabled();
    fireEvent.click(screen.getByRole("button", { name: "提交故障" }));
    await waitFor(() => expect(createFaultReport).toHaveBeenCalledOnce());
    expect(await screen.findByText("故障已提交：FR-001")).toBeInTheDocument();
  });

  it("adds only a clean uploaded attachment to the formal fault payload", async () => {
    vi.mocked(uploadAttachment).mockResolvedValue({ object_key: "safe/file.pdf", filename: "manual.pdf", size_bytes: 12, content_type: "application/pdf" });
    vi.mocked(createFaultReport).mockResolvedValue({
      id: "fault-2", number: "FR-002", status: "PENDING_ACCEPT", equipment_id: "eq-1", urgency: "HIGH", symptom: "异响", occurred_at: "2026-07-27T10:00:00+08:00", attachment_refs: [{ object_key: "safe/file.pdf", filename: "manual.pdf", size_bytes: 12, content_type: "application/pdf" }],
    });
    render(<FaultReportPage />);
    fireEvent.click(screen.getByRole("button", { name: "新增故障上报" }));
    fireEvent.change(screen.getByLabelText("设备 ID"), { target: { value: "eq-1" } });
    fireEvent.change(screen.getByLabelText("故障现象"), { target: { value: "异响" } });
    fireEvent.change(screen.getByLabelText("发生时间"), { target: { value: "2026-07-27T10:00" } });
    fireEvent.change(screen.getByLabelText("故障附件"), { target: { files: [new File(["safe"], "manual.pdf", { type: "application/pdf" })] } });
    expect(await screen.findByText(/附件已通过安全检查/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "提交故障" }));
    await waitFor(() => expect(createFaultReport).toHaveBeenCalledWith(expect.objectContaining({ attachment_refs: [{ object_key: "safe/file.pdf", filename: "manual.pdf", size_bytes: 12, content_type: "application/pdf" }] })));
  });

  it("blocks manual and AI submissions while an attachment scan is pending", async () => {
    vi.mocked(uploadAttachment).mockImplementation(() => new Promise(() => undefined));
    render(<FaultReportPage />);
    fireEvent.click(screen.getByRole("button", { name: "新增故障上报" }));
    fireEvent.change(screen.getByLabelText("设备 ID"), { target: { value: "eq-1" } });
    fireEvent.change(screen.getByLabelText("故障现象"), { target: { value: "异响" } });
    fireEvent.change(screen.getByLabelText("发生时间"), { target: { value: "2026-07-27T10:00" } });

    fireEvent.change(screen.getByLabelText("故障附件"), { target: { files: [new File(["safe"], "manual.pdf", { type: "application/pdf" })] } });

    expect(await screen.findByText("附件正在上传并进行安全检查…")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "生成 AI 草稿" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "提交故障" })).toBeDisabled();
    expect(createFaultReport).not.toHaveBeenCalled();
    expect(submitAgentFaultReport).not.toHaveBeenCalled();
  });

  it("prevents duplicate manual submission after an AI preview and confirms the latest user edits", async () => {
    const draft = {
      equipment_id: "eq-1", urgency: "HIGH", symptom: "旧症状", occurred_at: "2026-07-27T02:00:00.000Z",
      duration_minutes: 0, attachment_refs: [],
    };
    vi.mocked(submitAgentFaultReport)
      .mockResolvedValueOnce({ agent_status: "PREVIEW", draft, missing_fields: [] })
      .mockResolvedValueOnce({ id: "fault-1", number: "FR-001", status: "PENDING_ACCEPT", ...draft, symptom: "新症状", agent_status: "AI_DRAFT" });
    render(<FaultReportPage />);
    fireEvent.click(screen.getByRole("button", { name: "新增故障上报" }));
    fireEvent.change(screen.getByLabelText("设备 ID"), { target: { value: "eq-1" } });
    fireEvent.change(screen.getByLabelText("故障现象"), { target: { value: "旧症状" } });
    fireEvent.change(screen.getByLabelText("发生时间"), { target: { value: "2026-07-27T10:00" } });
    fireEvent.click(screen.getByRole("button", { name: "生成 AI 草稿" }));

    expect(await screen.findByText("请核对 AI 草稿后再正式提交。")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("故障现象"), { target: { value: "新症状" } });
    expect(screen.getByRole("button", { name: "提交故障" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "确认并提交 AI 草稿" }));

    await waitFor(() => expect(submitAgentFaultReport).toHaveBeenLastCalledWith(expect.objectContaining({ confirmed: true, draft: expect.objectContaining({ symptom: "新症状" }) })));
    expect(createFaultReport).not.toHaveBeenCalled();
  });
});
