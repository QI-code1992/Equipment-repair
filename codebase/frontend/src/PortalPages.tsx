import { FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ApiError, AuditEvent, BiDashboard, Equipment, MaintenanceRecord, WorkOrder, createOrganization, createUser, deleteOrganization, getAuditEvents, getBiDashboard, getEquipment, getEquipmentDetail, getEquipmentHistory, getIntelligenceUsage, getKnowledgeDocuments, getMaintenanceRecord, getMaintenanceRecords, getOrganizations, getPermissions, getRoles, getUsers, getWorkOrders, readRunEvents, requestJson, retryKnowledgeDocument, startAgentRun, submitAgentFaultReport, uploadAttachment, updateOrganization, updateRolePermissions, updateUser, type AttachmentRef, type RuntimeEvent } from "./api";

type LoadState<T> = { value: T | null; error: string | null; loading: boolean };

function useData<T>(load: () => Promise<T>, dependencies: unknown[] = []): LoadState<T> {
  const [state, setState] = useState<LoadState<T>>({ value: null, error: null, loading: true });
  useEffect(() => {
    let active = true;
    setState({ value: null, error: null, loading: true });
    load().then((value) => active && setState({ value, error: null, loading: false })).catch((error: unknown) => active && setState({ value: null, error: error instanceof ApiError ? error.code : "REQUEST_FAILED", loading: false }));
    return () => { active = false; };
  // The caller controls a stable loader and its explicit dependencies.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, dependencies);
  return state;
}

function Page({ title, children }: { title: string; children: React.ReactNode }) {
  return <section className="portal-page" aria-labelledby={`portal-page-title-${title}`}><h2 id={`portal-page-title-${title}`} className="sr-only">{title}</h2>{children}</section>;
}

function State<T>({ state, children, empty }: { state: LoadState<T>; children: (value: T) => React.ReactNode; empty?: (value: T) => boolean }) {
  if (state.loading) return <p role="status">正在加载…</p>;
  if (state.error) return <p role="alert">请求失败：{state.error}</p>;
  if (state.value !== null && empty?.(state.value)) return <p role="status">暂无可展示的正式业务数据。</p>;
  return state.value !== null ? <>{children(state.value)}</> : null;
}

export function BiDashboardPage() {
  const [organizationId, setOrganizationId] = useState("");
  const [period, setPeriod] = useState<"day" | "week" | "month">("week");
  const [region, setRegion] = useState("");
  const [equipmentType, setEquipmentType] = useState("");
  const [refresh, setRefresh] = useState(0);
  const state = useData<BiDashboard>(() => getBiDashboard(organizationId || undefined, period === "week" ? undefined : period), [organizationId, period, refresh]);
  const organizations = useData(getOrganizations, []);
  return <Page title="驾驶舱 BI">
    <div className="filter-bar bi-filter-bar"><label>时间范围<select aria-label="时间范围" value={period} onChange={(event) => setPeriod(event.target.value as typeof period)}><option value="day">日</option><option value="week">周</option><option value="month">月</option></select></label><label>组织<select aria-label="组织筛选" value={organizationId} onChange={(event) => setOrganizationId(event.target.value)} disabled={organizations.loading || !!organizations.error}><option value="">全部组织</option>{organizations.value?.filter((item) => item.enabled).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label>区域<select aria-label="区域" value={region} onChange={(event) => setRegion(event.target.value)} disabled><option value="">当前 API 未提供区域筛选</option></select></label><label>设备类型<select aria-label="设备类型" value={equipmentType} onChange={(event) => setEquipmentType(event.target.value)} disabled><option value="">当前 API 未提供设备类型筛选</option></select></label><div className="filter-actions"><button type="button" className="button-primary" onClick={() => setRefresh((value) => value + 1)}>查询</button><button type="button" className="button-secondary" onClick={() => { setOrganizationId(""); setPeriod("week"); setRegion(""); setEquipmentType(""); setRefresh((value) => value + 1); }}>重置</button></div></div>
    {organizations.error && <p role="alert">组织筛选不可用：{organizations.error}</p>}{state.error?.includes("ORGANIZATION_NOT_FOUND") && <p role="alert">所选组织不存在或已被移除。</p>}
    <State state={state}>{(value) => <>
      <section className="bi-section" aria-labelledby="bi-summary-heading"><header className="section-heading"><div><h3 id="bi-summary-heading">管理摘要</h3><p>整体经营与运维表现，数据来自正式 BI 接口。</p></div></header><div className="data-grid bi-kpi-grid"><div className="metric bi-kpi"><div className="bi-kpi__head"><span className="label">故障总数</span><span className="bi-kpi__icon" aria-hidden="true">!</span></div><b>{value.summary.fault_count}</b><span className="bi-kpi__delta">当前周期正式统计</span><div className="bi-kpi__sparkline" aria-hidden="true">{value.trend.slice(-5).map((item) => <i key={`fault-${item.date}`} style={{ height: `${Math.max(12, item.fault_count * 10)}%` }} />)}</div></div><div className="metric bi-kpi bi-kpi--risk"><div className="bi-kpi__head"><span className="label">活动故障</span><span className="bi-kpi__icon" aria-hidden="true">险</span></div><b>{value.summary.active_fault_count}</b><span className="bi-kpi__delta">当前未闭环故障</span><div className="bi-kpi__sparkline" aria-hidden="true">{value.trend.slice(-5).map((item) => <i key={`active-${item.date}`} style={{ height: `${Math.max(12, Math.min(100, item.fault_count * 10))}%` }} />)}</div></div><div className="metric bi-kpi"><div className="bi-kpi__head"><span className="label">完成工单</span><span className="bi-kpi__icon" aria-hidden="true">✓</span></div><b>{value.summary.completed_work_order_count}</b><span className="bi-kpi__delta">当前周期正式统计</span><div className="bi-kpi__sparkline" aria-hidden="true">{value.trend.slice(-5).map((item) => <i key={`done-${item.date}`} style={{ height: `${Math.max(12, item.completed_work_order_count * 10)}%` }} />)}</div></div><div className="metric bi-kpi"><div className="bi-kpi__head"><span className="label">完成率</span><span className="bi-kpi__icon" aria-hidden="true">率</span></div><b>{Math.round(value.summary.completion_rate * 100)}%</b><span className="bi-kpi__delta">当前周期正式统计</span><div className="bi-kpi__sparkline" aria-hidden="true">{value.trend.slice(-5).map((item) => <i key={`rate-${item.date}`} style={{ height: `${Math.max(12, Math.min(100, item.completed_work_order_count * 10))}%` }} />)}</div></div><div className="metric metric--warning bi-kpi"><div className="bi-kpi__head"><span className="label">平均维修时长</span><span className="bi-kpi__icon" aria-hidden="true">时</span></div><b>{value.efficiency.average_completion_hours ?? "—"}<small>{value.efficiency.average_completion_hours === null ? "" : " 小时"}</small></b><span className="bi-kpi__delta">当前周期正式统计</span><div className="bi-kpi__sparkline" aria-hidden="true">{value.trend.slice(-5).map((item) => <i key={`hours-${item.date}`} style={{ height: `${Math.max(12, Math.min(100, item.completed_work_order_count * 10))}%` }} />)}</div></div></div></section>
      <section className="data-card bi-section" aria-labelledby="bi-trend-heading"><header className="section-heading"><div><h3 id="bi-trend-heading">趋势分析</h3><p>按时间观察健康、故障和工单变化。</p></div><div className="segmented" role="group" aria-label="趋势粒度"><button type="button" aria-pressed={period === "day"} onClick={() => setPeriod("day")}>日</button><button type="button" aria-pressed={period === "week"} onClick={() => setPeriod("week")}>周</button><button type="button" aria-pressed={period === "month"} onClick={() => setPeriod("month")}>月</button></div></header>{value.trend.length ? <><div className="bi-trend-grid"><article className="data-card"><h3>健康综合评分趋势</h3><p className="prototype-unavailable">当前 BI API 未提供健康评分序列。</p></article><article className="data-card"><h3>故障数量趋势</h3><TrendSeriesChart label="故障数量" values={value.trend.map((item) => item.fault_count)} dates={value.trend.map((item) => item.date)} /></article><article className="data-card"><h3>工单数量趋势</h3><TrendSeriesChart label="工单数量" values={value.trend.map((item) => item.completed_work_order_count)} dates={value.trend.map((item) => item.date)} /></article></div><TrendChart trend={value.trend} /></> : <div className="prototype-unavailable"><p>暂无趋势数据。</p><p>当前 API 未提供趋势序列数据。</p></div>}</section>
      <section className="data-card bi-section" aria-labelledby="bi-efficiency-heading"><header className="section-heading"><div><h3 id="bi-efficiency-heading">效率分析</h3><p>聚合指标用于管理层效率判断。</p></div></header><div className="bi-unavailable-grid"><p>计划工单完成率：当前 API 未提供。</p><p>平均响应时长：当前 API 未提供。</p><p>{value.efficiency.average_completion_hours === null ? "平均完成时长：当前 API 未提供。" : `平均完成 ${value.efficiency.average_completion_hours} 小时`}</p><p>首次修复率：当前 API 未提供。</p></div><div className="bi-ranking" aria-label="组织排行"><h4>组织排行</h4>{value.organization_ranking.length ? <ol>{value.organization_ranking.map((item) => <li key={item.organization_id}>{item.organization_name}：{item.fault_count}</li>)}</ol> : <p className="prototype-unavailable">当前 API 未提供组织排行数据。</p>}</div></section>
      <section className="data-card bi-section" aria-labelledby="bi-health-heading"><header className="section-heading"><div><h3 id="bi-health-heading">设备健康列表</h3><p>当前 API 未提供设备健康列表数据。</p></div></header><p className="prototype-unavailable">当前 API 未提供设备健康列表数据。</p></section>
      <section className="data-card bi-section" aria-labelledby="bi-history-heading"><header className="section-heading"><div><h3 id="bi-history-heading">指标历史对比</h3><p>当前 API 未提供完整历史指标对比数据。</p></div></header><p className="prototype-unavailable">当前 API 未提供指标历史对比数据。</p></section>
    </>}</State>
  </Page>;
}

function TrendChart({ trend }: { trend: BiDashboard["trend"] }) {
  const maximum = Math.max(1, ...trend.flatMap((item) => [item.fault_count, item.completed_work_order_count]));
  return <div className="bi-trend" role="img" aria-label="故障与完成工单趋势">{trend.map((item) => <div className="bi-trend__item" key={item.date}><div className="bi-trend__bars" aria-hidden="true"><span className="bi-trend__bar bi-trend__bar--fault" style={{ height: `${item.fault_count / maximum * 100}%` }} /><span className="bi-trend__bar bi-trend__bar--completed" style={{ height: `${item.completed_work_order_count / maximum * 100}%` }} /></div><p>{item.date}：故障 {item.fault_count}，完成 {item.completed_work_order_count}</p></div>)}</div>;
}

function TrendSeriesChart({ label, values, dates }: { label: string; values: number[]; dates: string[] }) {
  const maximum = Math.max(1, ...values);
  const width = 320;
  const height = 120;
  const padding = 12;
  const points = values.map((value, index) => {
    const x = values.length <= 1 ? width / 2 : padding + (index / (values.length - 1)) * (width - padding * 2);
    const y = height - padding - (value / maximum) * (height - padding * 2);
    return `${x},${y}`;
  }).join(" ");
  return <div className="bi-series-chart" role="img" aria-label={`${label}趋势图`}><svg className="bi-series-chart__line" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" aria-hidden="true"><line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} /><polyline points={points} /><g>{values.map((value, index) => { const [x, y] = points.split(" ")[index].split(","); return <circle key={`${dates[index]}-${value}`} cx={x} cy={y} r="3" />; })}</g></svg><ul>{values.map((value, index) => <li key={`${dates[index]}-label`}>{dates[index]}：{value}</li>)}</ul></div>;
}

export function EquipmentLedgerPage() {
  const state = useData<Equipment[]>(getEquipment, []);
  const organizations = useData(getOrganizations, []);
  const [query, setQuery] = useState("");
  const [nameQuery, setNameQuery] = useState("");
  const [status, setStatus] = useState("");
  const [factoryId, setFactoryId] = useState("");
  const [workshopId, setWorkshopId] = useState("");
  const [lineId, setLineId] = useState("");
  if (state.loading) return <Page title="设备台账"><p role="status">正在加载…</p></Page>;
  if (state.error) return <Page title="设备台账"><p role="alert">请求失败：{state.error}</p></Page>;
  const items = state.value ?? [];
  const organizationItems = organizations.value ?? [];
  const factories = organizationItems.filter((item) => item.type === "FACTORY" && item.enabled);
  const workshops = organizationItems.filter((item) => item.type === "WORKSHOP" && item.enabled && item.parent_id === factoryId);
  const lines = organizationItems.filter((item) => item.type === "LINE" && item.enabled && item.parent_id === workshopId);
  const descendantIds = (rootId: string): Set<string> => {
    const ids = new Set([rootId]);
    let changed = true;
    while (changed) {
      changed = false;
      for (const item of organizationItems) {
        if (item.parent_id && ids.has(item.parent_id) && !ids.has(item.id)) {
          ids.add(item.id);
          changed = true;
        }
      }
    }
    return ids;
  };
  const selectedOrganization = lineId || workshopId || factoryId;
  const selectedOrganizationIds = selectedOrganization ? descendantIds(selectedOrganization) : null;
  return <Page title="设备台账">{(() => {
    const filtered = items.filter((item) => (!query || [item.code, item.name, item.model, item.status].some((value) => value.includes(query))) && (!nameQuery || item.name.includes(nameQuery)) && (!status || item.status === status) && (!selectedOrganizationIds || selectedOrganizationIds.has(item.organization_id)));
    const statusCounts = items.reduce<Record<string, number>>((counts, item) => ({ ...counts, [item.status]: (counts[item.status] ?? 0) + 1 }), {});
    return <>
      <section className="ledger-overview" aria-label="设备总览">
        <div><p className="page-shell__eyebrow">设备总览</p><strong>已加载 {items.length} 台正式设备</strong><span>仅展示设备台账 API 返回的资产、状态和运行字段。</span></div>
        <div className="ledger-overview__statuses" aria-label="设备状态分布">{Object.entries(statusCounts).map(([name, count]) => <span key={name} className={`status-chip ${name === "FAULT" ? "status-chip--danger" : name === "NORMAL" ? "status-chip--success" : "status-chip--neutral"}`}>{name} {count}</span>)}</div>
      </section>
      <section className="ledger-toolbar ledger-toolbar--hierarchy" aria-label="设备筛选工具栏">
        <label>工厂<select aria-label="设备所属工厂" value={factoryId} onChange={(event) => { setFactoryId(event.target.value); setWorkshopId(""); setLineId(""); }} disabled={organizations.loading || !!organizations.error}><option value="">全部工厂</option>{factories.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
        <label>车间<select aria-label="设备所属车间" value={workshopId} onChange={(event) => { setWorkshopId(event.target.value); setLineId(""); }} disabled={!factoryId || organizations.loading || !!organizations.error}><option value="">全部车间</option>{workshops.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
        <label>产线<select aria-label="设备所属产线" value={lineId} onChange={(event) => setLineId(event.target.value)} disabled={!workshopId || organizations.loading || !!organizations.error}><option value="">全部产线</option>{lines.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
        <label>设备编号<input aria-label="筛选设备" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="输入设备编号" /></label>
        <label>设备名称<input aria-label="设备名称筛选" value={nameQuery} onChange={(event) => setNameQuery(event.target.value)} placeholder="输入设备名称" /></label>
        <label>设备状态<select aria-label="设备状态筛选" value={status} onChange={(event) => setStatus(event.target.value)}><option value="">全部状态</option>{Object.keys(statusCounts).sort().map((name) => <option key={name} value={name}>{name}</option>)}</select></label>
        <div className="filter-actions"><button type="button" className="button-primary">查询</button><button type="button" className="button-secondary" onClick={() => { setQuery(""); setNameQuery(""); setStatus(""); setFactoryId(""); setWorkshopId(""); setLineId(""); }}>重置</button></div>
        <Link className="button-primary ledger-toolbar__create" to="/equipment/new">新增设备</Link>
      </section>
      <section className="ledger-table-panel">
        <header><div><h3 aria-label="设备列表">资产列表</h3><p>{filtered.length === items.length ? "当前显示全部已加载设备。" : `当前显示 ${filtered.length} 台符合筛选条件的设备。`}</p></div></header>
        {filtered.length ? <table><thead><tr><th>设备身份</th><th>型号与制造商</th><th>所属组织</th><th>健康评分</th><th>运行工时</th><th>状态</th><th>操作</th></tr></thead><tbody>{filtered.map((item) => <tr key={item.id}><td><strong>{item.name}</strong><small>{item.code}</small></td><td><strong>{item.model}</strong><small>{item.manufacturer}</small></td><td>{item.organization_id}</td><td><span className="prototype-unavailable table-unavailable">当前 API 未提供</span></td><td>{item.operating_hours}</td><td><span className={`status-chip ${item.status === "FAULT" ? "status-chip--danger" : item.status === "NORMAL" ? "status-chip--success" : "status-chip--neutral"}`}>{item.status}</span></td><td className="table-actions"><Link to={`/equipment/${item.id}`}>详情</Link><Link to={`/equipment/${item.id}/edit`}>编辑</Link></td></tr>)}</tbody></table> : <p className="empty-panel" role="status">{items.length ? "没有符合筛选条件的正式设备数据。" : "尚未登记正式设备。"}</p>}
      </section>
    </>;
  })()}</Page>;
}

export function EquipmentDetailPage() {
  const { id = "" } = useParams();
  const equipment = useData(() => getEquipmentDetail(id), [id]);
  const history = useData(() => getEquipmentHistory(id), [id]);
  const [activeTab, setActiveTab] = useState<"graph" | "bom" | "params" | "docs" | "records">("graph");
  return <Page title="设备详情"><State state={equipment}>{(item) => <>
    <section className="equipment-hero"><div><p className="page-shell__eyebrow">资产身份</p><h3>{item.name}</h3><p>{item.code} · {item.model} · {item.manufacturer}</p></div><div className="context-actions"><Link className="button-secondary" to="/equipment">返回台账</Link><Link className="button-primary" to={`/equipment/${item.id}/edit`}>编辑设备</Link></div></section>
    <div className="equipment-detail-grid"><section className="data-card"><h3>资产身份</h3><dl className="detail-list"><dt>设备编码</dt><dd>{item.code}</dd><dt>设备类型</dt><dd>{item.type}</dd><dt>所属组织</dt><dd>{item.organization_id}</dd><dt>负责人 ID</dt><dd>{item.owner_user_id ?? "未分配"}</dd></dl></section><section className="data-card"><h3>运行与关键参数</h3><dl className="detail-list"><dt>运行状态</dt><dd><span className={`status-chip ${item.status === "FAULT" ? "status-chip--danger" : item.status === "NORMAL" ? "status-chip--success" : "status-chip--neutral"}`}>{item.status}</span></dd><dt>累计工时</dt><dd>{item.operating_hours}</dd><dt>制造日期</dt><dd>{item.manufactured_at ?? "未登记"}</dd><dt>投用日期</dt><dd>{item.commissioned_at ?? "未登记"}</dd></dl></section></div>
    <section className="equipment-detail-overview" aria-label="设备分析概览"><article className="data-card"><h3>当前评分构成</h3><p className="prototype-unavailable">健康评分明细接口尚未提供，未生成演示分值。</p></article><article className="data-card"><h3>风险恢复记录</h3><p className="prototype-unavailable">风险恢复记录接口尚未提供，未生成演示记录。</p></article></section>
  </>}</State><section className="equipment-detail-tabs" aria-label="设备详情分区"><div className="section-tabs" role="tablist" aria-label="设备详情标签页">{[["graph", "图谱关系"], ["bom", "BOM 组成"], ["params", "额定参数"], ["docs", "知识文档"], ["records", "维修记录"]].map(([idValue, label]) => <button key={idValue} type="button" role="tab" aria-selected={activeTab === idValue} onClick={() => setActiveTab(idValue as typeof activeTab)}>{label}</button>)}</div><div className="equipment-detail-tab-panel" role="tabpanel">{activeTab === "graph" && <div className="detail-tab-empty"><h3>关联内容</h3><p>当前设备图谱接口尚未提供，未生成演示关系。</p></div>}{activeTab === "bom" && <div className="detail-tab-empty"><h3>BOM 组成</h3><p>当前 API 未提供该模块数据，未生成演示内容。</p></div>}{activeTab === "params" && <div className="detail-tab-empty"><h3>额定参数</h3><p>当前 API 未提供该模块数据，未生成演示内容。</p></div>}{activeTab === "docs" && <div className="detail-tab-empty"><h3>知识文档</h3><p>知识文档接口尚未提供，当前仅展示正式字段状态。</p></div>}{activeTab === "records" && <State state={history}>{(data) => <>{data.count ? <RecordsTable items={data.items} /> : <p className="empty-panel" role="status">暂无维修历史记录。</p>}<section className="history-trend" aria-label="维修完成趋势"><h4>维修完成趋势</h4>{data.trend.length ? <ul>{data.trend.map((item) => <li key={item.date}>{item.date}：完成 {item.completed_count} 次</li>)}</ul> : <p>暂无维修完成趋势。</p>}</section></>}</State>}</div></section><section className="history-panel" aria-label="维修历史"><header><div><h3>维修历史</h3><p>工单、故障和维修结论来自正式维修记录接口。</p></div></header><State state={history}>{(data) => <>{data.count ? <RecordsTable items={data.items} /> : <p className="empty-panel" role="status">暂无维修历史记录。</p>}<section className="history-trend" aria-label="维修完成趋势"><h4>维修完成趋势</h4>{data.trend.length ? <ul>{data.trend.map((item) => <li key={item.date}>{item.date}：完成 {item.completed_count} 次</li>)}</ul> : <p>暂无维修完成趋势。</p>}</section></>}</State></section></Page>;
}
function EquipmentForm({ edit = false }: { edit?: boolean }) {
  const { id = "" } = useParams();
  const details = useData(() => edit ? getEquipmentDetail(id) : Promise.resolve(null), [id, edit]);
  const organizations = useData(getOrganizations, []);
  const users = useData(getUsers, []);
  const [message, setMessage] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [factoryId, setFactoryId] = useState("");
  const [workshopId, setWorkshopId] = useState("");
  const [lineId, setLineId] = useState("");
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (saving) return;
    const form = new FormData(event.currentTarget);
    const ownerUserId = String(form.get("owner_user_id") ?? "");
    const manufacturedAt = String(form.get("manufactured_at") ?? "");
    const commissionedAt = String(form.get("commissioned_at") ?? "");
    const imageObjectKey = String(form.get("image_object_key") ?? "").trim();
    const imageFilename = String(form.get("image_filename") ?? "").trim();
    const imageRefs = imageObjectKey && imageFilename ? [{ object_key: imageObjectKey, filename: imageFilename }] : [];
    const body = {
      code: String(form.get("code")),
      name: String(form.get("name")),
      model: String(form.get("model")),
      type: String(form.get("type")),
      manufacturer: String(form.get("manufacturer")),
      manufactured_at: manufacturedAt || null,
      commissioned_at: commissionedAt || null,
      operating_hours: Number(form.get("operating_hours")),
      status: String(form.get("status")),
      organization_id: lineId || current?.organization_id || visibleLines[0]?.id || lines[0]?.id || String(form.get("organization_id")),
      owner_user_id: ownerUserId || null,
      image_refs: imageRefs,
    };
    setSaving(true);
    try {
      await requestJson(edit ? `/api/equipment/${id}` : "/api/equipment", { method: edit ? "PATCH" : "POST", headers: { "Content-Type": "application/json", "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify(body) });
      setMessage("已保存正式设备数据。");
    } catch (error) {
      setMessage(`保存失败：${error instanceof ApiError ? error.code : "REQUEST_FAILED"}`);
    } finally {
      setSaving(false);
    }
  }
  const current = details.value;
  const currentImage = current?.image_refs[0];
  const lines = (organizations.value ?? []).filter((item) => item.type === "LINE" && item.enabled);
  const owners = (users.value ?? []).filter((item) => item.enabled);
  const organizationItems = organizations.value ?? [];
  const factories = organizationItems.filter((item) => item.type === "FACTORY" && item.enabled);
  const workshops = organizationItems.filter((item) => item.type === "WORKSHOP" && item.enabled && item.parent_id === factoryId);
  const visibleLines = organizationItems.filter((item) => item.type === "LINE" && item.enabled && (!factories.length || item.parent_id === (workshopId || factoryId)));
  const effectiveLineId = lineId || current?.organization_id || visibleLines[0]?.id || lines[0]?.id || "";
  useEffect(() => {
    if (!organizationItems.length) return;
    const selectedLine = current?.organization_id ? organizationItems.find((item) => item.id === current.organization_id) : null;
    const initialLine = selectedLine ?? visibleLines[0] ?? lines[0];
    if (!initialLine) return;
    const parent = organizationItems.find((item) => item.id === initialLine.parent_id);
    const factory = parent?.type === "FACTORY" ? parent : parent ? organizationItems.find((item) => item.id === parent.parent_id) : null;
    const workshop = parent?.type === "WORKSHOP" ? parent : null;
    setFactoryId(factory?.id ?? "");
    setWorkshopId(workshop?.id ?? "");
    setLineId(initialLine.id);
  }, [current?.organization_id, organizationItems.length]);
  if (details.loading || organizations.loading || users.loading) return <Page title={edit ? "编辑设备" : "新增设备"}><p role="status">正在加载…</p></Page>;
  if (details.error || organizations.error || users.error) return <Page title={edit ? "编辑设备" : "新增设备"}><p role="alert">无法加载设备依赖：{details.error ?? organizations.error ?? users.error}</p></Page>;
  return <Page title={edit ? "编辑设备" : "新增设备"}><form className="equipment-form" onSubmit={submit}><header><div><p className="page-shell__eyebrow">{edit ? "维护已有资产字段" : "登记正式设备资产"}</p><h3>{edit ? current?.name ?? "编辑设备" : "新增设备"}</h3><p>保存只提交当前表单中的正式设备字段。</p></div><Link className="button-secondary" to={edit ? `/equipment/${id}` : "/equipment"}>返回</Link></header><fieldset><legend>设备基础信息</legend><div className="portal-form"><label>设备编码<input name="code" required defaultValue={current?.code} /></label><label>设备名称<input name="name" required defaultValue={current?.name} /></label><label>型号<input name="model" required defaultValue={current?.model} /></label><label>类型<input name="type" required defaultValue={current?.type} /></label><label>制造商<input name="manufacturer" required defaultValue={current?.manufacturer} /></label><label>所属工厂<select aria-label="所属工厂" value={factoryId} onChange={(event) => { setFactoryId(event.target.value); setWorkshopId(""); setLineId(""); }}><option value="" disabled>请选择启用工厂</option>{factories.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label>所属车间<select aria-label="所属车间" value={workshopId} onChange={(event) => { setWorkshopId(event.target.value); setLineId(""); }} disabled={factories.length > 0 && !factoryId}><option value="">请选择启用车间</option>{workshops.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label>所属产线<select name="organization_id" aria-label="所属产线" value={effectiveLineId} onChange={(event) => setLineId(event.target.value)} required disabled={factories.length > 0 && !factoryId}><option value="" disabled>请选择启用产线</option>{(visibleLines.length ? visibleLines : lines).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label></div></fieldset><fieldset><legend>运行与归属</legend><div className="portal-form"><label>负责人<select name="owner_user_id" aria-label="负责人" defaultValue={current?.owner_user_id ?? ""}><option value="">未分配</option>{owners.map((item) => <option key={item.id} value={item.id}>{item.username}</option>)}</select></label><label>运行工时<input name="operating_hours" type="number" min="0" defaultValue={current?.operating_hours ?? 0} /></label><label>状态<select name="status" defaultValue={current?.status ?? "NORMAL"}><option>NORMAL</option><option>FAULT</option><option>REPAIRING</option><option>DISABLED</option></select></label><label>制造日期<input aria-label="制造日期" name="manufactured_at" type="date" defaultValue={current?.manufactured_at ?? ""} /></label><label>投用日期<input aria-label="投用日期" name="commissioned_at" type="date" defaultValue={current?.commissioned_at ?? ""} /></label></div></fieldset><fieldset><legend>设备图片引用</legend><div className="portal-form"><label>图片对象键<input aria-label="图片对象键" name="image_object_key" defaultValue={currentImage?.object_key ?? ""} /></label><label>图片文件名<input aria-label="图片文件名" name="image_filename" defaultValue={currentImage?.filename ?? ""} /></label></div></fieldset><section className="equipment-add-section"><div className="section-title"><h3>设备 BOM 组成</h3><button type="button" className="button-secondary" disabled title="当前 API 未提供 BOM 数据">新增分支节点</button></div><div className="prototype-unavailable"><p>当前 API 未提供该模块数据，未生成演示内容。</p><table aria-label="设备 BOM 组成字段"><thead><tr><th>层级</th><th>上级节点</th><th>分枝节点编码</th><th>分枝节点名称</th><th>描述</th><th>单位</th><th>BOM 用量</th><th>操作</th></tr></thead></table></div></section><section className="equipment-add-section"><div className="section-title"><h3>设备额定参数</h3><button type="button" className="button-secondary" disabled title="当前 API 未提供额定参数数据">新增参数</button></div><div className="prototype-unavailable"><p>当前 API 未提供该模块数据，未生成演示内容。</p><table aria-label="设备额定参数字段"><thead><tr><th>序号</th><th>参数名</th><th>额定参数值</th><th>浮动上限</th><th>浮动下限</th><th>单位</th><th>说明</th><th>操作</th></tr></thead></table></div></section><section className="equipment-add-section"><div className="section-title"><h3>知识资料</h3><button type="button" className="button-secondary" disabled title="当前 API 未提供知识资料上传接口">上传资料</button></div><div className="prototype-unavailable"><p>当前 API 未提供该模块数据，未生成演示内容。</p><table aria-label="知识资料字段"><thead><tr><th>序号</th><th>资料类型</th><th>文件名</th><th>大小</th><th>上传时间</th><th>格式</th><th>操作</th></tr></thead></table></div></section><footer><button type="submit" disabled={saving}>{saving ? "保存中…" : "保存"}</button>{!effectiveLineId && <p role="alert">请选择可用产线，无法保存设备。</p>}{message && <p role="status">{message}</p>}</footer></form></Page>;
}
export const EquipmentAddPage = () => <EquipmentForm />;
export const EquipmentEditPage = () => <EquipmentForm edit />;

function RecordsTable({ items }: { items: MaintenanceRecord[] }) { return <table><thead><tr><th>工单</th><th>状态</th><th>故障</th><th>结论</th><th>知识状态</th><th>操作</th></tr></thead><tbody>{items.map((item) => <tr key={item.maintenance_record_id}><td>{item.work_order_number}</td><td>{item.status}</td><td>{item.symptom}</td><td>{item.repair_result ?? "未完成"}</td><td>{item.knowledge_status}</td><td><Link to={`/maintenance-records/${item.maintenance_record_id}`}>详情</Link></td></tr>)}</tbody></table>; }

function MaintenancePrototypeTable({ items }: { items: MaintenanceRecord[] }) {
  return <table aria-label="维修记录列表"><thead><tr><th>序号</th><th>维修记录编号</th><th>所属车间</th><th>所属产线</th><th>异常信息</th><th>工单状态</th><th>维修负责人</th><th>处理结果</th><th>完成时间</th></tr></thead><tbody>{items.map((item, index) => <tr key={item.maintenance_record_id}><td>{index + 1}</td><td>{item.maintenance_record_id}</td><td><span className="prototype-unavailable table-unavailable">当前 API 未提供</span></td><td><span className="prototype-unavailable table-unavailable">当前 API 未提供</span></td><td>{item.symptom || "未填写"}</td><td>{item.status}</td><td><span className="prototype-unavailable table-unavailable">当前 API 未提供</span></td><td>{item.repair_result ?? "未完成"}</td><td>{item.completed_at ?? "—"}</td></tr>)}</tbody></table>;
}

export function MaintenanceRecordsPage() {
  const [activePanel, setActivePanel] = useState<"overview" | "records">("overview");
  const [equipmentId, setEquipmentId] = useState("");
  const [knowledgeStatus, setKnowledgeStatus] = useState("");
  const [timeRange, setTimeRange] = useState("month");
  const [factoryId, setFactoryId] = useState("");
  const [workshopId, setWorkshopId] = useState("");
  const [lineId, setLineId] = useState("");
  const [page, setPage] = useState(1);
  const state = useData(() => getMaintenanceRecords({ equipmentId: equipmentId || undefined, knowledgeStatus: knowledgeStatus || undefined, page }), [equipmentId, knowledgeStatus, page]);
  return <Page title="维修记录"><section className="prototype-module-note" aria-label="上报预收集"><h3>上报预收集</h3><p>当前维修记录 API 未提供预收集数据，保留原型模块位置并明确不可用。</p></section><div className="maintenance-tabs" role="tablist" aria-label="维修记录视图"><button className={`maintenance-tab ${activePanel === "overview" ? "active" : ""}`} type="button" role="tab" aria-selected={activePanel === "overview"} aria-controls="maintenance-panel-overview" onClick={() => setActivePanel("overview")}>维修概览</button><button className={`maintenance-tab ${activePanel === "records" ? "active" : ""}`} type="button" role="tab" aria-selected={activePanel === "records"} aria-controls="maintenance-panel-records" onClick={() => setActivePanel("records")}>维修记录列表</button></div><section className="maintenance-filter"><header><h3 aria-label="维修记录检索">维修概览</h3><p>按时间、组织层级和正式设备筛选维修档案。</p></header><div className="maintenance-filter__fields"><label>时间范围<select aria-label="维修时间范围" value={timeRange} onChange={(event) => setTimeRange(event.target.value)}><option value="day">日</option><option value="week">周</option><option value="month">月</option></select></label><label>所属工厂<select aria-label="维修所属工厂" value={factoryId} onChange={(event) => setFactoryId(event.target.value)} disabled><option value="">当前 API 未提供组织筛选</option></select></label><label>所属车间<select aria-label="维修所属车间" value={workshopId} onChange={(event) => setWorkshopId(event.target.value)} disabled><option value="">当前 API 未提供组织筛选</option></select></label><label>所属产线<select aria-label="维修所属产线" value={lineId} onChange={(event) => setLineId(event.target.value)} disabled><option value="">当前 API 未提供组织筛选</option></select></label><label>设备筛选<input aria-label="维修记录设备筛选" value={equipmentId} onChange={(event) => { setEquipmentId(event.target.value); setPage(1); }} placeholder="输入正式设备 ID" /></label><label>知识状态<select aria-label="维修记录知识状态筛选" value={knowledgeStatus} onChange={(event) => { setKnowledgeStatus(event.target.value); setPage(1); }}><option value="">全部</option><option value="NOT_LINKED">未关联</option><option value="LINKED">已关联</option></select></label><div className="filter-actions"><button type="button" className="button-primary">查询</button><button type="button" className="button-secondary" onClick={() => { setTimeRange("month"); setFactoryId(""); setWorkshopId(""); setLineId(""); setEquipmentId(""); setKnowledgeStatus(""); setPage(1); }}>重置</button></div></div></section><section id="maintenance-panel-overview" className="maintenance-panel" role="tabpanel" aria-label="维修概览" hidden={activePanel !== "overview"}><section className="maintenance-overview" aria-label="维修概览指标"><article className="maintenance-kpi"><span>总维修次数</span><strong className="prototype-unavailable">当前 API 未提供</strong><em>维修中 + 已处理</em></article><article className="maintenance-kpi"><span>待处理维修</span><strong className="prototype-unavailable">当前 API 未提供</strong><em>当前维修中</em></article><article className="maintenance-kpi"><span>平均修复时间 MTTR</span><strong className="prototype-unavailable">当前 API 未提供</strong><em>按已处理记录计算</em></article><article className="maintenance-kpi"><span>平均故障间隔 MTBF</span><strong className="prototype-unavailable">当前 API 未提供</strong><em>按设备记录均值</em></article><article className="maintenance-kpi"><span>平均维修时间</span><strong className="prototype-unavailable">当前 API 未提供</strong><em>维修中计入当前时长</em></article><article className="maintenance-kpi"><span>维修完成率</span><strong className="prototype-unavailable">当前 API 未提供</strong><em>已处理 / 总维修</em></article></section><section className="maintenance-charts" aria-label="维修概览图表"><article className="maintenance-chart-card"><div className="maintenance-chart-head"><h3>故障类型分布</h3><span className="status-chip status-chip--info">类型</span></div><div className="maintenance-chart" role="img" aria-label="故障类型分布图"><p className="prototype-unavailable">当前 API 未提供故障类型分布数据。</p></div></article><article className="maintenance-chart-card"><div className="maintenance-chart-head"><h3>维修时长分布</h3><span className="status-chip status-chip--info">时长</span></div><div className="maintenance-chart" role="img" aria-label="维修时长分布图"><p className="prototype-unavailable">当前 API 未提供维修时长分布数据。</p></div></article><article className="maintenance-chart-card"><div className="maintenance-chart-head"><h3>设备状态分布</h3><span className="status-chip status-chip--info">状态</span></div><div className="maintenance-chart" role="img" aria-label="设备状态分布图"><p className="prototype-unavailable">当前 API 未提供设备状态分布数据。</p></div></article><article className="maintenance-chart-card"><div className="maintenance-chart-head"><h3>故障次数趋势</h3><span className="status-chip status-chip--info">时间</span></div><div className="maintenance-chart" role="img" aria-label="故障次数趋势图"><p className="prototype-unavailable">当前 API 未提供故障次数趋势数据。</p></div></article></section></section><section id="maintenance-panel-records" className="maintenance-panel" role="tabpanel" aria-label="维修记录列表" hidden={activePanel !== "records"}><State state={state}>{(data) => <section className="maintenance-records-panel"><header><div><h3>维修记录列表</h3><p>第 {page} 页的正式维修记录。</p></div><button type="button" className="button-secondary" disabled title="当前 API 未提供导出接口">导出</button></header><MaintenancePrototypeTable items={data.items} />{!data.items.length && <p className="empty-panel" role="status">暂无可展示的正式维修记录。</p>}<div className="pager"><button type="button" disabled={page <= 1} onClick={() => setPage((current) => current - 1)}>上一页</button><span>第 {page} 页</span><button type="button" disabled={data.items.length < data.page_size} onClick={() => setPage((current) => current + 1)}>下一页</button></div></section>}</State></section></Page>;
}
export function MaintenanceRecordDetailPage() { const { id = "" } = useParams(); const state = useData(() => getMaintenanceRecord(id), [id]); return <Page title="维修记录详情"><State state={state}>{(item) => <><section className="equipment-hero"><div><p className="page-shell__eyebrow">维修工单</p><h3>{item.work_order_number}</h3><p>设备 ID：{item.equipment_id} · 工单状态：{item.status}</p></div><Link className="button-secondary" to="/maintenance-records">返回记录</Link></section><section className="maintenance-detail-modules" aria-label="维修记录详情模块"><article className="data-card"><h3>故障摘要</h3><p>{item.symptom || "未填写故障现象"}</p></article><article className="data-card"><h3>现场描述</h3><p className="prototype-unavailable">现场描述扩展字段未由当前维修记录接口提供。</p></article><article className="data-card"><h3>维修进度</h3><p>{item.status}</p></article><article className="data-card"><h3>处理闭环</h3><p>{item.repair_result ?? "未完成"}</p></article><article className="data-card"><h3>附件证据</h3><p className="prototype-unavailable">附件证据列表接口未由当前维修记录详情接口提供。</p></article></section><div className="maintenance-detail-grid"><section className="data-card"><h3>故障与根因</h3><dl className="detail-list"><dt>故障现象</dt><dd>{item.symptom}</dd><dt>实际原因</dt><dd>{item.actual_cause ?? "未填写"}</dd><dt>解决方案</dt><dd>{item.actual_solution ?? "未填写"}</dd></dl></section><section className="data-card"><h3>维修结论</h3><dl className="detail-list"><dt>维修结果</dt><dd>{item.repair_result ?? "未完成"}</dd><dt>更换部件</dt><dd>{item.parts_replacement_notes ?? "无"}</dd><dt>知识状态</dt><dd>{item.knowledge_status}</dd><dt>完成时间</dt><dd>{item.completed_at ?? "未完成"}</dd></dl></section></div></>}</State></Page>; }
export function WorkOrdersPage() { const [status, setStatus] = useState(""); const [page, setPage] = useState(1); const state = useData(() => getWorkOrders({ status: status || undefined, page }), [status, page]); return <Page title="维修执行"><label>工单状态<select aria-label="工单状态筛选" value={status} onChange={(event) => { setStatus(event.target.value); setPage(1); }}><option value="">全部</option><option value="PENDING_ACCEPT">待接单</option><option value="IN_REPAIR">维修中</option><option value="PENDING_INSPECTION">待验收</option><option value="COMPLETED">已完成</option></select></label><State state={state} empty={(data) => !data.count}>{(data) => <><table><thead><tr><th>工单</th><th>设备</th><th>状态</th><th>故障</th></tr></thead><tbody>{data.items.map((item: WorkOrder) => <tr key={item.id}><td>{item.number}</td><td>{item.equipment_id}</td><td>{item.status}</td><td>{item.symptom}</td></tr>)}</tbody></table><div className="pager"><button type="button" disabled={page <= 1} onClick={() => setPage((current) => current - 1)}>上一页</button><span>第 {page} 页</span><button type="button" disabled={data.items.length < data.page_size} onClick={() => setPage((current) => current + 1)}>下一页</button></div></>}</State></Page>; }

export function SystemManagementPage({ permissionCodes }: { permissionCodes?: string[] } = {}) { return <SystemManagementContent canWrite={permissionCodes === undefined || permissionCodes.includes("identity:write")} />; }

function SystemManagementContent({ canWrite }: { canWrite: boolean }) {
  const [refresh, setRefresh] = useState(0);
  const [saving, setSaving] = useState(false);
  const [section, setSection] = useState<"users" | "roles" | "loginLogs" | "operationLogs">("roles");
  const [auditAction, setAuditAction] = useState("");
  const [auditPage, setAuditPage] = useState(1);
  const audits = useData(() => getAuditEvents({ action: auditAction || undefined, page: auditPage }), [auditAction, auditPage, refresh]);
  const users = useData(getUsers, [refresh]);
  const roles = useData(getRoles, [refresh]);
  const permissions = useData(getPermissions, [refresh]);
  const [notice, setNotice] = useState<string | null>(null);

  async function toggle(user: { id: string; enabled: boolean; role_ids: string[] }) {
    if (saving || !canWrite) return;
    setSaving(true);
    try {
      await updateUser(user.id, { enabled: !user.enabled, role_ids: user.role_ids });
      setRefresh((value) => value + 1);
      setNotice("账号状态已更新。");
    } catch {
      setNotice("账号更新失败，请检查权限或状态后重试。");
    } finally { setSaving(false); }
  }

  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (saving || !canWrite) return;
    const form = new FormData(event.currentTarget);
    setSaving(true);
    try {
      await createUser({
        username: String(form.get("username")),
        password: String(form.get("password")),
        role_ids: [String(form.get("role_id"))],
      });
      setRefresh((value) => value + 1);
      setNotice("账号已创建。");
    } catch {
      setNotice("账号创建失败，请检查输入和权限后重试。");
    } finally { setSaving(false); }
  }

  return <Page title="系统管理">
    <section className="system-hero"><div><span className="status-chip status-chip--info">RBAC 权限中心</span><h2>系统角色、组织与用户统一维护</h2><p>角色负责菜单和按钮权限，用户绑定组织与授权角色。系统管理员为唯一内置角色，不允许删除；自定义角色删除前会校验是否仍被用户绑定。</p></div><div className="system-stats"><div><span>角色总数</span><strong>{roles.value?.length ?? "—"}</strong></div><div><span>系统用户</span><strong>{users.value?.length ?? "—"}</strong></div><div><span>启用账号</span><strong>{users.value?.filter((item) => item.enabled).length ?? "—"}</strong></div></div></section>
    {notice && <p role="status">{notice}</p>}
    <div className="section-tabs" role="tablist" aria-label="系统管理分区">
      {[ ["roles", "角色管理"], ["users", "用户管理"], ["loginLogs", "登录日志"], ["operationLogs", "操作日志"] ].map(([id, label]) => <button key={id} type="button" role="tab" aria-label={label} aria-selected={section === id} onClick={() => setSection(id as typeof section)}>{label}</button>)}
    </div>
    <section className="section-tab-panel" role="tabpanel">
    {section === "users" && <><div className="panel-heading"><div><h3>账号管理</h3><p>仅身份写入权限可新增或调整账号状态。</p></div><span className={`status-chip ${canWrite ? "status-chip--success" : "status-chip--neutral"}`}>{canWrite ? "可管理" : "只读"}</span></div>
    <State state={users} empty={(items) => !items.length}>{(items) => <>
      <table><thead><tr><th>账号</th><th>状态</th><th>角色</th><th>操作</th></tr></thead><tbody>{items.map((item) => <tr key={item.id}><td>{item.username}</td><td>{item.enabled ? "启用" : "停用"}</td><td>{item.role_ids.join(", ") || "未分配"}</td><td>{canWrite ? <button type="button" disabled={saving} onClick={() => void toggle(item)}>{item.enabled ? "停用" : "启用"}</button> : "只读"}</td></tr>)}</tbody></table>
      {canWrite && <form className="portal-form" onSubmit={create}><label>用户名<input name="username" required /></label><label>初始密码<input name="password" type="password" minLength={8} required /></label><label>角色<select name="role_id">{roles.value?.map((role) => <option key={role.id} value={role.id}>{role.name}</option>)}</select></label><button type="submit" disabled={saving}>创建账号</button></form>}
    </>}</State></>}
    {section === "roles" && <><div className="panel-heading"><div><h3>角色列表</h3><p>修改会立即刷新正式角色数据。</p></div><button type="button" className="button-primary" disabled title="当前 API 未提供角色创建接口">新增角色</button></div><State state={roles} empty={(items) => !items.length}>{(items) => <div>{items.map((item) => <RolePermissionEditor key={item.id} role={item} permissions={permissions.value ?? []} canWrite={canWrite} onSaved={() => { setRefresh((value) => value + 1); setNotice("角色权限已更新。"); }} onFailed={() => setNotice("角色更新失败，请检查权限后重试。")} />)}</div>}</State></>}
    {(section === "loginLogs" || section === "operationLogs") && <><div className="panel-heading"><div><h3>{section === "loginLogs" ? "登录日志" : "操作日志"}</h3><p>只展示服务端已保留的审计记录。</p></div></div><label>动作筛选<input aria-label="审计动作筛选" value={auditAction} onChange={(event) => { setAuditAction(event.target.value); setAuditPage(1); }} placeholder="输入正式动作" /></label><State state={audits} empty={(data) => !data.count}>{(data) => <><table><thead><tr><th>时间</th><th>动作</th><th>资源</th><th>结果</th></tr></thead><tbody>{data.items.map((item: AuditEvent) => <tr key={item.id}><td>{item.created_at}</td><td>{item.action}</td><td>{item.resource_type}</td><td>{item.result}</td></tr>)}</tbody></table><div className="pager"><button type="button" disabled={auditPage <= 1} onClick={() => setAuditPage((current) => current - 1)}>上一页</button><span>第 {auditPage} 页</span><button type="button" disabled={data.items.length < data.page_size} onClick={() => setAuditPage((current) => current + 1)}>下一页</button></div></>}</State></>}
    </section>
  </Page>;
}

function RolePermissionEditor({ role, permissions, canWrite, onSaved, onFailed }: { role: { id: string; name: string; permission_codes: string[] }; permissions: Array<{ code: string }>; canWrite: boolean; onSaved: () => void; onFailed: () => void }) {
  const [selected, setSelected] = useState(role.permission_codes);
  const [saving, setSaving] = useState(false);
  useEffect(() => setSelected(role.permission_codes), [role.id, role.permission_codes]);
  async function save() {
    if (saving || !canWrite) return;
    setSaving(true);
    try {
      await updateRolePermissions(role.id, selected);
      onSaved();
    } catch {
      onFailed();
    } finally { setSaving(false); }
  }
  return <fieldset className="portal-form"><legend>{role.name}</legend><p>已选 {selected.length} 项权限。</p>{permissions.map((permission) => <label key={permission.code}><input type="checkbox" aria-label={permission.code} disabled={!canWrite} checked={selected.includes(permission.code)} onChange={(event) => setSelected((current) => event.target.checked ? [...current, permission.code] : current.filter((code) => code !== permission.code))} />{permission.code}</label>)}<button type="button" disabled={!canWrite || saving} onClick={() => void save()}>{saving ? "保存中…" : "保存角色权限"}</button></fieldset>;
}

export function IntelligentAuditPage({ permissionCodes = [] }: { permissionCodes?: string[] }) { const usage = useData(getIntelligenceUsage, []); const documents = useData(() => getKnowledgeDocuments({ page: 1 }), []); const [notice, setNotice] = useState<string | null>(null); const [action, setAction] = useState(""); const canRetryKnowledge = permissionCodes.includes("intelligence:knowledge"); async function retry(id: string) { if (!canRetryKnowledge) return; try { await retryKnowledgeDocument(id); setNotice("已提交知识文档重试请求。"); } catch (error) { setNotice(`重试失败：${error instanceof ApiError ? error.code : "REQUEST_FAILED"}`); } } return <Page title="智能运维审计"><div className="audit-workspace"><section className="audit-panel"><header><h3>受控调用概览</h3><p>保留期、调用状态和 Token 配置均来自正式审计接口。</p></header><State state={usage}>{(data) => <><div className="audit-summary"><span>保留期 <strong>{data.retention_days} 天</strong></span><span>受控记录 <strong>{data.count} 条</strong></span></div><p className="audit-note">配置 Token 预算统计，不代表模型实际消耗。</p>{data.items.length ? <table><thead><tr><th>Agent</th><th>状态</th><th>调用数</th><th>配置 Token 预算</th></tr></thead><tbody>{data.items.map((item) => <tr key={`${item.agent_id}-${item.status}`}><td>{item.agent_id}</td><td>{item.status}</td><td>{item.run_count}</td><td>{item.configured_max_reply_tokens}</td></tr>)}</tbody></table> : <p className="empty-panel">暂无受控调用记录。</p>}</>}</State></section><section className="audit-panel"><header><h3>知识文档状态</h3><p>失败重试操作仅在知识库写权限存在时可用。</p></header>{notice && <p role="status">{notice}</p>}{!canRetryKnowledge && <p role="status">当前账号没有知识库写入权限。</p>}<label className="audit-filter">动作筛选<select aria-label="知识状态筛选" value={action} onChange={(event) => setAction(event.target.value)}><option value="">全部</option><option value="FAILED">失败</option><option value="READY">完成</option></select></label><State state={documents} empty={(data) => !data.count}>{(data) => <table><thead><tr><th>文件</th><th>状态</th><th>失败原因</th><th>操作</th></tr></thead><tbody>{data.items.filter((item) => !action || item.status === action).map((item) => <tr key={item.id}><td>{item.filename}</td><td>{item.status}</td><td>{item.failure_reason ?? "—"}</td><td>{item.retry_available ? <button type="button" disabled={!canRetryKnowledge} onClick={() => void retry(item.id)}>重新同步</button> : "—"}</td></tr>)}</tbody></table>}</State></section></div></Page>; }

type OrganizationItem = { id: string; type: string; code: string; name: string; parent_id: string | null; enabled: boolean; sort_order?: number; remark?: string };

export function FactoryModelingPage({ permissionCodes }: { permissionCodes?: string[] } = {}) {
  const [refresh, setRefresh] = useState(0);
  const [saving, setSaving] = useState(false);
  const state = useData(getOrganizations, [refresh]);
  const [query, setQuery] = useState("");
  const [collapsed, setCollapsed] = useState<string[]>([]);
  const [notice, setNotice] = useState<string | null>(null);
  const [editing, setEditing] = useState<OrganizationItem | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const canWrite = permissionCodes === undefined || permissionCodes.includes("organization:write");

  async function submit(event: FormEvent<HTMLFormElement>, parent: OrganizationItem) {
    event.preventDefault();
    if (saving || !canWrite) return;
    const form = new FormData(event.currentTarget);
    setSaving(true);
    try {
      await createOrganization({ type: String(form.get("type")), code: String(form.get("code")), name: String(form.get("name")), parent_id: parent.id, sort_order: Number(form.get("sort_order")), enabled: true, remark: String(form.get("remark") ?? "") });
      setRefresh((value) => value + 1);
      setNotice("已创建组织节点。");
      setCreating(false);
    } catch (error) { setNotice(`创建失败：${error instanceof ApiError ? error.code : "REQUEST_FAILED"}`); } finally { setSaving(false); }
  }

  async function toggle(item: OrganizationItem) {
    if (saving || !canWrite) return;
    setSaving(true);
    try {
      await updateOrganization(item.id, { code: item.code, name: item.name, sort_order: item.sort_order ?? 0, enabled: !item.enabled, remark: item.remark ?? "" });
      setRefresh((value) => value + 1);
      setNotice("组织状态已更新。");
    } catch (error) { setNotice(`状态更新失败：${error instanceof ApiError ? error.code : "REQUEST_FAILED"}`); } finally { setSaving(false); }
  }

  async function remove(item: OrganizationItem) {
    if (saving || !canWrite) return;
    setSaving(true);
    try {
      await deleteOrganization(item.id);
      setRefresh((value) => value + 1);
      setNotice("组织节点已删除。");
    } catch (error) { setNotice(`删除受阻：${error instanceof ApiError ? error.code : "REQUEST_FAILED"}`); } finally { setSaving(false); }
  }

  async function saveEdit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editing || saving || !canWrite) return;
    const form = new FormData(event.currentTarget);
    setSaving(true);
    try {
      await updateOrganization(editing.id, { code: String(form.get("code")), name: String(form.get("name")), sort_order: Number(form.get("sort_order")), enabled: editing.enabled, remark: String(form.get("remark") ?? "") });
      setEditing(null);
      setRefresh((value) => value + 1);
      setNotice("组织信息已更新。");
    } catch (error) { setNotice(`编辑失败：${error instanceof ApiError ? error.code : "REQUEST_FAILED"}`); } finally { setSaving(false); }
  }

  function expandAll() { setCollapsed([]); }
  function collapseAll() { const items = (state.value ?? []) as OrganizationItem[]; setCollapsed(items.filter((item) => items.some((child) => child.parent_id === item.id)).map((item) => item.id)); }

  return <Page title="工厂建模"><p className="page-description">维护工厂、车间和产线层级；所有组织事实来自正式组织 API。</p><section className="prototype-module-note" aria-label="确认操作"><h3>确认操作</h3><p>停用或删除组织节点前由当前正式操作直接确认；未提供独立确认弹窗接口，保留原型位置。</p></section>{notice && <p role="status">{notice}</p>}{!canWrite && <p role="status">当前账号只有组织读取权限，不能修改组织结构。</p>}<State state={state} empty={(items) => !items.length}>{(items) => {
    const organizations = items as OrganizationItem[];
    const selected = organizations.find((item) => item.id === selectedId) ?? organizations[0];
    if (!selected) return null;
    const children = organizations.filter((item) => item.parent_id === selected.id);
    const childType = selected.type === "ROOT" ? "FACTORY" : selected.type === "FACTORY" ? "WORKSHOP" : "LINE";
    const canAddChild = canWrite && selected.type !== "LINE";
    return <div className="factory-workspace"><aside className="factory-tree-panel"><div className="panel-heading"><div><h3>组织结构树</h3><p>按编码或名称定位节点</p></div><span className="status-chip status-chip--neutral">{organizations.length} 个节点</span></div><div className="tree-actions"><button type="button" onClick={expandAll}>全部展开</button><button type="button" onClick={collapseAll}>全部折叠</button></div><label className="search-field">搜索组织<input aria-label="搜索组织" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索编码 / 名称" /></label><OrganizationTree items={organizations} query={query} collapsed={collapsed} selectedId={selected.id} onSelect={setSelectedId} onToggle={(id) => setCollapsed((current) => current.includes(id) ? current.filter((value) => value !== id) : [...current, id])} /></aside><section className="factory-detail-panel"><header className="panel-heading"><div><h3>{creating ? "新增下级节点" : editing ? "编辑组织节点" : "节点详情"}</h3><p>{creating ? `父节点：${selected.name}` : editing ? `正在编辑：${editing.name}` : `${selected.type} · ${selected.code}`}</p></div>{!creating && !editing && <div className="context-actions">{canAddChild && <button type="button" className="button-primary" onClick={() => setCreating(true)}>新增下级节点</button>}{canWrite && selected.type !== "ROOT" && <button type="button" className="button-secondary" onClick={() => setEditing(selected)}>编辑</button>}</div>}</header>{creating ? <form className="portal-form" onSubmit={(event) => void submit(event, selected)}><fieldset disabled={!canWrite || saving}><label>类型<select name="type" defaultValue={childType}><option value={childType}>{childType}</option></select></label><label>编码<input name="code" required /></label><label>名称<input name="name" required /></label><label>排序<input name="sort_order" type="number" min="0" defaultValue="0" /></label><label className="form-field--wide">备注<input name="remark" /></label><div className="form-actions"><button type="button" className="button-secondary" onClick={() => setCreating(false)}>取消</button><button type="submit" className="button-primary">{saving ? "创建中…" : "创建节点"}</button></div></fieldset></form> : editing ? <form className="portal-form" onSubmit={saveEdit}><fieldset disabled={!canWrite || saving}><label>编码<input name="code" required defaultValue={editing.code} /></label><label>名称<input name="name" required defaultValue={editing.name} /></label><label>排序<input name="sort_order" type="number" min="0" defaultValue={editing.sort_order ?? 0} /></label><label>备注<input name="remark" defaultValue={editing.remark ?? ""} /></label><div className="form-actions"><button type="button" className="button-secondary" onClick={() => setEditing(null)}>取消</button><button type="submit" className="button-primary">{saving ? "保存中…" : "保存组织"}</button></div></fieldset></form> : <><div className="factory-summary"><article><span>组织名称</span><strong>{selected.name}</strong></article><article><span>组织编码</span><strong>{selected.code}</strong></article><article><span>当前状态</span><strong className={selected.enabled ? "status-chip status-chip--success" : "status-chip status-chip--muted"}>{selected.enabled ? "启用" : "停用"}</strong></article><article><span>下级节点</span><strong>{children.length} 个</strong></article></div><section className="detail-note"><h4>备注</h4><p>{selected.remark || "暂无备注。"}</p></section><section className="child-table"><header><h4>下级节点</h4><span>{children.length} 个</span></header>{children.length ? <table><thead><tr><th>编码</th><th>名称</th><th>类型</th><th>状态</th></tr></thead><tbody>{children.map((item) => <tr key={item.id}><td>{item.code}</td><td><button type="button" className="link-button" onClick={() => setSelectedId(item.id)}>{item.name}</button></td><td>{item.type}</td><td><span className={item.enabled ? "status-chip status-chip--success" : "status-chip status-chip--muted"}>{item.enabled ? "启用" : "停用"}</span></td></tr>)}</tbody></table> : <p className="empty-panel">当前节点暂无下级节点。</p>}</section>{canWrite && selected.type !== "ROOT" && <div className="danger-actions"><button type="button" className="button-secondary" onClick={() => void toggle(selected)}>{selected.enabled ? "停用" : "启用"}</button><button type="button" className="button-danger" onClick={() => void remove(selected)}>删除节点</button></div>}</>}</section></div>;
  }}</State></Page>;
}

function OrganizationTree({ items, query, collapsed, selectedId, onSelect, onToggle }: { items: OrganizationItem[]; query: string; collapsed: string[]; selectedId: string; onSelect: (id: string) => void; onToggle: (id: string) => void }) {
  const byParent = new Map<string | null, OrganizationItem[]>();
  for (const item of items) byParent.set(item.parent_id, [...(byParent.get(item.parent_id) ?? []), item]);
  const matches = (item: OrganizationItem): boolean => !query || item.name.includes(query) || item.code.includes(query) || (byParent.get(item.id) ?? []).some(matches);
  const rows: Array<{ item: OrganizationItem; depth: number }> = [];
  const visited = new Set<string>();
  function visit(parentId: string | null, depth: number) { for (const item of byParent.get(parentId) ?? []) { if (visited.has(item.id) || !matches(item)) continue; visited.add(item.id); rows.push({ item, depth }); if (!collapsed.includes(item.id) || query) visit(item.id, depth + 1); } }
  visit(null, 0);
  for (const item of items) if (!visited.has(item.id) && matches(item)) { visited.add(item.id); rows.push({ item, depth: 0 }); }
  return <div className="organization-tree" role="tree" aria-label="组织结构树">{rows.map(({ item, depth }) => { const hasChildren = (byParent.get(item.id) ?? []).length > 0; const expanded = !collapsed.includes(item.id); return <div className={`organization-tree__row ${selectedId === item.id ? "is-selected" : ""}`} key={item.id} style={{ paddingLeft: `${12 + depth * 18}px` }}><button type="button" className="tree-toggle" aria-label={`${expanded ? "收起" : "展开"} ${item.name}`} disabled={!hasChildren} onClick={() => onToggle(item.id)}>{hasChildren ? (expanded ? "−" : "+") : "·"}</button><button type="button" className="tree-node" onClick={() => onSelect(item.id)}><span>{item.name}</span><small>{item.code}</small></button><span className={item.enabled ? "status-chip status-chip--success" : "status-chip status-chip--muted"}>{item.enabled ? "启用" : "停用"}</span></div>; })}</div>;
}
export function AgentReportPage() {
  const [equipmentId, setEquipmentId] = useState("");
  const [symptom, setSymptom] = useState("");
  const [description, setDescription] = useState("");
  const [urgency, setUrgency] = useState("HIGH");
  const [occurredAt, setOccurredAt] = useState("");
  const [collected, setCollected] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [collecting, setCollecting] = useState(false);
  const [attachments, setAttachments] = useState<AttachmentRef[]>([]);
  const [uploading, setUploading] = useState(false);
  const [durationMinutes, setDurationMinutes] = useState(0);
  const [runtimeEvents, setRuntimeEvents] = useState<RuntimeEvent[]>([]);

  async function addAttachment(file: File | undefined) {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const attachment = await uploadAttachment(file);
      setAttachments((current) => [...current, attachment]);
      setNotice("附件已通过安全检查，可在确认时提交。");
    } catch (caught) {
      setError(caught instanceof ApiError && caught.code === "ATTACHMENT_INFECTED" ? "附件未通过安全检查，未加入 AI 故障草稿。" : "附件上传失败，未加入 AI 故障草稿。");
    } finally {
      setUploading(false);
    }
  }

  async function collect(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (collecting || submitting) return;
    setError(null);
    setCollecting(true);
    try {
      const run = await startAgentRun("fault_reporting", { equipment_id: equipmentId }, symptom);
      setRuntimeEvents([]);
      await readRunEvents(run.run_id, (runtimeEvent) => setRuntimeEvents((current) => [...current, runtimeEvent]));
      setCollected(true);
      setNotice("AI 收集任务已创建，请补全并确认正式上报字段。");
    } catch (caught) { setError(`创建 AI 收集任务失败：${caught instanceof ApiError ? caught.code : "REQUEST_FAILED"}`); } finally { setCollecting(false); }
  }

  async function confirm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const created = await submitAgentFaultReport({ draft: { equipment_id: equipmentId, urgency, symptom, occurred_at: new Date(occurredAt).toISOString(), possible_location: undefined, description: description || undefined, attachment_refs: attachments, duration_minutes: durationMinutes }, confirmed: true });
      if ("draft" in created) throw new Error("unexpected preview");
      setNotice(`故障已正式提交：${created.number}`);
    } catch (caught) { setError(`正式提交失败：${caught instanceof ApiError ? caught.code : "REQUEST_FAILED"}`); } finally { setSubmitting(false); }
  }

  return <Page title="AI 故障上报">
    <p className="page-description">AI 只负责受控收集；它不会直接写入故障事实。正式上报必须由用户完成结构化确认。</p>
    <div className="agent-report-layout"><section className="data-card agent-chat-panel" aria-label="对话主区域"><header className="section-heading"><div><h3>对话主区域</h3><p>AI 先校验设备权限，再整理结构化上报内容。</p></div><span className={`status-chip ${collected ? "status-chip--success" : "status-chip--warning"}`}>{collected ? "已完成" : "待收集"}</span></header><div className="agent-chat-flow"><p className="agent-bubble">请描述故障现象，我会先校验设备权限，再整理为结构化上报单。</p>{symptom && <p className="agent-bubble agent-bubble--user">{symptom}</p>}{runtimeEvents.length ? <p className="agent-bubble">运行状态：{String(runtimeEvents[runtimeEvents.length - 1].data.status ?? runtimeEvents[runtimeEvents.length - 1].event)}</p> : <p className="prototype-unavailable">尚未开始 Agent 运行，暂无实时对话结果。</p>}</div><section className="agent-progress-card" aria-label="上报预收集"><header className="section-heading"><h3>上报预收集</h3><span className="status-chip status-chip--warning">{collected ? "已完成" : "待收集"}</span></header><p>设备、故障现象和运行状态将在正式 Agent 完成后汇总。</p></section></section><section className="data-card agent-summary-panel" aria-label="结构化上报摘要"><header className="section-heading"><div><h3>结构化上报摘要</h3><p>正式提交前由人工补齐并确认。</p></div><span className={`status-chip ${occurredAt && durationMinutes > 0 ? "status-chip--success" : "status-chip--warning"}`}>{occurredAt && durationMinutes > 0 ? "可提交" : "未完成"}</span></header><dl className="detail-list"><dt>已选设备</dt><dd>{equipmentId || "未选择"}</dd><dt>故障摘要</dt><dd>{symptom || "未填写"}</dd><dt>必填完成度</dt><dd>{[equipmentId, symptom, occurredAt, durationMinutes > 0 ? String(durationMinutes) : ""].filter(Boolean).length} / 4</dd><dt>提交状态</dt><dd>{collected ? "等待人工确认" : "等待 AI 收集"}</dd></dl></section></div>
    <div className="agent-report-workspace"><section className="agent-report-workspace__collect"><h3>AI 受控收集</h3><p>提交现场设备与故障描述后，页面会实时显示运行状态。</p><form className="portal-form" onSubmit={collect}>
      <fieldset disabled={collecting || submitting}>
        <label>设备 ID<input aria-label="设备 ID" value={equipmentId} onChange={(event) => setEquipmentId(event.target.value)} required /></label>
        <label>故障描述<textarea aria-label="故障描述" value={symptom} onChange={(event) => setSymptom(event.target.value)} required /></label>
        <button type="submit">{collecting ? "AI 收集中…" : "开始 AI 收集"}</button>
      </fieldset>
    </form></section><aside className="agent-report-workspace__notice"><h3>正式写入边界</h3><p>AI 线程完成后仍需补全时间、时长与附件，并由人工确认正式上报。</p><span className={`status-chip ${collected ? "status-chip--success" : "status-chip--neutral"}`}>{collected ? "可进行正式确认" : "等待 AI 收集"}</span></aside></div>
    {collected && <section className="agent-confirmation-panel"><h3 aria-label="正式字段确认">结构化上报摘要</h3><form className="portal-form" onSubmit={confirm}><label>紧急程度<select value={urgency} onChange={(event) => setUrgency(event.target.value)}><option>HIGH</option><option>MEDIUM</option><option>LOW</option></select></label><label>发生时间<input aria-label="发生时间" type="datetime-local" value={occurredAt} onChange={(event) => setOccurredAt(event.target.value)} required /></label><label>持续时间（分钟）<input aria-label="持续时间（分钟）" type="number" min="0" value={durationMinutes} onChange={(event) => setDurationMinutes(Number(event.target.value))} /></label><label>补充说明<textarea value={description} onChange={(event) => setDescription(event.target.value)} /></label><label>附件<input aria-label="AI 故障附件" type="file" disabled={uploading || submitting} onChange={(event) => void addAttachment(event.target.files?.[0])} /></label>{uploading && <p role="status">附件正在上传并进行安全检查…</p>}{attachments.length > 0 && <ul aria-label="AI 草稿附件">{attachments.map((item) => <li key={item.object_key}>{item.filename}</li>)}</ul>}<div className="form-actions"><button type="button" className="button-secondary" onClick={() => { setCollected(false); setNotice("已返回上报预收集，可继续补充现场信息。"); }}>继续补充</button><button type="submit" disabled={submitting || uploading || !occurredAt}>{submitting ? "提交中…" : "确认并提交正式故障单"}</button></div></form></section>}
    {error && <p role="alert">{error}</p>}{notice && <p role="status">{notice}</p>}<p><Link to="/fault-report">转人工表单</Link></p>
  </Page>;
}
