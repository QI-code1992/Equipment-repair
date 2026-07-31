import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ApiError, getHealthScore, getWorkbenchAlertSummary, getWorkbenchShortcuts, getWorkbenchTodos } from "./api";
import { WorkbenchPage } from "./WorkbenchPage";

vi.mock("./api", async (importOriginal) => ({ ...await importOriginal<typeof import("./api")>(), getHealthScore: vi.fn(), getWorkbenchTodos: vi.fn(), getWorkbenchAlertSummary: vi.fn(), getWorkbenchShortcuts: vi.fn() }));

describe("WorkbenchPage", () => {
  it("shows permission denial without static health data", async () => {
    vi.mocked(getHealthScore).mockRejectedValue(new ApiError(403, "FORBIDDEN"));
    vi.mocked(getWorkbenchTodos).mockResolvedValue({ items: [], count: 0 });
    vi.mocked(getWorkbenchAlertSummary).mockResolvedValue({ active_fault_count: 0, status_counts: [], urgency_counts: [] });
    vi.mocked(getWorkbenchShortcuts).mockResolvedValue({ items: [] });
    render(<WorkbenchPage />);
    fireEvent.change(screen.getByLabelText("设备 ID"), { target: { value: "eq-1" } });
    fireEvent.click(screen.getByRole("button", { name: "查询健康分" }));
    expect(await screen.findByText("无权查看工作台数据。")) .toBeInTheDocument();
    expect(screen.queryByText("模拟健康分")).not.toBeInTheDocument();
  });
});
