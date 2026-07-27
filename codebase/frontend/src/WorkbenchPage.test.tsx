import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ApiError, getHealthScore } from "./api";
import { WorkbenchPage } from "./WorkbenchPage";

vi.mock("./api", async (importOriginal) => ({ ...await importOriginal<typeof import("./api")>(), getHealthScore: vi.fn() }));

describe("WorkbenchPage", () => {
  it("shows permission denial without static health data", async () => {
    vi.mocked(getHealthScore).mockRejectedValue(new ApiError(403, "FORBIDDEN"));
    render(<WorkbenchPage />);
    fireEvent.change(screen.getByLabelText("设备 ID"), { target: { value: "eq-1" } });
    fireEvent.click(screen.getByRole("button", { name: "查询健康分" }));
    expect(await screen.findByText("无权查看工作台数据。")) .toBeInTheDocument();
    expect(screen.queryByText("模拟健康分")).not.toBeInTheDocument();
  });
});
