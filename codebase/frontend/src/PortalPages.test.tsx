import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { BiDashboardPage, FactoryModelingPage, MaintenanceRecordsPage, SystemManagementPage } from "./PortalPages";

describe("TASK-012 portal pages", () => {
  it("renders BI only from its formal API response", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({
      summary: { fault_count: 2, active_fault_count: 1, completed_work_order_count: 1, completion_rate: 0.5 },
      trend: [], organization_ranking: [],
    }), { status: 200 })));

    render(<BiDashboardPage />);

    expect(await screen.findByText("2")).toBeInTheDocument();
    expect(screen.getByText("暂无排行数据。")).toBeInTheDocument();
  });

  it("renders actual factory organizations instead of prototype examples", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify([
      { id: "line-1", type: "LINE", code: "LINE-01", name: "装配线", parent_id: "workshop-1", enabled: true },
    ]), { status: 200 })));

    render(<FactoryModelingPage />);

    expect(await screen.findByText("装配线")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "创建节点" })).toBeInTheDocument();
  });

  it("shows an empty maintenance state instead of fabricated records", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ items: [], count: 0, page: 1, page_size: 20 }), { status: 200 })));

    render(<MaintenanceRecordsPage />);

    expect(await screen.findByText("暂无可展示的正式业务数据。")).toBeInTheDocument();
  });

  it("keeps management lists behind their formal endpoints", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [], count: 0, page: 1, page_size: 20 }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    render(<MemoryRouter><SystemManagementPage /></MemoryRouter>);

    expect(await screen.findAllByText("暂无可展示的正式业务数据。")).toHaveLength(4);
    expect(fetchMock.mock.calls.map(([path]) => path)).toEqual([
      "/api/audit-events", "/api/users", "/api/roles", "/api/permissions",
    ]);
  });
});
