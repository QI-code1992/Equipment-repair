import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { AgentReportPage, BiDashboardPage, EquipmentAddPage, EquipmentDetailPage, EquipmentEditPage, EquipmentLedgerPage, FactoryModelingPage, IntelligentAuditPage, MaintenanceRecordDetailPage, MaintenanceRecordsPage, SystemManagementPage } from "./PortalPages";

describe("TASK-012 portal pages", () => {
  it("renders BI only from its formal API response", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({
      summary: { fault_count: 2, active_fault_count: 1, completed_work_order_count: 1, completion_rate: 0.5 },
      trend: [], efficiency: { completed_work_order_count: 1, average_completion_hours: null }, organization_ranking: [], history_comparison: { current_fault_count: 2, previous_fault_count: 0 },
    }), { status: 200 })));

    render(<BiDashboardPage />);

    expect(await screen.findByText("2")).toBeInTheDocument();
    expect(screen.getByText("暂无趋势数据。")).toBeInTheDocument();
  });

  it("renders a semantic BI trend chart from formal API series values", async () => {
    vi.stubGlobal("fetch", vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({
        summary: { fault_count: 3, active_fault_count: 1, completed_work_order_count: 2, completion_rate: 0.67 },
        trend: [{ date: "2026-08-01", fault_count: 3, completed_work_order_count: 1 }, { date: "2026-08-02", fault_count: 1, completed_work_order_count: 2 }],
        efficiency: { completed_work_order_count: 2, average_completion_hours: 3 }, organization_ranking: [], history_comparison: { current_fault_count: 3, previous_fault_count: 2 },
      }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 })));

    render(<BiDashboardPage />);

    expect(await screen.findByRole("img", { name: "故障与完成工单趋势" })).toBeInTheDocument();
    expect(screen.getByText("2026-08-01：故障 3，完成 1")).toBeInTheDocument();
  });

  it("keeps the approved BI module order and labels while using only formal response data", async () => {
    vi.stubGlobal("fetch", vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({
        summary: { fault_count: 3, active_fault_count: 1, completed_work_order_count: 2, completion_rate: 0.67 },
        trend: [], efficiency: { completed_work_order_count: 2, average_completion_hours: 4 }, organization_ranking: [], history_comparison: { current_fault_count: 3, previous_fault_count: 2 },
      }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 })));

    render(<BiDashboardPage />);

    expect(await screen.findByRole("heading", { name: "管理摘要" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "趋势分析" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "效率分析" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "设备健康列表" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "指标历史对比" })).toBeInTheDocument();
    expect(screen.getByText("设备健康综合评分")).toBeInTheDocument();
    expect(screen.getByText("工单总数")).toBeInTheDocument();
    expect(screen.getByText("工单按时完成率")).toBeInTheDocument();
    expect(screen.getByText("平均维修时长 MTTR")).toBeInTheDocument();
    expect(screen.getByRole("group", { name: "趋势粒度" })).toBeInTheDocument();
    expect(screen.queryByLabelText("图表视图")).not.toBeInTheDocument();
    expect(screen.getAllByText("当前 API 未提供设备健康列表数据。")).toHaveLength(2);
    expect(screen.getByText("当前 API 未提供指标历史对比数据。")).toBeInTheDocument();
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

    expect(await screen.findByRole("button", { name: "装配线 LINE-01" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "新增下级节点" })).not.toBeInTheDocument();
  });

  it("uses the approved factory-modeling workspace instead of a permanent create form", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify([
      { id: "factory-1", type: "FACTORY", code: "FAC-01", name: "新能源一厂", parent_id: null, enabled: true, sort_order: 1, remark: "总装基地" },
      { id: "line-1", type: "LINE", code: "LINE-01", name: "总装一线", parent_id: "factory-1", enabled: true, sort_order: 1, remark: "主产线" },
    ]), { status: 200 })));

    render(<FactoryModelingPage permissionCodes={["organization:read", "organization:write"]} />);

    expect(await screen.findByRole("heading", { name: "组织结构树" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "节点详情" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "新能源一厂 FAC-01" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "新增下级节点" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "新增组织节点" })).not.toBeInTheDocument();
  });

  it("filters an organization tree and sends an idempotent disable update", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify([
        { id: "root", type: "ROOT", code: "ROOT", name: "根节点", parent_id: null, enabled: true, sort_order: 0, remark: "" },
        { id: "line-1", type: "LINE", code: "LINE-01", name: "装配线", parent_id: "root", enabled: true, sort_order: 0, remark: "" },
      ]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "line-1" }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    render(<FactoryModelingPage />);

    fireEvent.change(await screen.findByLabelText("搜索组织"), { target: { value: "装配" } });
    expect(screen.getByRole("button", { name: "装配线" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "装配线" }));
    fireEvent.click(screen.getByRole("button", { name: "停用" }));
    expect(screen.getByRole("dialog", { name: "停用确认" })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole("button", { name: "确认" }));

    await screen.findByText("组织状态已更新。");
    expect(fetchMock.mock.calls[1][0]).toBe("/api/organizations/line-1");
    const init = fetchMock.mock.calls[1][1] as RequestInit;
    expect(init.method).toBe("PATCH");
    expect(new Headers(init.headers).get("Idempotency-Key")).toBeTruthy();
  });

  it("shows an empty maintenance state instead of fabricated records", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ items: [], count: 0, page: 1, page_size: 20 }), { status: 200 })));

    render(<MemoryRouter><MaintenanceRecordsPage /></MemoryRouter>);

    fireEvent.click(await screen.findByRole("tab", { name: "维修记录列表" }));
    expect(await screen.findByText("暂无可展示的正式维修记录。")).toBeInTheDocument();
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

  it("renders the real equipment repair trend returned by API-003", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "eq-1", code: "EQ-1", name: "设备", model: "M", type: "LOADER", manufacturer: "厂", status: "NORMAL", organization_id: "line", owner_user_id: null, operating_hours: 1 }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [], count: 0, page: 1, page_size: 20, trend: [{ date: "2026-07-30", completed_count: 2 }] }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    render(<MemoryRouter initialEntries={["/equipment/eq-1"]}><Routes><Route path="/equipment/:id" element={<EquipmentDetailPage />} /></Routes></MemoryRouter>);
    expect(await screen.findByText(/2026-07-30：完成 2 次/)).toBeInTheDocument();
  });

  it("groups the equipment detail header into the approved prototype overview regions", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "eq-1", code: "EQ-1", name: "设备", model: "M", type: "LOADER", manufacturer: "厂", status: "NORMAL", organization_id: "line", owner_user_id: null, operating_hours: 1, manufactured_at: "2026-01-01", commissioned_at: "2026-02-01", image_refs: [] }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [], count: 0, page: 1, page_size: 20, trend: [] }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    render(<MemoryRouter initialEntries={["/equipment/eq-1"]}><Routes><Route path="/equipment/:id" element={<EquipmentDetailPage />} /></Routes></MemoryRouter>);

    expect(await screen.findByRole("heading", { name: "EQ-1 · 设备（M）" })).toBeInTheDocument();
    expect(screen.getByLabelText("设备图片")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "查看健康评分明细" })).toBeInTheDocument();
    expect(screen.getByText("负责人")).toBeInTheDocument();
    expect(screen.getByText("最近异常")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "维修历史" })).toBeInTheDocument();
  });

  it("opens the prototype health-score detail surface using the formal health API", async () => {
    vi.stubGlobal("fetch", vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "eq-1", code: "EQ-1", name: "设备", model: "M", type: "LOADER", manufacturer: "厂", status: "NORMAL", organization_id: "line", owner_user_id: null, operating_hours: 1, image_refs: [] }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [], count: 0, page: 1, page_size: 20, trend: [] }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ status: "LOW_RISK", score: 82 }), { status: 200 })));

    render(<MemoryRouter initialEntries={["/equipment/eq-1"]}><Routes><Route path="/equipment/:id" element={<EquipmentDetailPage />} /></Routes></MemoryRouter>);

    expect(await screen.findByText("82")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "查看健康评分明细" }));
    expect(screen.getByRole("dialog", { name: "健康评分明细" })).toBeInTheDocument();
    expect(screen.getByText("82 分")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "关闭健康评分明细" }));
    expect(screen.queryByRole("dialog", { name: "健康评分明细" })).not.toBeInTheDocument();
  });

  it("renders the prototype equipment detail tab structure without inventing unavailable data", async () => {
    vi.stubGlobal("fetch", vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "eq-1", code: "EQ-1", name: "设备", model: "M", type: "LOADER", manufacturer: "厂", status: "NORMAL", organization_id: "line", owner_user_id: null, operating_hours: 1, manufactured_at: null, commissioned_at: null, image_refs: [] }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [], count: 0, page: 1, page_size: 20, trend: [] }), { status: 200 })));

    render(<MemoryRouter initialEntries={["/equipment/eq-1"]}><Routes><Route path="/equipment/:id" element={<EquipmentDetailPage />} /></Routes></MemoryRouter>);

    expect(await screen.findByRole("tab", { name: "图谱关系" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "BOM 组成" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "额定参数" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "知识文档" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("tab", { name: "知识文档" }));
    expect(screen.getByText("知识文档接口尚未提供，当前仅展示正式字段状态。" )).toBeInTheDocument();
  });

  it("keeps each equipment detail prototype tab's visual structure without fabricated records", async () => {
    vi.stubGlobal("fetch", vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "eq-1", code: "EQ-1", name: "设备", model: "M", type: "LOADER", manufacturer: "厂", status: "NORMAL", organization_id: "line", owner_user_id: null, operating_hours: 1, manufactured_at: null, commissioned_at: null, image_refs: [] }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [], count: 0, page: 1, page_size: 20, trend: [] }), { status: 200 })));
    render(<MemoryRouter initialEntries={["/equipment/eq-1"]}><Routes><Route path="/equipment/:id" element={<EquipmentDetailPage />} /></Routes></MemoryRouter>);

    expect(await screen.findByRole("region", { name: "知识图谱" })).toBeInTheDocument();
    expect(screen.getByText("当前 API 未提供设备知识图谱数据。" )).toBeInTheDocument();
    fireEvent.click(screen.getByRole("tab", { name: "BOM 组成" }));
    expect(screen.getByRole("tree", { name: "BOM 组成" })).toBeInTheDocument();
    expect(screen.getByText("当前 API 未提供 BOM 数据。" )).toBeInTheDocument();
    fireEvent.click(screen.getByRole("tab", { name: "额定参数" }));
    expect(screen.getByRole("table", { name: "额定参数" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("tab", { name: "知识文档" }));
    expect(screen.getByRole("table", { name: "知识文档" })).toBeInTheDocument();
  });

  it("keeps the approved equipment detail overview modules visible", async () => {
    vi.stubGlobal("fetch", vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "eq-1", code: "EQ-1", name: "设备", model: "M", type: "LOADER", manufacturer: "厂", status: "NORMAL", organization_id: "line", owner_user_id: null, operating_hours: 1, image_refs: [] }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [], count: 0, page: 1, page_size: 20, trend: [] }), { status: 200 })));
    render(<MemoryRouter initialEntries={["/equipment/eq-1"]}><Routes><Route path="/equipment/:id" element={<EquipmentDetailPage />} /></Routes></MemoryRouter>);
    expect(await screen.findByText("最近异常")).toBeInTheDocument();
    expect(screen.getByText("BOM 节点")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "查看健康评分明细" }));
    expect(screen.getByText("当前 API 未提供健康评分构成。")).toBeInTheDocument();
  });

  it("keeps the approved maintenance detail modules visible", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ maintenance_record_id: "record-1", work_order_id: "order-1", fault_report_id: "fault-1", equipment_id: "eq-1", work_order_number: "WO-1", status: "COMPLETED", symptom: "异响", actual_cause: null, actual_solution: null, repair_result: "通过", completed_at: null, knowledge_status: "NOT_LINKED", start_mode: "DIRECT", parts_replacement_notes: null, created_at: "2026-08-01T00:00:00Z", updated_at: "2026-08-01T00:00:00Z" }), { status: 200 })));
    render(<MemoryRouter initialEntries={["/maintenance-records/record-1"]}><Routes><Route path="/maintenance-records/:id" element={<MaintenanceRecordDetailPage />} /></Routes></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "故障摘要" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "附件证据" })).toBeInTheDocument();
  });

  it("keeps prototype equipment form sections visible when APIs are unavailable", async () => {
    vi.stubGlobal("fetch", vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify([{ id: "line-1", type: "LINE", code: "LINE", name: "一线", parent_id: "factory", enabled: true }]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 })));

    render(<MemoryRouter><EquipmentAddPage /></MemoryRouter>);

    expect(await screen.findByRole("heading", { name: "设备 BOM 组成" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "设备额定参数" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "知识资料" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "新增分支节点" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "新增参数" })).toBeDisabled();
    expect(screen.getByText("分枝节点编码")).toBeInTheDocument();
    expect(screen.getByText("额定参数值")).toBeInTheDocument();
    expect(screen.getAllByText("当前 API 未提供该模块数据，未生成演示内容。")).toHaveLength(3);
  });

  it("keeps the equipment form top actions and required-field hierarchy from the prototype", async () => {
    vi.stubGlobal("fetch", vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify([{ id: "line-1", type: "LINE", code: "LINE", name: "一线", parent_id: "factory", enabled: true }]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 })));

    render(<MemoryRouter><EquipmentAddPage /></MemoryRouter>);

    expect((await screen.findAllByRole("button", { name: "保存设备" })).length).toBe(2);
    expect(screen.getAllByText((_, node) => node?.textContent === "设备编号 *")).not.toHaveLength(0);
    expect(screen.getAllByText((_, node) => node?.textContent === "设备名称 *")).not.toHaveLength(0);
    expect(screen.getAllByText((_, node) => node?.textContent === "设备型号 *")).not.toHaveLength(0);
    expect(screen.getAllByText((_, node) => node?.textContent === "所属工厂 *")).not.toHaveLength(0);
    expect(screen.getAllByText((_, node) => node?.textContent === "负责人（可多选）*")).not.toHaveLength(0);
  });

  it("sends the selected knowledge status to the maintenance-record API", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [{ maintenance_record_id: "r-1", work_order_number: "WO-1", status: "COMPLETED", symptom: "异响", repair_result: "通过", knowledge_status: "NOT_LINKED" }], count: 1, page: 1, page_size: 20 }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [], count: 0, page: 1, page_size: 20 }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    render(<MemoryRouter><MaintenanceRecordsPage /></MemoryRouter>);
    fireEvent.change(await screen.findByLabelText("维修记录知识状态筛选"), { target: { value: "LINKED" } });
    fireEvent.click(screen.getByRole("tab", { name: "维修记录列表" }));
    await screen.findByText("暂无可展示的正式维修记录。");
    expect(fetchMock.mock.calls[1][0]).toBe("/api/maintenance-records?knowledge_status=LINKED");
  });

  it("presents maintenance records inside a searchable formal workspace", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ items: [{ maintenance_record_id: "r-1", work_order_number: "WO-1", equipment_id: "eq-1", status: "COMPLETED", symptom: "异响", repair_result: "通过", knowledge_status: "LINKED" }], count: 1, page: 1, page_size: 20 }), { status: 200 })));

    render(<MemoryRouter><MaintenanceRecordsPage /></MemoryRouter>);

    expect(await screen.findByRole("heading", { name: "维修记录检索" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("tab", { name: "维修记录列表" }));
    expect(screen.getByRole("heading", { name: "维修记录列表" })).toBeInTheDocument();
  });

  it("keeps the approved maintenance overview modules without fabricating analytics", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ items: [{ maintenance_record_id: "r-1", work_order_number: "WO-1", equipment_id: "eq-1", status: "COMPLETED", symptom: "异响", repair_result: "通过", knowledge_status: "LINKED" }], count: 1, page: 1, page_size: 20 }), { status: 200 })));

    render(<MemoryRouter><MaintenanceRecordsPage /></MemoryRouter>);

    expect(await screen.findByRole("heading", { name: "故障类型分布" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "维修时长分布" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "设备状态分布" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "故障次数趋势" })).toBeInTheDocument();
    expect(screen.getByText("当前 API 未提供故障类型分布数据。")).toBeInTheDocument();
  });

  it("keeps the complete prototype maintenance overview and record table structure", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ items: [], count: 0, page: 1, page_size: 20 }), { status: 200 })));

    render(<MemoryRouter><MaintenanceRecordsPage /></MemoryRouter>);

    expect(await screen.findByRole("region", { name: "维修概览指标" })).toBeInTheDocument();
    for (const label of ["总维修次数", "待处理维修", "平均修复时间 MTTR", "平均故障间隔 MTBF", "平均维修时间", "维修完成率"]) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
    expect(screen.getByRole("region", { name: "维修概览图表" })).toBeInTheDocument();
    for (const label of ["故障类型分布图", "维修时长分布图", "设备状态分布图", "故障次数趋势图"]) {
      expect(screen.getByRole("img", { name: label })).toBeInTheDocument();
    }

    fireEvent.click(screen.getByRole("tab", { name: "维修记录列表" }));
    expect(await screen.findByRole("table", { name: "维修记录列表" })).toBeInTheDocument();
    for (const heading of ["序号", "维修记录编号", "所属车间", "所属产线", "异常信息", "工单状态", "维修负责人", "处理结果", "完成时间"]) {
      expect(screen.getByRole("columnheader", { name: heading })).toBeInTheDocument();
    }
  });

  it("filters the equipment ledger with real loaded equipment", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify([
      { id: "eq-1", code: "EQ-01", name: "液压装载机", model: "L-1", type: "LOADER", manufacturer: "M", status: "NORMAL", organization_id: "line-1", owner_user_id: null, operating_hours: 4 },
      { id: "eq-2", code: "EQ-02", name: "电驱装载机", model: "L-2", type: "LOADER", manufacturer: "M", status: "FAULT", organization_id: "line-2", owner_user_id: null, operating_hours: 5 },
    ]), { status: 200 })));

    render(<MemoryRouter><EquipmentLedgerPage /></MemoryRouter>);

    fireEvent.change(await screen.findByLabelText("设备名称筛选"), { target: { value: "电驱" } });
    expect(screen.getByText("电驱装载机")).toBeInTheDocument();
    expect(screen.queryByText("液压装载机")).not.toBeInTheDocument();
  });

  it("uses formal equipment fields for ledger rendering without inventing health scores", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify([
      { id: "eq-1", code: "EQ-01", name: "液压装载机", model: "L-1", type: "LOADER", manufacturer: "M", status: "NORMAL", organization_id: "line-1", owner_user_id: null, operating_hours: 4 },
      { id: "eq-2", code: "EQ-02", name: "电驱装载机", model: "L-2", type: "LOADER", manufacturer: "M", status: "FAULT", organization_id: "line-2", owner_user_id: null, operating_hours: 5 },
    ]), { status: 200 })));

    render(<MemoryRouter><EquipmentLedgerPage /></MemoryRouter>);

    expect(await screen.findByText("液压装载机")).toBeInTheDocument();
    expect(screen.getByText("电驱装载机")).toBeInTheDocument();
    expect(screen.getAllByText("当前 API 未提供")).toHaveLength(2);
    expect(screen.getByText("设备总数 2 台；当前显示 2 台。")).toBeInTheDocument();
  });

  it("keeps the equipment ledger filter and seven-column table aligned with the approved prototype", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify([
      { id: "eq-1", code: "EQ-01", name: "液压装载机", model: "L-1", type: "LOADER", manufacturer: "M", status: "NORMAL", organization_id: "line-1", owner_user_id: "owner-1", operating_hours: 4 },
    ]), { status: 200 })));

    render(<MemoryRouter><EquipmentLedgerPage /></MemoryRouter>);

    expect(await screen.findByRole("heading", { name: "设备列表" })).toBeInTheDocument();
    expect(screen.getByLabelText("健康评分筛选")).toBeInTheDocument();
    for (const heading of ["序号", "设备编号", "设备名称", "型号", "负责人", "健康评分", "操作"]) {
      expect(screen.getByRole("columnheader", { name: heading })).toBeInTheDocument();
    }
    expect(screen.queryByRole("heading", { name: "资产列表" })).not.toBeInTheDocument();
    expect(screen.queryByRole("columnheader", { name: "设备身份" })).not.toBeInTheDocument();
    expect(screen.getByText("owner-1")).toBeInTheDocument();
    expect(screen.getByText("设备总数 1 台；当前显示 1 台。")).toBeInTheDocument();
  });

  it("filters the equipment ledger by the real organization hierarchy", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify([
        { id: "eq-1", code: "EQ-01", name: "一号装载机", model: "L-1", type: "LOADER", manufacturer: "M", status: "NORMAL", organization_id: "line-a", owner_user_id: null, operating_hours: 4 },
        { id: "eq-2", code: "EQ-02", name: "二号装载机", model: "L-2", type: "LOADER", manufacturer: "M", status: "FAULT", organization_id: "line-b", owner_user_id: null, operating_hours: 5 },
      ]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([
        { id: "factory-a", type: "FACTORY", code: "FAC-A", name: "华东总装厂", parent_id: null, enabled: true },
        { id: "workshop-a", type: "WORKSHOP", code: "WS-A", name: "总装车间", parent_id: "factory-a", enabled: true },
        { id: "line-a", type: "LINE", code: "LINE-A", name: "A1 产线", parent_id: "workshop-a", enabled: true },
        { id: "factory-b", type: "FACTORY", code: "FAC-B", name: "西南保障中心", parent_id: null, enabled: true },
        { id: "line-b", type: "LINE", code: "LINE-B", name: "B1 产线", parent_id: "factory-b", enabled: true },
      ]), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    render(<MemoryRouter><EquipmentLedgerPage /></MemoryRouter>);

    fireEvent.change(await screen.findByLabelText("设备所属工厂"), { target: { value: "factory-a" } });
    expect(screen.getByText("一号装载机")).toBeInTheDocument();
    expect(screen.queryByText("二号装载机")).not.toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "设备所属车间" })).not.toBeDisabled();
  });

  it("keeps the equipment creation action available when the ledger is empty", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify([]), { status: 200 })));

    render(<MemoryRouter><EquipmentLedgerPage /></MemoryRouter>);

    expect(await screen.findByRole("link", { name: "新增设备" })).toHaveAttribute("href", "/equipment/new");
    expect(screen.getByText("尚未登记正式设备。")) .toBeInTheDocument();
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
    fireEvent.click(screen.getAllByRole("button", { name: "保存设备" })[0]);

    await screen.findByText("已保存正式设备数据。");
    expect(fetchMock.mock.calls[2][0]).toBe("/api/equipment");
    const init = fetchMock.mock.calls[2][1] as RequestInit;
    expect(new Headers(init.headers).get("Idempotency-Key")).toBeTruthy();
    expect(JSON.parse(String(init.body))).toMatchObject({ organization_id: "line-1", owner_user_id: "user-1" });
  });

  it("preserves editable equipment dates and image refs instead of clearing formal fields", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({
        id: "eq-1", code: "EQ-01", name: "装载机", model: "L-1", type: "LOADER", manufacturer: "M",
        manufactured_at: "2026-01-10", commissioned_at: "2026-02-01", operating_hours: 12,
        status: "NORMAL", organization_id: "line-1", owner_user_id: "user-1",
        image_refs: [{ object_key: "equipment/eq-1.png", filename: "eq-1.png" }],
      }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([{ id: "line-1", type: "LINE", code: "LINE", name: "一线", parent_id: "factory", enabled: true }]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([{ id: "user-1", username: "owner", enabled: true, role_ids: [] }]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "eq-1" }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    render(<MemoryRouter initialEntries={["/equipment/eq-1/edit"]}><Routes><Route path="/equipment/:id/edit" element={<EquipmentEditPage />} /></Routes></MemoryRouter>);

    expect(await screen.findByDisplayValue("2026-01-10")).toBeInTheDocument();
    expect(screen.getByDisplayValue("2026-02-01")).toBeInTheDocument();
    expect(screen.getByDisplayValue("equipment/eq-1.png")).toBeInTheDocument();
    fireEvent.click(screen.getAllByRole("button", { name: "保存修改" })[0]);

    await screen.findByText("已保存正式设备数据。");
    const init = fetchMock.mock.calls[3][1] as RequestInit;
    expect(JSON.parse(String(init.body))).toMatchObject({
      manufactured_at: "2026-01-10",
      commissioned_at: "2026-02-01",
      image_refs: [{ object_key: "equipment/eq-1.png", filename: "eq-1.png" }],
    });
  });

  it("keeps management lists behind their formal endpoints", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [], count: 0, page: 1, page_size: 20 }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    render(<MemoryRouter><SystemManagementPage /></MemoryRouter>);

    expect(await screen.findByText("暂无可展示的正式业务数据。")).toBeInTheDocument();
    expect(fetchMock.mock.calls.map(([path]) => path)).toEqual([
      "/api/audit-events", "/api/users", "/api/roles", "/api/permissions", "/api/organizations",
    ]);
  });

  it("organizes system management into permission-aware tabs", async () => {
    vi.stubGlobal("fetch", vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [], count: 0, page: 1, page_size: 20 }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([{ id: "org-1", type: "FACTORY", code: "FAC-01", name: "新能源一厂", parent_id: null, enabled: true }]), { status: 200 })));

    render(<MemoryRouter><SystemManagementPage permissionCodes={["identity:read"]} /></MemoryRouter>);

    expect(await screen.findByRole("tab", { name: "角色管理" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("tab", { name: "用户管理" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "登录日志" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "操作日志" })).toBeInTheDocument();
    expect(screen.queryByRole("tab", { name: "审计事件" })).not.toBeInTheDocument();
    expect(screen.queryByRole("tab", { name: "组织树" })).not.toBeInTheDocument();
    expect(screen.getByText("RBAC 权限中心")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "创建账号" })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("tab", { name: "用户管理" }));
    expect(await screen.findByRole("heading", { name: "我的账号" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "组织树" })).toBeInTheDocument();
    expect(screen.getByText("新能源一厂 FAC-01")).toBeInTheDocument();
  });

  it("submits a role permission update with an idempotency key", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [], count: 0, page: 1, page_size: 20 }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([{ id: "user-1", username: "operator", enabled: true, role_ids: ["role-1"] }]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([{ id: "role-1", code: "LINE_OPERATOR", name: "操作员", permission_codes: ["workbench:view"] }]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([{ code: "workbench:view" }, { code: "fault:create" }]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "role-1" }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    render(<MemoryRouter><SystemManagementPage /></MemoryRouter>);

    fireEvent.click(await screen.findByRole("tab", { name: "角色管理" }));
    fireEvent.click(await screen.findByRole("button", { name: "配置权限" }));
    (await screen.findByRole("button", { name: "保存角色权限" })).click();

    await screen.findByText("角色权限已更新。");
    expect(fetchMock.mock.calls[5][0]).toBe("/api/roles/role-1/permissions");
    const init = fetchMock.mock.calls[5][1] as RequestInit;
    expect(init.method).toBe("PATCH");
    expect(new Headers(init.headers).get("Idempotency-Key")).toBeTruthy();
  });

  it("lets an administrator select formal permission codes before saving a role", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [], count: 0, page: 1, page_size: 20 }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([{ id: "role-1", code: "LINE_OPERATOR", name: "操作员", permission_codes: ["workbench:view"] }]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([{ code: "workbench:view" }, { code: "fault:create" }]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "role-1" }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    render(<MemoryRouter><SystemManagementPage /></MemoryRouter>);

    fireEvent.click(await screen.findByRole("tab", { name: "角色管理" }));
    fireEvent.click(await screen.findByRole("button", { name: "配置权限" }));
    const checkbox = await screen.findByRole("checkbox", { name: "fault:create" });
    fireEvent.click(checkbox);
    fireEvent.click(screen.getByRole("button", { name: "保存角色权限" }));

    await screen.findByText("角色权限已更新。");
    expect(JSON.parse(String((fetchMock.mock.calls[5][1] as RequestInit).body))).toEqual({
      permission_codes: ["workbench:view", "fault:create"],
    });
  });

  it("keeps the prototype role-list table and does not fabricate unavailable role metadata", async () => {
    vi.stubGlobal("fetch", vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [], count: 0, page: 1, page_size: 20 }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([{ id: "role-1", code: "LINE_OPERATOR", name: "操作员", permission_codes: ["workbench:view"] }]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([{ code: "workbench:view" }]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 })));

    render(<MemoryRouter><SystemManagementPage /></MemoryRouter>);

    expect(await screen.findByRole("columnheader", { name: "角色类型" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "绑定用户" })).toBeInTheDocument();
    expect(screen.getByText("操作员")).toBeInTheDocument();
    expect(screen.getAllByText("当前 API 未提供")).toHaveLength(3);
    fireEvent.click(screen.getByRole("button", { name: "配置权限" }));
    expect(await screen.findByRole("button", { name: "保存角色权限" })).toBeInTheDocument();
  });

  it("keeps separate prototype audit-table structures while only rendering formal audit fields", async () => {
    vi.stubGlobal("fetch", vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [{ id: "audit-1", created_at: "2026-08-06T10:00:00Z", action: "LOGIN", resource_type: "session", result: "SUCCESS" }], count: 1, page: 1, page_size: 20 }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 })));

    render(<MemoryRouter><SystemManagementPage /></MemoryRouter>);

    fireEvent.click(screen.getByRole("tab", { name: "登录日志" }));
    expect(await screen.findByRole("columnheader", { name: "登录账号" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "来源 IP" })).toBeInTheDocument();
    expect(screen.getByText("LOGIN")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("tab", { name: "操作日志" }));
    expect(screen.getByRole("columnheader", { name: "操作时间" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "操作对象" })).toBeInTheDocument();
    expect(screen.getByText("session")).toBeInTheDocument();
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
    expect(screen.getByRole("heading", { name: "受控调用概览" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "知识文档状态" })).toBeInTheDocument();
    expect(screen.getByText(/配置 Token 预算统计，不代表模型实际消耗/)).toBeInTheDocument();
    expect(screen.getByText("512")).toBeInTheDocument();
  });

  it("disables knowledge retry for audit-only users", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [], count: 0, retention_days: 30, token_measurement: "configured_max_reply_tokens_not_actual_usage" }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [{ id: "doc-1", filename: "manual.pdf", status: "FAILED", failure_reason: "retryable", retry_available: true }], count: 1, page: 1, page_size: 20 }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    render(<IntelligentAuditPage permissionCodes={["intelligence:audit"]} />);

    const retry = await screen.findByRole("button", { name: "重新同步" });
    expect(retry).toBeDisabled();
    expect(screen.getByText("当前账号没有知识库写入权限。")).toBeInTheDocument();
  });

  it("enables knowledge retry when audit and knowledge permissions are present", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [], count: 0, retention_days: 30, token_measurement: "configured_max_reply_tokens_not_actual_usage" }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [{ id: "doc-1", filename: "manual.pdf", status: "FAILED", failure_reason: "retryable", retry_available: true }], count: 1, page: 1, page_size: 20 }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "doc-1", status: "UPLOADING" }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    render(<IntelligentAuditPage permissionCodes={["intelligence:audit", "intelligence:knowledge"]} />);

    const retry = await screen.findByRole("button", { name: "重新同步" });
    expect(retry).toBeEnabled();
    expect(screen.queryByText("当前账号没有知识库写入权限。")).not.toBeInTheDocument();
    fireEvent.click(retry);
    await screen.findByText("已提交知识文档重试请求。");
    expect(fetchMock.mock.calls[2][0]).toBe("/api/knowledge/documents/doc-1/retry");
    expect(new Headers((fetchMock.mock.calls[2][1] as RequestInit).headers).get("Idempotency-Key")).toBeTruthy();
  });

  it("requires an explicit structured confirmation before AI fault reporting writes a formal fault", async () => {
    const encoder = new TextEncoder();
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ thread_id: "thread-1", run_id: "run-1" }), { status: 202 }))
      .mockResolvedValueOnce(new Response(new ReadableStream({ start(controller) { controller.enqueue(encoder.encode('event: run_started\ndata: {"status":"RUNNING"}\n\n')); controller.close(); } }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "fault-1", number: "FR-1", agent_status: "submitted" }), { status: 201 }));
    vi.stubGlobal("fetch", fetchMock);

    render(<MemoryRouter><AgentReportPage /></MemoryRouter>);

    expect(screen.getByRole("heading", { name: "对话主区域" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "确认并提交正式故障单" })).not.toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("设备 ID"), { target: { value: "eq-1" } });
    fireEvent.change(screen.getByLabelText("故障描述"), { target: { value: "液压异响" } });
    fireEvent.click(screen.getByRole("button", { name: "开始 AI 收集" }));
    expect(screen.getByRole("button", { name: "AI 收集中…" })).toBeDisabled();
    await screen.findByText("AI 收集任务已创建，请补全并确认正式上报字段。");
    expect(screen.getByRole("heading", { name: "正式字段确认" })).toBeInTheDocument();
    expect(await screen.findByText("运行状态：RUNNING")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("发生时间"), { target: { value: "2026-07-31T10:00" } });
    fireEvent.change(screen.getByLabelText("持续时间（分钟）"), { target: { value: "25" } });
    fireEvent.click(screen.getByRole("button", { name: "确认并提交正式故障单" }));

    await screen.findByText("故障已正式提交：FR-1");
    expect(fetchMock.mock.calls[2][0]).toBe("/api/agent/fault-reports/submit");
    expect(JSON.parse(String((fetchMock.mock.calls[2][1] as RequestInit).body))).toMatchObject({ confirmed: true, draft: { equipment_id: "eq-1", symptom: "液压异响", duration_minutes: 25 } });
  });

  it("preserves the approved Agent report module structure", () => {
    render(<MemoryRouter><AgentReportPage /></MemoryRouter>);
    expect(screen.getByRole("region", { name: "对话主区域" })).toBeInTheDocument();
    expect(screen.getByRole("complementary", { name: "结构化上报摘要" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "对话主区域" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "结构化上报摘要" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "上报预收集" })).toBeInTheDocument();
  });
});
