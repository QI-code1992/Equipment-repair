import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { runFaultDiagnosis, startRepair } from "./api";
import { RepairExecutionPage } from "./RepairExecutionPage";

vi.mock("./api", async (importOriginal) => ({
  ...await importOriginal<typeof import("./api")>(),
  runFaultDiagnosis: vi.fn(),
  startRepair: vi.fn(),
}));

describe("RepairExecutionPage", () => {
  it("keeps direct start available when evidence is insufficient", async () => {
    vi.mocked(runFaultDiagnosis).mockResolvedValue({
      state: "EVIDENCE_PENDING", question: "请补充报警码", evidence: [], prefill: null,
      summary: null, steps: 2, questions: 1, diagnosis_draft_id: "draft-1",
    });
    vi.mocked(startRepair).mockResolvedValue({ work_order_id: "wo-1", maintenance_record_id: "mr-1", start_mode: "DIRECT", diagnosis_draft_id: null });
    render(<RepairExecutionPage />);

    fireEvent.change(screen.getByLabelText("故障单 ID"), { target: { value: "fault-1" } });
    fireEvent.click(screen.getByRole("button", { name: "开始 AI 诊断" }));
    expect(await screen.findByText("证据仍不足，可补充信息或直接开始维修。")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "采纳 AI 建议并开始维修" })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "直接开始维修" }));
    expect(await screen.findByText("维修工单已创建：wo-1")).toBeInTheDocument();
    expect(startRepair).toHaveBeenCalledWith("fault-1", { mode: "DIRECT" });
  });
});
