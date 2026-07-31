import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { BiDashboardPage, EquipmentAddPage, EquipmentLedgerPage, FactoryModelingPage, IntelligentAuditPage, MaintenanceRecordDetailPage, MaintenanceRecordsPage, SystemManagementPage } from "./PortalPages";

describe("TASK-012 portal pages", () => {
  it("renders BI only from its formal API response", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({
      summary: { fault_count: 2, active_fault_count: 1, completed_work_order_count: 1, completion_rate: 0.5 },
      trend: [], efficiency: { completed_work_order_count: 1, average_completion_hours: null }, organization_ranking: [], history_comparison: { current_fault_count: 2, previous_fault_count: 0 },
    }), { status: 200 })));

    render(<BiDashboardPage />);

    expect(await screen.findByText("2")).toBeInTheDocument();
    expect(screen.getByText("暂无排行数据。")).toBeInTheDocument();
  });

  it("reloads the BI dashboard with a selected formal organization filter", async () => {
    const dashboard = { summary: { fault_count: 2, active_fault_count: 1, completed_work_order_count: 1, completion_rate: 0.5 }, trend: [], efficiency: { completed_work_order_count: 1, average_completion_hours: 3 }, organization_ranking: [], history_comparison: { current_fault_count: 1, previous_fault_count: 0 } };
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify(dashboard), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([{ id: "line-1", type: "LINE", code: "LINE", name: "一线", parent_id: "root", enabled: true }]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(dashboard), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    render(<BiDashboardPage />);

    fireEvent.change(await screen.findByLabelText("组织筛选"), { target: { value: "line-1" } });
    await screen.findByText("平均完成 3 小时");
    expect(fetchMock.mock.calls[2][0]).toBe("/api/bi/dashboard?organization_id=line-1");
  });

  it("renders actual factory organizations instead of prototype examples", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify([
      { id: "line-1", type: "LINE", code: "LINE-01", name: "装配线", parent_id: "workshop-1", enabled: true },
    ]), { status: 200 })));

    render(<FactoryModelingPage />);

    expect(await screen.findByText("装配线")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "创建节点" })).toBeInTheDocument();
  });

  it("filters an organization tree and sends an idempotent disable update", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify([
        { id: "root", type: "ROOT", code: "ROOT", name: "根节点", parent_id: null, enabled: true, sort_order: 0, remark: "" },
        { id: "line-1", type: "LINE", code: "LINE-01", name: "装配线", parent_id: "root", enabled: true, sort_order: 0, remark: "" },
      ]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "line-1" }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    render(<FactoryModelingPage />);

    fireEvent.change(await screen.findByLabelText("搜索组织"), { target: { value: "装配" } });
    expect(screen.getByText("装配线")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "停用 装配线" }));

    await screen.findByText("组织状态已提交更新，请刷新页面确认。");
    expect(fetchMock.mock.calls[1][0]).toBe("/api/organizations/line-1");
    const init = fetchMock.mock.calls[1][1] as RequestInit;
    expect(init.method).toBe("PATCH");
    expect(new Headers(init.headers).get("Idempotency-Key")).toBeTruthy();
  });

  it("shows an empty maintenance state instead of fabricated records", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ items: [], count: 0, page: 1, page_size: 20 }), { status: 200 })));

    render(<MaintenanceRecordsPage />);

    expect(await screen.findByText("暂无可展示的正式业务数据。")).toBeInTheDocument();
  });

  it("loads a maintenance-record detail only through its formal detail endpoint", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({
      maintenance_record_id: "record-1", work_order_id: "order-1", fault_report_id: "fault-1", equipment_id: "eq-1", work_order_number: "WO-1", status: "COMPLETED", symptom: "异响", actual_cause: "轴承磨损", actual_solution: "更换轴承", repair_result: "通过", completed_at: "2026-07-31T00:00:00Z", knowledge_status: "NOT_LINKED", start_mode: "DIRECT", parts_replacement_notes: "轴承", created_at: "2026-07-31T00:00:00Z", updated_at: "2026-07-31T00:00:00Z",
    }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    render(<MemoryRouter initialEntries={["/maintenance-records/record-1"]}><Routes><Route path="/maintenance-records/:id" element={<MaintenanceRecordDetailPage />} /></Routes></MemoryRouter>);

    expect(await screen.findByText("轴承磨损")).toBeInTheDocument();
    expect(screen.getByText("NOT_LINKED")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith("/api/maintenance-records/record-1", undefined);
  });

  it("filters the equipment ledger with real loaded equipment", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify([
      { id: "eq-1", code: "EQ-01", name: "液压装载机", model: "L-1", type: "LOADER", manufacturer: "M", status: "NORMAL", organization_id: "line-1", owner_user_id: null, operating_hours: 4 },
      { id: "eq-2", code: "EQ-02", name: "电驱装载机", model: "L-2", type: "LOADER", manufacturer: "M", status: "FAULT", organization_id: "line-2", owner_user_id: null, operating_hours: 5 },
    ]), { status: 200 })));

    render(<MemoryRouter><EquipmentLedgerPage /></MemoryRouter>);

    fireEvent.change(await screen.findByLabelText("筛选设备"), { target: { value: "电驱" } });
    expect(screen.getByText("电驱装载机")).toBeInTheDocument();
    expect(screen.queryByText("液压装载机")).not.toBeInTheDocument();
  });

  it("creates equipment with enabled line and user options from formal APIs", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify([
        { id: "factory", type: "FACTORY", code: "FAC", name: "工厂", parent_id: "root", enabled: true },
        { id: "line-1", type: "LINE", code: "LINE", name: "一线", parent_id: "factory", enabled: true },
      ]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([{ id: "user-1", username: "owner", enabled: true, role_ids: [] }]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "eq-1" }), { status: 201 }));
    vi.stubGlobal("fetch", fetchMock);

    render(<MemoryRouter><EquipmentAddPage /></MemoryRouter>);

    expect(await screen.findByRole("option", { name: "一线" })).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("设备编码"), { target: { value: "EQ-01" } });
    fireEvent.change(screen.getByLabelText("设备名称"), { target: { value: "装载机" } });
    fireEvent.change(screen.getByLabelText("型号"), { target: { value: "L-1" } });
    fireEvent.change(screen.getByLabelText("类型"), { target: { value: "LOADER" } });
    fireEvent.change(screen.getByLabelText("制造商"), { target: { value: "M" } });
    fireEvent.change(screen.getByLabelText("负责人"), { target: { value: "user-1" } });
    fireEvent.click(screen.getByRole("button", { name: "保存" }));

    await screen.findByText("已保存正式设备数据。");
    expect(fetchMock.mock.calls[2][0]).toBe("/api/equipment");
    const init = fetchMock.mock.calls[2][1] as RequestInit;
    expect(new Headers(init.headers).get("Idempotency-Key")).toBeTruthy();
    expect(JSON.parse(String(init.body))).toMatchObject({ organization_id: "line-1", owner_user_id: "user-1" });
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

  it("submits a role permission update with an idempotency key", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [], count: 0, page: 1, page_size: 20 }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([{ id: "user-1", username: "operator", enabled: true, role_ids: ["role-1"] }]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([{ id: "role-1", code: "LINE_OPERATOR", name: "操作员", permission_codes: ["workbench:view"] }]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([{ code: "workbench:view" }, { code: "fault:create" }]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "role-1" }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    render(<MemoryRouter><SystemManagementPage /></MemoryRouter>);

    (await screen.findByRole("button", { name: "保存角色权限" })).click();

    await screen.findByText("角色权限已提交更新，请刷新列表确认。");
    expect(fetchMock.mock.calls[4][0]).toBe("/api/roles/role-1/permissions");
    const init = fetchMock.mock.calls[4][1] as RequestInit;
    expect(init.method).toBe("PATCH");
    expect(new Headers(init.headers).get("Idempotency-Key")).toBeTruthy();
  });

  it("lets an administrator select formal permission codes before saving a role", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [], count: 0, page: 1, page_size: 20 }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([{ id: "role-1", code: "LINE_OPERATOR", name: "操作员", permission_codes: ["workbench:view"] }]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([{ code: "workbench:view" }, { code: "fault:create" }]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "role-1" }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    render(<MemoryRouter><SystemManagementPage /></MemoryRouter>);

    const checkbox = await screen.findByRole("checkbox", { name: "fault:create" });
    fireEvent.click(checkbox);
    fireEvent.click(screen.getByRole("button", { name: "保存角色权限" }));

    await screen.findByText("角色权限已提交更新，请刷新列表确认。");
    expect(JSON.parse(String((fetchMock.mock.calls[4][1] as RequestInit).body))).toEqual({
      permission_codes: ["workbench:view", "fault:create"],
    });
  });

  it("labels configured token budgets without claiming actual model consumption", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({
        items: [{ agent_id: "operation_guidance", status: "COMPLETED", run_count: 2, configured_max_reply_tokens: 512 }],
        count: 1, retention_days: 30, token_measurement: "configured_max_reply_tokens_not_actual_usage",
      }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [], count: 0, page: 1, page_size: 20 }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    render(<IntelligentAuditPage />);

    expect(await screen.findByText("operation_guidance")).toBeInTheDocument();
    expect(screen.getByText(/配置 Token 预算统计，不代表模型实际消耗/)).toBeInTheDocument();
    expect(screen.getByText("512")).toBeInTheDocument();
  });
});
