import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { completeRepair, runFaultDiagnosis, startRepair } from "./api";
import { RepairExecutionPage } from "./RepairExecutionPage";

vi.mock("./api", async (importOriginal) => ({
  ...await importOriginal<typeof import("./api")>(),
  runFaultDiagnosis: vi.fn(),
  startRepair: vi.fn(),
  completeRepair: vi.fn(),
}));

beforeEach(() => vi.resetAllMocks());

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

it("sends only the server draft id and user evidence when advancing diagnosis", async () => {
  vi.mocked(runFaultDiagnosis)
    .mockResolvedValueOnce({ state: "QUESTIONING", question: "请提供复现工况", evidence: [], prefill: null, summary: null, steps: 1, questions: 1, diagnosis_draft_id: "draft-3" })
    .mockResolvedValueOnce({ state: "EVIDENCE_PENDING", question: "请补充另一类证据", evidence: [{ category: "reproduction", detail: "热机后复现" }], prefill: null, summary: null, steps: 2, questions: 1, diagnosis_draft_id: "draft-3" });
  render(<RepairExecutionPage />);
  fireEvent.change(screen.getByLabelText("故障单 ID"), { target: { value: "fault-3" } });
  fireEvent.click(screen.getByRole("button", { name: "开始 AI 诊断" }));
  await screen.findByText("请提供复现工况");
  fireEvent.change(screen.getByLabelText("证据内容"), { target: { value: "热机后复现" } });
  fireEvent.click(screen.getByRole("button", { name: "提交诊断证据" }));
  expect(runFaultDiagnosis).toHaveBeenLastCalledWith({ action: "evidence", diagnosis_draft_id: "draft-3", category: "reproduction", detail: "热机后复现" });
});

it("adopts a ready diagnosis and shows its summary after repair parts notes", async () => {
  vi.mocked(runFaultDiagnosis).mockResolvedValue({
    state: "DIAGNOSIS_READY", question: null, evidence: [{ category: "reproduction", detail: "热机后复现" }],
    prefill: { actual_cause: "压力阀卡滞", actual_solution: "检查压力阀" },
    summary: { symptom: "压力异常", key_evidence: ["热机后复现"], root_cause: "压力阀卡滞" }, steps: 3, questions: 1, diagnosis_draft_id: "draft-1",
  });
  vi.mocked(startRepair).mockResolvedValue({ work_order_id: "wo-2", maintenance_record_id: "mr-2", start_mode: "ADOPTED", diagnosis_draft_id: "draft-1" });
  vi.mocked(completeRepair).mockResolvedValue({ actual_cause: "压力阀卡滞", actual_solution: "检查压力阀", repair_result: "已恢复", parts_replacement_notes: "更换压力传感器" });
  render(<RepairExecutionPage />);

  fireEvent.change(screen.getByLabelText("故障单 ID"), { target: { value: "fault-2" } });
  fireEvent.click(screen.getByRole("button", { name: "开始 AI 诊断" }));
  expect(await screen.findByRole("button", { name: "采纳 AI 建议并开始维修" })).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "采纳 AI 建议并开始维修" }));
  await screen.findByText("维修工单已创建：wo-2");
  fireEvent.change(screen.getByLabelText("备件更换说明"), { target: { value: "更换压力传感器" } });
  fireEvent.click(screen.getByRole("button", { name: "提交维修结果" }));
  expect(await screen.findByText("AI 对话摘要：压力异常；压力阀卡滞")).toBeInTheDocument();
});
