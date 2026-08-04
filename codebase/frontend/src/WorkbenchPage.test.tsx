import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { ApiError, getEquipment, getHealthScore, getWorkbenchAlertSummary, getWorkbenchShortcuts, getWorkbenchTodos } from "./api";
import { WorkbenchPage } from "./WorkbenchPage";

vi.mock("./api", async (importOriginal) => ({ ...await importOriginal<typeof import("./api")>(), getEquipment: vi.fn(), getHealthScore: vi.fn(), getWorkbenchTodos: vi.fn(), getWorkbenchAlertSummary: vi.fn(), getWorkbenchShortcuts: vi.fn() }));

describe("WorkbenchPage", () => {
  it("presents formal alerts and todo actions in the approved workbench layout", async () => {
    vi.mocked(getWorkbenchTodos).mockResolvedValue({ items: [{ id: "todo-1", number: "WO-001", equipment_name: "装载机", urgency: "HIGH", symptom: "液压温度过高", status: "PENDING_ACCEPT" }], count: 1 });
    vi.mocked(getWorkbenchAlertSummary).mockResolvedValue({ active_fault_count: 1, status_counts: [], urgency_counts: [] });
    vi.mocked(getWorkbenchShortcuts).mockResolvedValue({ items: [{ id: "shortcut-1", label: "故障上报", path: "/fault-report" }] });
    vi.mocked(getEquipment).mockResolvedValue([]);

    render(<MemoryRouter><WorkbenchPage /></MemoryRouter>);

    expect(await screen.findByRole("heading", { name: "待办处置" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "风险总览" })).toBeInTheDocument();
    expect(screen.getByText("WO-001")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /故障上报/ })).toBeInTheDocument();
  });

  it("shows permission denial without static health data", async () => {
    vi.mocked(getHealthScore).mockRejectedValue(new ApiError(403, "FORBIDDEN"));
    vi.mocked(getWorkbenchTodos).mockResolvedValue({ items: [], count: 0 });
    vi.mocked(getWorkbenchAlertSummary).mockResolvedValue({ active_fault_count: 0, status_counts: [], urgency_counts: [] });
    vi.mocked(getWorkbenchShortcuts).mockResolvedValue({ items: [] });
    vi.mocked(getEquipment).mockResolvedValue([{ id: "eq-1", code: "EQ-01", name: "装载机", model: "L-1", type: "LOADER", manufacturer: "M", manufactured_at: null, commissioned_at: null, status: "NORMAL", organization_id: "line-1", owner_user_id: null, operating_hours: 0, image_refs: [] }]);
    render(<WorkbenchPage />);
    await screen.findByRole("option", { name: "EQ-01 · 装载机" });
    fireEvent.change(screen.getByLabelText("设备 ID"), { target: { value: "eq-1" } });
    fireEvent.click(screen.getByRole("button", { name: "查询健康分" }));
    expect(await screen.findByText("无权查看工作台数据。")) .toBeInTheDocument();
    expect(screen.queryByText("模拟健康分")).not.toBeInTheDocument();
  });
});
