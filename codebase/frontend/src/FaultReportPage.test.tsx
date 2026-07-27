import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ApiError, createFaultReport, submitAgentFaultReport } from "./api";
import { FaultReportPage } from "./FaultReportPage";

vi.mock("./api", async (importOriginal) => ({
  ...await importOriginal<typeof import("./api")>(),
  createFaultReport: vi.fn(),
  submitAgentFaultReport: vi.fn(),
}));

describe("FaultReportPage", () => {
  it("keeps manual fault submission available when AI submission is unavailable", async () => {
    vi.mocked(submitAgentFaultReport).mockRejectedValue(new ApiError(503, "AGENT_CONFIG_INVALID"));
    vi.mocked(createFaultReport).mockResolvedValue({
      id: "fault-1", number: "FR-001", status: "PENDING_ACCEPT",
      equipment_id: "eq-1", urgency: "HIGH", symptom: "液压压力异常",
      occurred_at: "2026-07-27T10:00:00+08:00", attachment_refs: [],
    });
    render(<FaultReportPage />);

    fireEvent.change(screen.getByLabelText("设备 ID"), { target: { value: "eq-1" } });
    fireEvent.change(screen.getByLabelText("故障现象"), { target: { value: "液压压力异常" } });
    fireEvent.change(screen.getByLabelText("发生时间"), { target: { value: "2026-07-27T10:00" } });
    fireEvent.click(screen.getByRole("button", { name: "使用 AI 整理" }));

    expect(await screen.findByText("AI 故障上报暂不可用，请继续人工填写。")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "提交故障" })).toBeEnabled();
    fireEvent.click(screen.getByRole("button", { name: "提交故障" }));
    await waitFor(() => expect(createFaultReport).toHaveBeenCalledOnce());
    expect(await screen.findByText("故障已提交：FR-001")).toBeInTheDocument();
  });
});
