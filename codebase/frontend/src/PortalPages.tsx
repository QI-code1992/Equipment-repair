import { FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ApiError, AuditEvent, BiDashboard, Equipment, MaintenanceRecord, WorkOrder, createOrganization, createRole, createUser, deleteOrganization, deleteRole, getAuditEvents, getBiDashboard, getEquipment, getEquipmentDetail, getEquipmentHistory, getIntelligenceUsage, getKnowledgeDocuments, getLoginEvents, getMaintenanceRecord, getMaintenanceRecords, getOrganizations, getPermissions, getRoles, getUsers, getWorkOrders, readRunEvents, requestJson, resetUserPassword, retryKnowledgeDocument, startAgentRun, submitAgentFaultReport, uploadAttachment, updateOrganization, updateRole, updateRolePermissions, updateUser, type AttachmentRef, type LoginEvent, type RuntimeEvent, type SystemRole, type SystemUser } from "./api";

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

function Page({ children }: { title: string; children: React.ReactNode }) {
  return <section className="portal-page">{children}</section>;
}

function State<T>({ state, children, empty }: { state: LoadState<T>; children: (value: T) => React.ReactNode; empty?: (value: T) => boolean }) {
  if (state.loading) return <p role="status">正在加载…</p>;
  if (state.error) return <p role="alert">请求失败：{state.error}</p>;
  if (state.value !== null && empty?.(state.value)) return <p role="status">暂无可展示的正式业务数据。</p>;
  return state.value !== null ? <>{children(state.value)}</> : null;
}

export function BiDashboardPage() {
  const [organizationId, setOrganizationId] = useState("");
  const [period, setPeriod] = useState<"day" | "week" | "month">("day");
  const [notice, setNotice] = useState<string | null>(null);
  const state = useData<BiDashboard>(() => getBiDashboard(organizationId || undefined, period), [organizationId, period]);
  const organizations = useData(getOrganizations, []);
  const equipment = useData<Equipment[]>(getEquipment, []);
  const [healthEquipment, setHealthEquipment] = useState<Equipment | null>(null);
  const reset = () => { setOrganizationId(""); setPeriod("day"); setNotice("筛选条件已重置。"); };
  return <Page title="驾驶舱 BI">
    <form className="bi-filter" aria-label="驾驶舱筛选条件" onSubmit={(event) => { event.preventDefault(); setNotice("已按当前筛选条件查询正式数据。"); }}>
      <div className="bi-filter__grid">
        <label>时间范围<select aria-label="时间范围" value={period} onChange={(event) => setPeriod(event.target.value as typeof period)}><option value="day">最近 1 天</option><option value="week">最近 7 天</option><option value="month">最近 30 天</option></select></label>
        <label>组织<select aria-label="组织筛选" value={organizationId} onChange={(event) => setOrganizationId(event.target.value)} disabled={organizations.loading || !!organizations.error}><option value="">全部组织</option>{organizations.value?.filter((item) => item.enabled).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
        <label>区域<select aria-label="区域筛选" disabled title="当前 BI API 未提供区域筛选字段"><option>全部区域</option></select></label>
        <label>设备类型<select aria-label="设备类型筛选" disabled title="当前 BI API 未提供设备类型筛选字段"><option>全部类型</option></select></label>
      </div>
      <div className="bi-filter__actions"><button className="button-primary" type="submit">查询</button><button className="button-secondary" type="button" onClick={reset}>重置</button></div>
    </form>
    {notice && <p role="status" className="bi-notice">{notice}</p>}
    {organizations.error && <p role="alert">组织筛选不可用：{organizations.error}</p>}
    {state.error?.includes("ORGANIZATION_NOT_FOUND") && <p role="alert">所选组织不存在或已被移除。</p>}
    <State state={state}>{(value) => <>
      <section aria-labelledby="bi-summary-title"><div className="section-title"><div><h3 id="bi-summary-title">管理摘要</h3><p>整体经营与运维表现 · 较上期对比</p></div></div><div className="bi-kpi-grid"><BiMetric label="设备健康综合评分" value="—" hint="当前 BI API 未提供健康评分聚合" unavailable /><BiMetric label="故障总数" value={`${value.summary.fault_count}`} suffix="次" /><BiMetric label="工单总数" value={`${value.efficiency.completed_work_order_count}`} suffix="单" /><BiMetric label="工单按时完成率" value={`${Math.round(value.summary.completion_rate * 100)}`} suffix="%" /><BiMetric label="平均维修时长 MTTR" value={value.efficiency.average_completion_hours === null ? "—" : `${value.efficiency.average_completion_hours}`} suffix={value.efficiency.average_completion_hours === null ? undefined : "小时"} unavailable={value.efficiency.average_completion_hours === null} /></div></section>
      <section className="data-card bi-analytics-panel" aria-labelledby="bi-trend-title"><div className="section-title"><div><h3 id="bi-trend-title">趋势分析</h3><p>按时间观察健康、故障和工单的变化趋势</p></div><div className="bi-segmented" role="group" aria-label="趋势粒度">{(["day", "week", "month"] as const).map((item) => <button type="button" key={item} className={period === item ? "is-active" : ""} onClick={() => setPeriod(item)}>{({ day: "日", week: "周", month: "月" })[item]}</button>)}</div></div><div className="bi-trend-grid"><section className="bi-chart-panel"><h4>健康综合评分趋势</h4><p className="empty-panel">当前 BI API 未提供健康评分趋势。</p></section><section className="bi-chart-panel"><h4>故障数量趋势</h4>{value.trend.length ? <TrendChart trend={value.trend} /> : <p>暂无趋势数据。</p>}</section><section className="bi-chart-panel"><h4>工单数量趋势</h4>{value.trend.length ? <BiOrderTrendChart trend={value.trend} /> : <p>暂无趋势数据。</p>}</section></div></section>
      <section className="data-card bi-analytics-panel" aria-labelledby="bi-efficiency-title"><div className="section-title"><div><h3 id="bi-efficiency-title">效率分析</h3><p>聚合指标用于管理层效率判断，不展示具体工单列表</p></div></div><div className="bi-efficiency-grid"><article className="bi-efficiency-item is-unavailable"><strong>—</strong><span>计划工单完成率</span><em>当前 BI API 未提供计划工单汇总</em></article><article className="bi-efficiency-item is-unavailable"><strong>—</strong><span>平均响应时长</span><em>当前 BI API 未提供响应时长汇总</em></article><article className={`bi-efficiency-item ${value.efficiency.average_completion_hours === null ? "is-unavailable" : ""}`}><strong>{value.efficiency.average_completion_hours === null ? "—" : value.efficiency.average_completion_hours}<small>{value.efficiency.average_completion_hours === null ? "" : "小时"}</small></strong><span>平均维修时长</span><em>{value.efficiency.average_completion_hours === null ? "当前 BI API 未提供维修时长汇总" : "来自当前筛选窗口"}</em></article><article className="bi-efficiency-item is-unavailable"><strong>—</strong><span>首次修复率</span><em>当前 BI API 未提供首次修复汇总</em></article></div></section>
      <section className="data-card bi-health-list" aria-labelledby="bi-health-list-title"><div className="section-title"><div><h3 id="bi-health-list-title">设备健康列表</h3><p>点击设备行进入设备驾驶舱详情，查看健康趋势、故障类型分布和工单分析。</p></div><a className="button-secondary" href="/equipment">查看全部设备</a></div>{equipment.loading ? <p role="status" className="empty-panel">正在加载正式设备数据…</p> : equipment.error ? <p role="alert" className="empty-panel">设备列表不可用：{equipment.error}</p> : <><div className="table-wrap"><table className="health-table"><thead><tr><th>设备编号 / 名称</th><th>设备型号</th><th>负责人</th><th>健康评分</th><th>风险等级</th><th>近7天故障</th><th>工单状态</th><th>操作</th></tr></thead><tbody>{equipment.value?.length ? equipment.value.map((item) => <tr key={item.id}><td><a href={`/equipment/${item.id}`}><strong>{item.code}</strong><span>{item.name}</span></a></td><td>{item.model}</td><td>{item.owner_user_id ?? "未分配"}</td><td>—</td><td>—</td><td>—</td><td>—</td><td><a className="link-btn" href={`/equipment/${item.id}?openHealthScore=1`} onClick={(event) => { event.preventDefault(); setHealthEquipment(item); }}>查看分析</a></td></tr>) : <tr><td colSpan={8}>暂无可展示的正式设备数据。</td></tr>}</tbody></table></div><p className="result-status" role="status">当前显示 {equipment.value?.length ?? 0} 台正式设备。</p><div className="table-note"><span>共 {equipment.value?.length ?? 0} 台正式设备</span><span>数据更新时间：当前接口未提供</span></div></>}</section>
      <section className="data-card bi-analytics-panel" aria-labelledby="bi-history-title"><div className="section-title"><div><h3 id="bi-history-title">指标历史对比</h3><p>本期与上期故障统计来自正式 BI API。</p></div></div><div className="table-wrap"><table><thead><tr><th>指标</th><th>本期</th><th>上期</th><th>变化值</th><th>变化率</th><th>趋势</th></tr></thead><tbody><BiHistoryRow label="故障总数（次）" current={value.history_comparison.current_fault_count} previous={value.history_comparison.previous_fault_count} /><tr><td>健康综合评分</td><td colSpan={4}>—（当前 API 未提供）</td><td>—</td></tr><tr><td>工单按时完成率</td><td colSpan={4}>—（当前 API 未提供上期值）</td><td>—</td></tr></tbody></table></div></section>
    </>}</State>
    {healthEquipment && <div className="bi-drawer-layer"><div className="bi-drawer-scrim" onClick={() => setHealthEquipment(null)} /><aside className="bi-health-drawer" role="dialog" aria-modal="true" aria-label="设备健康分析"><header><div><strong>设备健康分析</strong><span>{healthEquipment.code} · {healthEquipment.name}</span></div><button type="button" className="icon-button" aria-label="关闭设备健康分析" onClick={() => setHealthEquipment(null)}>×</button></header><div className="bi-health-drawer__summary"><div><span>设备型号</span><strong>{healthEquipment.model}</strong></div><div><span>负责人</span><strong>{healthEquipment.owner_user_id ?? "未分配"}</strong></div></div><p className="empty-panel">当前接口未提供健康趋势、风险等级和处置建议。</p><a className="button-primary" href={`/equipment/${healthEquipment.id}`}>查看设备详情</a></aside></div>}
  </Page>;
}

function BiMetric({ label, value, suffix, hint, unavailable = false }: { label: string; value: string; suffix?: string; hint?: string; unavailable?: boolean }) { return <article className={`bi-metric ${unavailable ? "is-unavailable" : ""}`}><span>{label}</span><strong>{value}{suffix && <small>{suffix}</small>}</strong><em>{hint ?? (unavailable ? "当前接口未提供该正式数据" : "来自当前筛选窗口")}</em></article>; }

function BiHistoryRow({ label, current, previous }: { label: string; current: number; previous: number }) { const delta = current - previous; const rate = previous === 0 ? null : delta / previous * 100; return <tr><td>{label}</td><td>{current}</td><td>{previous}</td><td>{delta > 0 ? `+${delta}` : delta}</td><td>{rate === null ? "—" : `${rate > 0 ? "+" : ""}${rate.toFixed(1)}%`}</td><td>—</td></tr>; }

function TrendChart({ trend }: { trend: BiDashboard["trend"] }) {
  const maximum = Math.max(1, ...trend.flatMap((item) => [item.fault_count, item.completed_work_order_count]));
  return <div className="bi-trend" role="img" aria-label="故障与完成工单趋势">{trend.map((item) => <div className="bi-trend__item" key={item.date}><div className="bi-trend__bars" aria-hidden="true"><span className="bi-trend__bar bi-trend__bar--fault" style={{ height: `${item.fault_count / maximum * 100}%` }} /><span className="bi-trend__bar bi-trend__bar--completed" style={{ height: `${item.completed_work_order_count / maximum * 100}%` }} /></div><p>{item.date}：故障 {item.fault_count}，完成 {item.completed_work_order_count}</p></div>)}</div>;
}

function BiOrderTrendChart({ trend }: { trend: BiDashboard["trend"] }) { const maximum = Math.max(1, ...trend.map((item) => item.completed_work_order_count)); return <div className="bi-trend" role="img" aria-label="完成工单数量趋势">{trend.map((item) => <div className="bi-trend__item" key={item.date}><div className="bi-trend__bars"><span className="bi-trend__bar bi-trend__bar--completed" style={{ height: `${item.completed_work_order_count / maximum * 100}%` }} /></div><p>{item.date}：完成 {item.completed_work_order_count}</p></div>)}</div>; }

export function EquipmentLedgerPage() {
  const state = useData<Equipment[]>(getEquipment, []);
  const organizations = useData(getOrganizations, []);
  const [codeQuery, setCodeQuery] = useState("");
  const [nameQuery, setNameQuery] = useState("");
  const [factoryId, setFactoryId] = useState("");
  const [workshopId, setWorkshopId] = useState("");
  const [lineId, setLineId] = useState("");
  const [notice, setNotice] = useState<string | null>(null);
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
    const filtered = items.filter((item) => (!codeQuery || item.code.toLowerCase().includes(codeQuery.toLowerCase())) && (!nameQuery || item.name.toLowerCase().includes(nameQuery.toLowerCase())) && (!selectedOrganizationIds || selectedOrganizationIds.has(item.organization_id)));
    const reset = () => { setFactoryId(""); setWorkshopId(""); setLineId(""); setCodeQuery(""); setNameQuery(""); setNotice("筛选条件已重置。"); };
    return <>
      <section className="ledger-toolbar ledger-toolbar--hierarchy" aria-label="设备筛选工具栏">
        <label>工厂<select aria-label="设备所属工厂" value={factoryId} onChange={(event) => { setFactoryId(event.target.value); setWorkshopId(""); setLineId(""); }} disabled={organizations.loading || !!organizations.error}><option value="">全部工厂</option>{factories.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
        <label>车间<select aria-label="设备所属车间" value={workshopId} onChange={(event) => { setWorkshopId(event.target.value); setLineId(""); }} disabled={!factoryId || organizations.loading || !!organizations.error}><option value="">全部车间</option>{workshops.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
        <label>产线<select aria-label="设备所属产线" value={lineId} onChange={(event) => setLineId(event.target.value)} disabled={!workshopId || organizations.loading || !!organizations.error}><option value="">全部产线</option>{lines.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
        <label>设备编号<input aria-label="设备编号筛选" value={codeQuery} onChange={(event) => setCodeQuery(event.target.value)} placeholder="搜索设备编号" /></label>
        <label>设备名称<input aria-label="设备名称筛选" value={nameQuery} onChange={(event) => setNameQuery(event.target.value)} placeholder="搜索设备名称" /></label>
        <label>健康评分<select aria-label="健康评分筛选" disabled title="当前设备台账 API 未提供健康评分字段"><option>全部评分</option></select></label>
        <div className="ledger-toolbar__actions"><button type="button" className="button-secondary" onClick={reset}>重置</button><button type="button" className="button-primary" onClick={() => setNotice("已按当前条件筛选正式设备数据。")}>查询</button><Link className="button-primary ledger-toolbar__create" to="/equipment/new">新增设备</Link></div>
      </section>
      {notice && <p role="status" className="ledger-notice">{notice}</p>}
      <section className="ledger-table-panel">
        <header><div><h3>设备列表</h3><p>{filtered.length === items.length ? `共加载 ${items.length} 台正式设备。` : `当前显示 ${filtered.length} 台符合筛选条件的设备。`}</p></div></header>
        {filtered.length ? <table><thead><tr><th>序号</th><th>设备编号</th><th>设备名称</th><th>型号</th><th>负责人</th><th>健康评分</th><th>操作</th></tr></thead><tbody>{filtered.map((item, index) => <tr key={item.id}><td>{index + 1}</td><td>{item.code}</td><td>{item.name}</td><td>{item.model}</td><td>{item.owner_user_id ?? "未分配"}</td><td><span className="score-pill score-pill--unavailable" title="当前设备台账 API 未提供健康评分">—</span></td><td className="table-actions"><Link to={`/equipment/${item.id}`}>详情</Link><Link to={`/equipment/${item.id}/edit`}>编辑</Link></td></tr>)}</tbody></table> : <p className="empty-panel" role="status">{items.length ? "没有符合筛选条件的正式设备数据。" : "尚未登记正式设备。"}</p>}
      </section>
    </>;
  })()}</Page>;
}

export function EquipmentDetailPage() {
  const { id = "" } = useParams();
  const equipment = useData(() => getEquipmentDetail(id), [id]);
  const history = useData(() => getEquipmentHistory(id), [id]);
  const [detailTab, setDetailTab] = useState<"graph" | "bom" | "params" | "docs" | "records">("graph");
  return <Page title="设备详情"><State state={equipment}>{(item) => <>
    <section className="equipment-hero"><div><p className="page-shell__eyebrow">资产身份</p><h3>{item.name}</h3><p>{item.code} · {item.model} · {item.manufacturer}</p></div><div className="context-actions"><Link className="button-secondary" to="/equipment">返回台账</Link><Link className="button-primary" to={`/equipment/${item.id}/edit`}>编辑设备</Link></div></section>
    <div className="equipment-detail-grid"><section className="data-card"><h3>资产身份</h3><dl className="detail-list"><dt>设备编码</dt><dd>{item.code}</dd><dt>设备类型</dt><dd>{item.type}</dd><dt>所属组织</dt><dd>{item.organization_id}</dd><dt>负责人 ID</dt><dd>{item.owner_user_id ?? "未分配"}</dd></dl></section><section className="data-card"><h3>运行与关键参数</h3><dl className="detail-list"><dt>运行状态</dt><dd><span className={`status-chip ${item.status === "FAULT" ? "status-chip--danger" : item.status === "NORMAL" ? "status-chip--success" : "status-chip--neutral"}`}>{item.status}</span></dd><dt>累计工时</dt><dd>{item.operating_hours}</dd><dt>制造日期</dt><dd>{item.manufactured_at ?? "未登记"}</dd><dt>投用日期</dt><dd>{item.commissioned_at ?? "未登记"}</dd></dl></section></div>
    <section className="equipment-health-summary"><div><h3>当前健康评分</h3><p>当前设备 API 未提供健康评分明细。</p></div><button type="button" aria-label="设备健康评分" className="health-score-trigger" disabled title="当前 API 未提供健康评分明细">暂无评分</button></section>
    <section className="equipment-detail-tabs" aria-label="设备详情分区"><div role="tablist">{[["graph", "图谱关系"], ["bom", "BOM 组成"], ["params", "额定参数"], ["docs", "知识文档"], ["records", "维修记录"]].map(([id, label]) => <button type="button" role="tab" aria-selected={detailTab === id} key={id} onClick={() => setDetailTab(id as typeof detailTab)}>{label}</button>)}</div>{detailTab === "records" ? <div className="equipment-tab-content"><h3>维修记录</h3><p>维修历史见下方正式维修记录接口。</p></div> : <div className="equipment-tab-content"><h3>{detailTab === "graph" ? "关联内容" : detailTab === "bom" ? "BOM 组成" : detailTab === "params" ? "额定参数" : "知识文档"}</h3><p>当前接口未提供该设备的图谱、BOM、额定参数或知识文档数据。</p></div>}</section>
  </>}</State><section className="history-panel"><header><div><h3>维修历史</h3><p>工单、故障和维修结论来自正式维修记录接口。</p></div></header><State state={history}>{(data) => <>{data.count ? <RecordsTable items={data.items} /> : <p className="empty-panel" role="status">暂无维修历史记录。</p>}<section className="history-trend" aria-label="维修完成趋势"><h4>维修完成趋势</h4>{data.trend.length ? <ul>{data.trend.map((item) => <li key={item.date}>{item.date}：完成 {item.completed_count} 次</li>)}</ul> : <p>暂无维修完成趋势。</p>}</section></>}</State></section></Page>;
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
  useEffect(() => {
    if (!edit || !details.value || !organizations.value || lineId) return;
    const line = organizations.value.find((item) => item.id === details.value?.organization_id);
    const workshop = organizations.value.find((item) => item.id === line?.parent_id);
    const factory = organizations.value.find((item) => item.id === workshop?.parent_id);
    setFactoryId(factory?.id ?? "");
    setWorkshopId(workshop?.id ?? "");
    setLineId(line?.id ?? "");
  }, [details.value, edit, lineId, organizations.value]);
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
      organization_id: String(form.get("organization_id")),
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
  if (details.loading || organizations.loading || users.loading) return <Page title={edit ? "编辑设备" : "新增设备"}><p role="status">正在加载…</p></Page>;
  if (details.error || organizations.error || users.error) return <Page title={edit ? "编辑设备" : "新增设备"}><p role="alert">无法加载设备依赖：{details.error ?? organizations.error ?? users.error}</p></Page>;
  const organizationItems = organizations.value ?? [];
  const factories = organizationItems.filter((item) => item.type === "FACTORY" && item.enabled);
  const workshops = organizationItems.filter((item) => item.type === "WORKSHOP" && item.enabled && item.parent_id === factoryId);
  const lines = organizationItems.filter((item) => item.type === "LINE" && item.enabled && item.parent_id === workshopId);
  const owners = (users.value ?? []).filter((item) => item.enabled);
  return <Page title={edit ? "编辑设备" : "新增设备"}>
    <form className="equipment-form" onSubmit={submit}>
      <header><div><p className="page-shell__eyebrow">{edit ? "维护已有资产字段" : "登记正式设备资产"}</p><h3>{edit ? current?.name ?? "编辑设备" : "新增设备"}</h3><p>保存只提交当前表单中的正式设备字段。</p></div><Link className="button-secondary" to={edit ? `/equipment/${id}` : "/equipment"}>返回</Link></header>
      <fieldset><legend>设备基础信息</legend><div className="portal-form equipment-basic-grid"><label>设备编码<input name="code" required defaultValue={current?.code} /></label><label>设备名称<input name="name" required defaultValue={current?.name} /></label><label>型号<input name="model" required defaultValue={current?.model} /></label><label>类型<input name="type" required defaultValue={current?.type} /></label><label>制造商<input name="manufacturer" required defaultValue={current?.manufacturer} /></label><label>所属工厂<select aria-label="所属工厂" required value={factoryId} onChange={(event) => { setFactoryId(event.target.value); setWorkshopId(""); setLineId(""); }}><option value="">请选择工厂</option>{factories.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label>所属车间<select aria-label="所属车间" required disabled={!factoryId} value={workshopId} onChange={(event) => { setWorkshopId(event.target.value); setLineId(""); }}><option value="">请选择车间</option>{workshops.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label>所属产线<select name="organization_id" aria-label="所属产线" required disabled={!workshopId} value={lineId} onChange={(event) => setLineId(event.target.value)}><option value="">请选择产线</option>{lines.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label></div></fieldset>
      <fieldset><legend>运行与归属</legend><div className="portal-form"><label>负责人<select name="owner_user_id" aria-label="负责人" defaultValue={current?.owner_user_id ?? ""}><option value="">未分配</option>{owners.map((item) => <option key={item.id} value={item.id}>{item.username}</option>)}</select></label><label>运行工时<input name="operating_hours" type="number" min="0" defaultValue={current?.operating_hours ?? 0} /></label><label>状态<select name="status" defaultValue={current?.status ?? "NORMAL"}><option>NORMAL</option><option>FAULT</option><option>REPAIRING</option><option>DISABLED</option></select></label><label>制造日期<input aria-label="制造日期" name="manufactured_at" type="date" defaultValue={current?.manufactured_at ?? ""} /></label><label>投用日期<input aria-label="投用日期" name="commissioned_at" type="date" defaultValue={current?.commissioned_at ?? ""} /></label></div></fieldset>
      <fieldset><legend>设备图片引用</legend><div className="portal-form"><label>图片对象键<input aria-label="图片对象键" name="image_object_key" defaultValue={currentImage?.object_key ?? ""} /></label><label>图片文件名<input aria-label="图片文件名" name="image_filename" defaultValue={currentImage?.filename ?? ""} /></label></div></fieldset>
      <fieldset className="equipment-boundary-section"><legend>设备 BOM 组成</legend><div className="section-title"><span>列表维护 2–4 级分支节点</span><button type="button" className="button-secondary" disabled>新增分支节点</button></div><div className="table-wrap"><table><thead><tr><th>层级</th><th>上级节点</th><th>分支节点编码</th><th>分支节点名称</th><th>描述</th><th>单位</th><th>BOM 用量</th><th>操作</th></tr></thead><tbody><tr><td colSpan={8}>当前接口未提供该设备的 BOM 数据。</td></tr></tbody></table></div></fieldset>
      <fieldset className="equipment-boundary-section"><legend>设备额定参数</legend><div className="section-title"><span>设备运行额定参数与阈值</span><button type="button" className="button-secondary" disabled>新增参数</button></div><div className="table-wrap"><table><thead><tr><th>序号</th><th>参数名</th><th>额定参数值</th><th>浮动上限</th><th>浮动下限</th><th>单位</th><th>说明</th><th>操作</th></tr></thead><tbody><tr><td colSpan={8}>当前接口未提供该设备的额定参数数据。</td></tr></tbody></table></div></fieldset>
      <fieldset className="equipment-boundary-section"><legend>知识资料</legend><div className="section-title"><span>维修手册、故障手册与历史案例</span><button type="button" className="button-secondary" disabled>上传资料</button></div><div className="table-wrap"><table><thead><tr><th>序号</th><th>文件类型</th><th>文件名</th><th>文件大小</th><th>上传时间</th><th>文件格式</th><th>操作</th></tr></thead><tbody><tr><td colSpan={7}>当前接口未提供该设备的知识资料数据。</td></tr></tbody></table></div></fieldset>
      <footer><Link className="button-secondary" to="/equipment">取消</Link><button type="submit" disabled={!lineId || saving}>{saving ? "保存中…" : "保存设备"}</button>{!lineId && <p role="alert">请选择启用的工厂、车间和产线后再保存。</p>}{message && <p role="status">{message}</p>}</footer>
    </form>
  </Page>;
}
export const EquipmentAddPage = () => <EquipmentForm />;
export const EquipmentEditPage = () => <EquipmentForm edit />;

function RecordsTable({ items }: { items: MaintenanceRecord[] }) { return <table><thead><tr><th>工单</th><th>状态</th><th>故障</th><th>结论</th><th>知识状态</th><th>操作</th></tr></thead><tbody>{items.map((item) => <tr key={item.maintenance_record_id}><td>{item.work_order_number}</td><td>{item.status}</td><td>{item.symptom}</td><td>{item.repair_result ?? "未完成"}</td><td>{item.knowledge_status}</td><td><Link to={`/maintenance-records/${item.maintenance_record_id}`}>详情</Link></td></tr>)}</tbody></table>; }

export function MaintenanceRecordsPage() {
  const [equipmentId, setEquipmentId] = useState("");
  const [knowledgeStatus, setKnowledgeStatus] = useState("");
  const [page, setPage] = useState(1);
  const [view, setView] = useState<"overview" | "records">("overview");
  const state = useData(() => getMaintenanceRecords({ equipmentId: equipmentId || undefined, knowledgeStatus: knowledgeStatus || undefined, page }), [equipmentId, knowledgeStatus, page]);
  const filters = <section className="maintenance-filter"><header><h3>维修记录检索</h3><p>按正式设备 ID 和知识关联状态查询维修档案。</p></header><div className="maintenance-filter__fields"><label>设备筛选<input aria-label="维修记录设备筛选" value={equipmentId} onChange={(event) => { setEquipmentId(event.target.value); setPage(1); }} placeholder="输入正式设备 ID" /></label><label>知识状态<select aria-label="维修记录知识状态筛选" value={knowledgeStatus} onChange={(event) => { setKnowledgeStatus(event.target.value); setPage(1); }}><option value="">全部</option><option value="NOT_LINKED">未关联</option><option value="LINKED">已关联</option></select></label><div className="maintenance-filter__actions"><button type="button" className="button-secondary" onClick={() => { setEquipmentId(""); setKnowledgeStatus(""); setPage(1); }}>重置</button></div></div></section>;
  return <Page title="维修记录"><div className="maintenance-tabs" role="tablist" aria-label="维修记录视图"><button type="button" role="tab" aria-selected={view === "overview"} className={view === "overview" ? "is-active" : ""} onClick={() => setView("overview")}>维修概览</button><button type="button" role="tab" aria-selected={view === "records"} className={view === "records" ? "is-active" : ""} onClick={() => setView("records")}>维修记录列表</button></div>{view === "overview" ? <section role="tabpanel" aria-label="维修概览">{filters}<State state={state}>{(data) => <><section className="maintenance-kpis" aria-label="维修概览指标" data-testid="maintenance-kpi-grid" data-layout="six-column"><article><span>总维修次数</span><strong>{data.count}</strong><em>正式维修记录总数</em></article><article><span>待处理维修</span><strong>—</strong><em>当前接口未提供全量状态汇总</em></article><article><span>平均修复时间 MTTR</span><strong>—</strong><em>当前接口未提供该正式数据</em></article><article><span>平均故障间隔 MTBF</span><strong>—</strong><em>当前接口未提供该正式数据</em></article><article><span>平均维修时间</span><strong>—</strong><em>当前接口未提供该正式数据</em></article><article><span>维修完成率</span><strong>—</strong><em>当前接口未提供该正式数据</em></article></section><section className="maintenance-charts" aria-label="维修概览图表" data-testid="maintenance-chart-grid" data-layout="two-column">{["故障类型分布", "维修时长分布", "设备状态分布", "故障次数趋势"].map((title) => <article className="data-card" key={title}><h3>{title}</h3><p className="empty-panel">当前接口未提供该正式数据。</p></article>)}</section></>}</State></section> : <section role="tabpanel" aria-label="维修记录列表">{filters}<section className="maintenance-records-panel"><header><div><h3>维修记录列表</h3><p>第 {page} 页的正式维修记录。</p></div><div className="maintenance-list-actions"><span className="status-chip status-chip--neutral">{state.value?.count ?? 0} 条记录</span><button type="button" className="button-secondary" disabled title="当前接口未提供维修记录导出">导出</button></div></header><State state={state} empty={(data) => !data.count}>{(data) => <><RecordsTable items={data.items} /><div className="pager"><span>显示本页 {data.items.length} 条，共 {data.count} 条</span><button type="button" disabled={page <= 1} onClick={() => setPage((current) => current - 1)}>上一页</button><span>第 {page} 页</span><button type="button" disabled={data.items.length < data.page_size} onClick={() => setPage((current) => current + 1)}>下一页</button></div></>}</State></section></section>}</Page>;
}
export function MaintenanceRecordDetailPage() { const { id = "" } = useParams(); const state = useData(() => getMaintenanceRecord(id), [id]); return <Page title="维修记录详情"><State state={state}>{(item) => <><section className="equipment-hero"><div><p className="page-shell__eyebrow">维修工单</p><h3>{item.work_order_number}</h3><p>设备 ID：{item.equipment_id} · 工单状态：{item.status}</p></div><Link className="button-secondary" to="/maintenance-records">返回记录</Link></section><div className="maintenance-detail-grid"><section className="data-card"><h3>故障与根因</h3><dl className="detail-list"><dt>故障现象</dt><dd>{item.symptom}</dd><dt>实际原因</dt><dd>{item.actual_cause ?? "未填写"}</dd><dt>解决方案</dt><dd>{item.actual_solution ?? "未填写"}</dd></dl></section><section className="data-card"><h3>维修结论</h3><dl className="detail-list"><dt>维修结果</dt><dd>{item.repair_result ?? "未完成"}</dd><dt>更换部件</dt><dd>{item.parts_replacement_notes ?? "无"}</dd><dt>知识状态</dt><dd>{item.knowledge_status}</dd><dt>完成时间</dt><dd>{item.completed_at ?? "未完成"}</dd></dl></section></div></>}</State></Page>; }
export function WorkOrdersPage() { const [status, setStatus] = useState(""); const [page, setPage] = useState(1); const state = useData(() => getWorkOrders({ status: status || undefined, page }), [status, page]); return <Page title="维修执行"><label>工单状态<select aria-label="工单状态筛选" value={status} onChange={(event) => { setStatus(event.target.value); setPage(1); }}><option value="">全部</option><option value="PENDING_ACCEPT">待接单</option><option value="IN_REPAIR">维修中</option><option value="PENDING_INSPECTION">待验收</option><option value="COMPLETED">已完成</option></select></label><State state={state} empty={(data) => !data.count}>{(data) => <><table><thead><tr><th>工单</th><th>设备</th><th>状态</th><th>故障</th></tr></thead><tbody>{data.items.map((item: WorkOrder) => <tr key={item.id}><td>{item.number}</td><td>{item.equipment_id}</td><td>{item.status}</td><td>{item.symptom}</td></tr>)}</tbody></table><div className="pager"><button type="button" disabled={page <= 1} onClick={() => setPage((current) => current - 1)}>上一页</button><span>第 {page} 页</span><button type="button" disabled={data.items.length < data.page_size} onClick={() => setPage((current) => current + 1)}>下一页</button></div></>}</State></Page>; }

export function SystemManagementPage({ permissionCodes }: { permissionCodes?: string[] } = {}) { return <SystemManagementContent canWrite={permissionCodes === undefined || permissionCodes.includes("identity:write")} />; }

function SystemManagementContent({ canWrite }: { canWrite: boolean }) {
  const [refresh, setRefresh] = useState(0);
  const [saving, setSaving] = useState(false);
  const [section, setSection] = useState<"roles" | "users" | "loginLogs" | "operationLogs">("roles");
  const [roleQuery, setRoleQuery] = useState("");
  const [userQuery, setUserQuery] = useState("");
  const [userRoleId, setUserRoleId] = useState("");
  const [userPage, setUserPage] = useState(1);
  const [rolePage, setRolePage] = useState(1);
  const [editingRoleId, setEditingRoleId] = useState<string | null>(null);
  const [roleModal, setRoleModal] = useState<"new" | "edit" | null>(null);
  const [userModal, setUserModal] = useState<"new" | "edit" | "detail" | null>(null);
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [loginQuery, setLoginQuery] = useState("");
  const [loginResult, setLoginResult] = useState("");
  const [loginRange, setLoginRange] = useState("");
  const [operationQuery, setOperationQuery] = useState("");
  const [operationModule, setOperationModule] = useState("");
  const [operationResult, setOperationResult] = useState("");
  const [loginPage, setLoginPage] = useState(1);
  const [operationPage, setOperationPage] = useState(1);
  const loginEvents = useData(() => section === "loginLogs" ? getLoginEvents({ username: loginQuery || undefined, result: loginResult || undefined, page: loginPage }) : Promise.resolve({ items: [], count: 0, page: 1, page_size: 20 }), [section, refresh, loginQuery, loginResult, loginPage]);
  const audits = useData(getAuditEvents, [refresh]);
  const users = useData(getUsers, [refresh]);
  const roles = useData(getRoles, [refresh]);
  const permissions = useData(getPermissions, []);
  const [notice, setNotice] = useState<string | null>(null);

  async function toggle(user: SystemUser) {
    if (saving || !canWrite) return;
    setSaving(true);
    try {
      await updateUser(user.id, { ...user, enabled: !user.enabled });
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
        display_name: String(form.get("display_name") || "") || null,
        gender: String(form.get("gender") || "UNSPECIFIED") as SystemUser["gender"],
        email: String(form.get("email") || "") || null,
        phone: String(form.get("phone") || "") || null,
        remark: String(form.get("remark") || "") || null,
        organization_id: null,
        enabled: true,
      });
      setRefresh((value) => value + 1);
      setUserModal(null);
      setNotice("账号已创建。");
    } catch {
      setNotice("账号创建失败，请检查输入和权限后重试。");
    } finally { setSaving(false); }
  }

  async function updateSelectedUser(roleIds: string[], enabled: boolean, fields: Pick<SystemUser, "display_name" | "gender" | "email" | "phone" | "remark">) {
    if (!selectedUser || saving || !canWrite) return;
    setSaving(true);
    try {
      await updateUser(selectedUser.id, { ...selectedUser, ...fields, role_ids: roleIds, enabled });
      setUserModal(null);
      setRefresh((value) => value + 1);
      setNotice("账号信息已更新。");
    } catch {
      setNotice("账号更新失败，请检查权限或状态后重试。");
    } finally { setSaving(false); }
  }

  const roleName = (role: { code: string; name: string }) => ({ SYSTEM_ADMIN: "系统管理员", EQUIPMENT_ADMIN: "设备管理员", REPAIR_WORKER: "维修工", LINE_OPERATOR: "产线作业员" } as Record<string, string>)[role.code] ?? role.name;
  const roleItems = (roles.value ?? []).map((item) => ({ ...item, permission_codes: item.permission_codes ?? [], description: item.description ?? null, built_in: item.built_in ?? false, enabled: item.enabled ?? true, user_count: item.user_count ?? 0, updated_at: item.updated_at ?? "—" })).filter((item) => !roleQuery || [roleName(item), item.name, item.code].some((value) => value.toLowerCase().includes(roleQuery.toLowerCase())));
  const roleBoundCount = (roleId: string) => (roles.value ?? []).find((role) => role.id === roleId)?.user_count ?? 0;
  const isBuiltinRole = (role: SystemRole) => role.built_in;
  const userItems = (users.value ?? []).map((item) => ({ ...item, role_ids: item.role_ids ?? [], display_name: item.display_name ?? null, gender: item.gender ?? null, email: item.email ?? null, phone: item.phone ?? null, remark: item.remark ?? null, organization_id: item.organization_id ?? null })).filter((item) => (!userQuery || [item.username, item.display_name ?? ""].some((value) => value.toLowerCase().includes(userQuery.toLowerCase()))) && (!userRoleId || item.role_ids.includes(userRoleId)));
  const enabledUsers = (users.value ?? []).filter((item) => item.enabled).length;
  const selectedUser = (users.value ?? []).find((item) => item.id === selectedUserId);
  return <Page title="系统管理">
    <section className="system-overview" aria-label="系统管理概览"><div><p className="page-shell__eyebrow">● RBAC 权限中心</p><h3>系统角色、组织与用户统一维护</h3><p>角色负责菜单和按钮权限，用户绑定组织与授权角色。系统管理员为唯一内置角色，不允许删除；自定义角色删除前会校验是否被用户绑定。</p></div><div className="system-overview__stats"><span>角色总数<strong>{roles.value?.length ?? "—"}</strong></span><span>系统用户<strong>{users.value?.length ?? "—"}</strong></span><span>启用账号<strong>{users.value ? enabledUsers : "—"}</strong></span></div></section>
    {notice && <p role="status">{notice}</p>}
    <div className="section-tabs system-tabs" role="tablist" aria-label="系统管理分区">
      {[ ["roles", "角色管理"], ["users", "用户管理"], ["loginLogs", "登录日志"], ["operationLogs", "操作日志"] ].map(([id, label]) => <button key={id} type="button" role="tab" aria-selected={section === id} onClick={() => setSection(id as typeof section)}>{label}</button>)}
    </div>
    <section className="section-tab-panel system-tab-panel" role="tabpanel">
      {section === "roles" && <RolePanel roles={roles} items={roleItems} canWrite={canWrite} page={rolePage} onPageChange={setRolePage} onSearch={setRoleQuery} onCreate={() => setRoleModal("new")} onRefresh={() => setRefresh((value) => value + 1)} onEdit={(id) => { setEditingRoleId(id); setRoleModal("edit"); }} onDelete={(id) => void deleteRole(id).then(() => { setRefresh((value) => value + 1); setNotice("角色已删除。"); }).catch(() => setNotice("角色删除失败，已绑定用户的角色不能删除。"))} roleName={roleName} isBuiltin={isBuiltinRole} roleBoundCount={roleBoundCount} />}
      {section === "users" && <UserPanel users={users} roles={roles.value ?? []} items={userItems} canWrite={canWrite} saving={saving} page={userPage} query={userQuery} roleId={userRoleId} onSearch={(value) => { setUserQuery(value); setUserPage(1); }} onRoleFilter={(value) => { setUserRoleId(value); setUserPage(1); }} onPageChange={setUserPage} onRefresh={() => setRefresh((value) => value + 1)} onCreate={() => setUserModal("new")} onDetail={(id) => { setSelectedUserId(id); setUserModal("detail"); }} onEdit={(id) => { setSelectedUserId(id); setUserModal("edit"); }} onToggle={(item) => void toggle(item)} roleName={roleName} />}
      {section === "loginLogs" && <PrototypeAuditLogPanel kind="login" data={{ ...loginEvents, value: loginEvents.value ? { ...loginEvents.value, items: loginEvents.value.items.map((item) => ({ id: item.id, actor_user_id: item.username, actor_display_name: item.display_name, action: "login", resource_type: "login", resource_id: null, result: item.result, created_at: item.logged_at, summary: item.reason })) } : null }} page={loginPage} query={loginQuery} result={loginResult} range={loginRange} onQuery={(value) => { setLoginQuery(value); setLoginPage(1); }} onResult={(value) => { setLoginResult(value); setLoginPage(1); }} onRange={(value) => { setLoginRange(value); setLoginPage(1); }} onPageChange={setLoginPage} onRefresh={() => { setLoginQuery(""); setLoginResult(""); setLoginRange(""); setLoginPage(1); setRefresh((value) => value + 1); }} />}
      {section === "operationLogs" && <PrototypeAuditLogPanel kind="operation" data={audits} page={operationPage} query={operationQuery} module={operationModule} result={operationResult} onQuery={(value) => { setOperationQuery(value); setOperationPage(1); }} onModule={(value) => { setOperationModule(value); setOperationPage(1); }} onResult={(value) => { setOperationResult(value); setOperationPage(1); }} onPageChange={setOperationPage} onRefresh={() => { setOperationQuery(""); setOperationModule(""); setOperationResult(""); setOperationPage(1); setRefresh((value) => value + 1); }} />}
    </section>
    {roleModal && <RoleEditorModal mode={roleModal} role={roleModal === "edit" ? roleItems.find((item) => item.id === editingRoleId) ?? roleItems[0] : undefined} permissions={permissions.value ?? []} canWrite={canWrite} onClose={() => setRoleModal(null)} onSaved={() => { setRoleModal(null); setRefresh((value) => value + 1); setNotice(roleModal === "new" ? "角色已创建。" : "角色权限已更新。"); }} onFailed={() => setNotice("角色保存失败，请检查权限或名称后重试。")} />}
    {userModal && <UserModal mode={userModal} user={selectedUser} roles={roles.value ?? []} canWrite={canWrite} saving={saving} roleName={roleName} onClose={() => setUserModal(null)} onCreate={create} onUpdate={(roleIds, enabled, fields) => void updateSelectedUser(roleIds, enabled, fields)} />}
  </Page>;
}

const PAGE_SIZE = 10;

function PrototypePager({ count, page, onPageChange }: { count: number; page: number; onPageChange: React.Dispatch<React.SetStateAction<number>> }) {
  const total = Math.max(1, Math.ceil(count / PAGE_SIZE));
  return <div className="pagination-bar"><span>共 {count} 条</span><div className="pagination-actions"><button type="button" className="button-secondary" disabled={page <= 1} onClick={() => onPageChange((value) => Math.max(1, value - 1))}>上一页</button><span>{page} / {total}</span><button type="button" className="button-secondary" disabled={page >= total} onClick={() => onPageChange((value) => Math.min(total, value + 1))}>下一页</button></div></div>;
}

function RolePanel({ roles, items, canWrite, page, onPageChange, onSearch, onCreate, onRefresh, onEdit, onDelete, roleName, isBuiltin, roleBoundCount }: { roles: LoadState<SystemRole[]>; items: SystemRole[]; canWrite: boolean; page: number; onPageChange: React.Dispatch<React.SetStateAction<number>>; onSearch: (value: string) => void; onCreate: () => void; onRefresh: () => void; onEdit: (id: string) => void; onDelete: (id: string) => void; roleName: (role: { code: string; name: string }) => string; isBuiltin: (role: SystemRole) => boolean; roleBoundCount: (id: string) => number }) {
  const rows = items.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  return <><div className="system-toolbar"><div className="system-toolbar-left"><label className="system-search">⌕<input aria-label="搜索角色名称" placeholder="搜索角色名称" onChange={(event) => onSearch(event.target.value)} /></label><span className="system-tag blue">内置角色仅系统管理员</span><span className="system-tag">自定义角色可自由新增</span></div><div className="system-toolbar-actions"><button type="button" className="button-primary" disabled={!canWrite} title={!canWrite ? "当前账号没有身份写入权限" : undefined} onClick={onCreate}>新增角色</button><button type="button" className="button-secondary" onClick={onRefresh}>刷新</button></div></div><article className="system-table-card"><div className="system-table-head"><div><h3>角色列表</h3><p>支持按角色名称搜索；已绑定用户的自定义角色不可删除。</p></div><span className="status-chip status-chip--success">{items.length} 个角色</span></div><State state={roles} empty={(value) => !value.length}>{() => <><div className="system-table-wrap"><table className="system-table"><thead><tr><th>角色名称</th><th>角色类型</th><th>状态</th><th>绑定用户</th><th>更新时间</th><th>操作</th></tr></thead><tbody>{rows.map((role) => { const builtin = isBuiltin(role); const bound = roleBoundCount(role.id); return <tr key={role.id}><td><strong>{roleName(role)}</strong><small>{builtin ? "内置最高权限角色，禁止删除。" : "自定义角色"}</small></td><td><span className={`system-role-type ${builtin ? "is-builtin" : ""}`}>{builtin ? "内置角色" : "自定义角色"}</span></td><td><span className={role.enabled ? "system-status-enabled" : "system-tag red"}>{role.enabled ? "启用" : "禁用"}</span></td><td><span className="system-bound-count">{bound} 人</span></td><td>{role.updated_at}</td><td><div className="system-link-actions">{canWrite ? <button type="button" className="system-text-action" onClick={() => onEdit(role.id)}>编辑权限</button> : <span>只读</span>}<button type="button" className="system-text-action danger" disabled={!canWrite || builtin || Boolean(bound)} title={builtin ? "内置角色禁止删除" : bound ? "已绑定用户的角色不可删除" : undefined} onClick={() => onDelete(role.id)}>删除</button></div></td></tr>; })}</tbody></table></div><PrototypePager count={items.length} page={page} onPageChange={onPageChange} /></>}</State></article></>;
}

function UserPanel({ users, roles, items, canWrite, saving, page, query, roleId, onSearch, onRoleFilter, onPageChange, onRefresh, onCreate, onDetail, onEdit, onToggle, roleName }: { users: LoadState<SystemUser[]>; roles: SystemRole[]; items: SystemUser[]; canWrite: boolean; saving: boolean; page: number; query: string; roleId: string; onSearch: (value: string) => void; onRoleFilter: (value: string) => void; onPageChange: React.Dispatch<React.SetStateAction<number>>; onRefresh: () => void; onCreate: () => void; onDetail: (id: string) => void; onEdit: (id: string) => void; onToggle: (item: SystemUser) => void; roleName: (role: { code: string; name: string }) => string }) {
  const rows = items.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  const names = new Map(roles.map((role) => [role.id, roleName(role)]));
  return <div className="system-users-layout"><aside className="system-org-boundary"><div className="org-panel-head"><div><h3>组织树</h3><p>选中节点后可按组织查看用户。</p></div></div><div className="system-toolbar-actions"><button type="button" className="button-primary" disabled title="当前身份管理接口未提供组织维护">新增组织</button><button type="button" className="button-secondary" disabled title="当前身份管理接口未提供组织维护">删除组织</button></div><p className="empty-panel">当前接口未提供用户组织关联，不能按组织筛选。</p></aside><section className="system-users-panel"><div className="system-toolbar"><div className="system-toolbar-left"><label className="system-search">⌕<input aria-label="搜索用户名" value={query} onChange={(event) => onSearch(event.target.value)} placeholder="搜索用户名、姓名" /></label><select className="system-filter-select" aria-label="按授权角色筛选" value={roleId} onChange={(event) => onRoleFilter(event.target.value)}><option value="">全部授权角色</option>{roles.map((role) => <option key={role.id} value={role.id}>{roleName(role)}</option>)}</select><span className="system-tag blue">当前组织：全部组织</span></div><div className="system-toolbar-actions"><button type="button" className="button-primary" disabled={!canWrite} onClick={onCreate}>新增用户</button><button type="button" className="button-secondary" onClick={onRefresh}>刷新</button></div></div><article className="system-table-card"><div className="system-table-head"><div><h3>用户列表</h3><p>用户名全局唯一；编辑时用户名不可修改。姓名、手机号和组织需接口支持后才可维护。</p></div><span className="status-chip status-chip--success">{items.length} 个用户</span></div><State state={users} empty={(value) => !value.length}>{() => <><div className="system-table-wrap"><table className="system-table"><thead><tr><th>用户名</th><th>姓名</th><th>手机号</th><th>账号状态</th><th>授权角色</th><th>所属组织</th><th>操作</th></tr></thead><tbody>{rows.map((item) => <tr key={item.id}><td><strong>{item.username}</strong></td><td>当前接口未提供</td><td>当前接口未提供</td><td><span className={item.enabled ? "system-status-enabled" : "system-tag red"}>{item.enabled ? "启用" : "禁用"}</span></td><td><div className="tag-row">{item.role_ids.length ? item.role_ids.map((id) => <span className="system-tag blue" key={id}>{names.get(id) ?? "未命名角色"}</span>) : "未授权"}</div></td><td>当前接口未提供</td><td><div className="system-link-actions"><button type="button" className="system-text-action" onClick={() => onDetail(item.id)}>详情</button><button type="button" className="system-text-action" disabled={!canWrite || saving} onClick={() => onToggle(item)}>{item.enabled ? "禁用" : "启用"}</button><button type="button" className="system-text-action" disabled title="当前公开 API 未提供重置密码">重置密码</button><button type="button" className="system-text-action" disabled={!canWrite} onClick={() => onEdit(item.id)}>编辑</button><button type="button" className="system-text-action danger" disabled title="当前公开 API 未提供删除用户">删除</button></div></td></tr>)}</tbody></table></div><PrototypePager count={items.length} page={page} onPageChange={onPageChange} /></>}</State></article></section></div>;
}

function UserModal({ mode, user, roles, canWrite, saving, roleName, onClose, onCreate, onUpdate }: { mode: "new" | "edit" | "detail"; user?: SystemUser; roles: SystemRole[]; canWrite: boolean; saving: boolean; roleName: (role: { code: string; name: string }) => string; onClose: () => void; onCreate: (event: FormEvent<HTMLFormElement>) => Promise<void>; onUpdate: (roleIds: string[], enabled: boolean, fields: Pick<SystemUser, "display_name" | "gender" | "email" | "phone" | "remark">) => void }) {
  const [roleId, setRoleId] = useState(user?.role_ids[0] ?? roles[0]?.id ?? "");
  const [enabled, setEnabled] = useState(user?.enabled ?? true);
  const detail = mode === "detail";
  function submit(event: FormEvent<HTMLFormElement>) {
    if (mode === "new") { void onCreate(event); return; }
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    onUpdate(roleId ? [roleId] : [], enabled, {
      display_name: String(form.get("display_name") || "") || null,
      gender: String(form.get("gender") || "UNSPECIFIED") as SystemUser["gender"],
      email: String(form.get("email") || "") || null,
      phone: String(form.get("phone") || "") || null,
      remark: String(form.get("remark") || "") || null,
    });
  }
  const locked = detail || !canWrite;
  return <div className="system-modal-layer" role="presentation"><div className="system-modal-scrim" onClick={onClose} /><section className="system-user-modal" role="dialog" aria-modal="true" aria-label={mode === "new" ? "新增用户" : mode === "edit" ? "编辑用户" : "用户详情"}><header className="system-role-modal__head"><div><h3>{mode === "new" ? "新增用户" : mode === "edit" ? "编辑用户" : "用户详情"}</h3><p>{detail ? "展示账号完整资料与授权信息。" : "用户名全局唯一；编辑用户时用户名保持只读。"}</p></div><button type="button" className="icon-button" aria-label="关闭用户弹窗" onClick={onClose}>×</button></header><form className="system-user-form" onSubmit={submit}><div className="form-grid-3"><label>用户名 <span className="required-mark">*</span><input aria-label="用户名" name="username" defaultValue={user?.username ?? ""} readOnly={mode === "edit" || detail} required disabled={detail} placeholder="例如：zhangsan" /></label><label>初始密码 <span className="required-mark">*</span><input aria-label="初始密码" name="password" type="password" minLength={8} required={mode === "new"} disabled={mode !== "new" || detail} placeholder="至少 8 位" /></label><label>姓名<input aria-label="姓名" name="display_name" defaultValue={user?.display_name ?? ""} disabled={locked} /></label><label>性别<select aria-label="性别" name="gender" defaultValue={user?.gender ?? "UNSPECIFIED"} disabled={locked}><option value="UNSPECIFIED">未说明</option><option value="MALE">男</option><option value="FEMALE">女</option></select></label><label>邮箱<input aria-label="邮箱" name="email" type="email" defaultValue={user?.email ?? ""} disabled={locked} /></label><label>手机号<input aria-label="手机号" name="phone" defaultValue={user?.phone ?? ""} disabled={locked} /></label><label>账号状态 <span className="required-mark">*</span><select aria-label="账号状态" value={enabled ? "enabled" : "disabled"} disabled={locked} onChange={(event) => setEnabled(event.target.value === "enabled")}><option value="enabled">启用</option><option value="disabled">禁用</option></select></label><label className="form-field--wide">授权角色 <span className="required-mark">*</span><select aria-label="授权角色" name="role_id" value={roleId} disabled={locked} onChange={(event) => setRoleId(event.target.value)}>{roles.map((role) => <option key={role.id} value={role.id}>{roleName(role)}</option>)}</select></label><label className="form-field--wide">备注<textarea name="remark" defaultValue={user?.remark ?? ""} disabled={locked} /></label></div><footer className="system-role-modal__foot"><button type="button" className="button-secondary" onClick={onClose}>{detail ? "关闭" : "取消"}</button>{!detail && <button type="submit" className="button-primary" disabled={!canWrite || saving}>{saving ? "保存中…" : "保存用户"}</button>}</footer></form></section></div>;
}

function PrototypeAuditLogPanel({ kind, data, page, query, result, range, module, onQuery, onResult, onRange, onModule, onPageChange, onRefresh }: { kind: "login" | "operation"; data: LoadState<{ items: AuditEvent[]; count: number; page: number; page_size: number }>; page: number; query: string; result: string; range?: string; module?: string; onQuery: (value: string) => void; onResult: (value: string) => void; onRange?: (value: string) => void; onModule?: (value: string) => void; onPageChange: React.Dispatch<React.SetStateAction<number>>; onRefresh: () => void }) {
  const login = kind === "login";
  const title = login ? "登录日志" : "操作日志";
  const source = data.value?.items ?? [];
  const items = source.filter((item) => { const loginMatch = !login || item.action.toLowerCase().includes("login"); const searchable = [item.actor_user_id, item.actor_display_name, item.action, item.resource_type, item.resource_id, item.result].filter(Boolean).join(" ").toLowerCase().includes(query.toLowerCase()); const resultMatch = !result || item.result.toLowerCase() === result; const moduleMatch = login || !module || item.resource_type === module; return loginMatch && searchable && resultMatch && moduleMatch; });
  const rows = items.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  return <><div className="system-toolbar"><div className="system-toolbar-left"><label className="system-search">⌕<input aria-label={`${title}搜索`} value={query} onChange={(event) => onQuery(event.target.value)} placeholder={login ? "搜索用户名、姓名、IP" : "搜索操作人、模块、对象"} /></label>{login ? <><select className="system-filter-select log-filter-select" aria-label="按登录结果筛选" value={result} onChange={(event) => onResult(event.target.value)}><option value="">全部结果</option><option value="success">成功</option><option value="failure">失败</option></select><select className="system-filter-select log-filter-select" aria-label="按时间范围筛选" value={range} disabled title="时间范围筛选由页面本地处理" onChange={(event) => onRange?.(event.target.value)}><option value="">全部时间</option><option value="today">今天</option><option value="week">近 7 天</option></select></> : <><select className="system-filter-select log-filter-select" aria-label="按模块筛选" value={module} onChange={(event) => onModule?.(event.target.value)}><option value="">全部模块</option>{[...new Set(source.map((item) => item.resource_type))].map((value) => <option key={value} value={value}>{value}</option>)}</select><select className="system-filter-select log-filter-select" aria-label="按操作结果筛选" value={result} onChange={(event) => onResult(event.target.value)}><option value="">全部结果</option><option value="success">成功</option><option value="failure">失败</option></select></>}</div><div className="system-toolbar-actions"><button type="button" className="button-secondary" onClick={onRefresh}>刷新</button></div></div><article className="system-table-card"><div className="system-table-head"><div><h3>{title}</h3><p>{login ? "记录账号登录时间、来源和登录结果。" : "记录角色、用户、组织等配置变更动作。"}</p></div><span className="status-chip status-chip--success">{items.length} 条记录</span></div><State state={data}>{() => <><div className="system-table-wrap"><table className="system-table log-table"><thead>{login ? <tr><th>登录账号</th><th>姓名</th><th>登录时间</th><th>来源 IP</th><th>登录终端</th><th>结果</th><th>说明</th></tr> : <tr><th>操作时间</th><th>操作人</th><th>模块</th><th>操作类型</th><th>操作对象</th><th>结果</th><th>说明</th></tr>}</thead><tbody>{rows.length ? rows.map((item) => login ? <tr key={item.id}><td>{item.actor_user_id ?? "系统"}</td><td>{item.actor_display_name ?? "—"}</td><td>{item.created_at}</td><td>—</td><td>—</td><td><span className={item.result === "success" ? "system-status-enabled" : "system-tag red"}>{item.result === "success" ? "成功" : "失败"}</span></td><td>{item.summary ?? "—"}</td></tr> : <tr key={item.id}><td>{item.created_at}</td><td>{item.actor_display_name ?? item.actor_user_id ?? "系统"}</td><td><span className="system-tag blue">{item.resource_type}</span></td><td>{item.action}</td><td>{item.resource_id ?? "—"}</td><td><span className={item.result === "success" ? "system-status-enabled" : "system-tag red"}>{item.result === "success" ? "成功" : "失败"}</span></td><td>{item.summary ?? "—"}</td></tr>) : <tr><td colSpan={7}>暂无符合条件的正式{title}。</td></tr>}</tbody></table></div><PrototypePager count={items.length} page={page} onPageChange={onPageChange} /></>}</State></article></>;
}

function RoleEditorModal({ mode, role, permissions, canWrite, onClose, onSaved, onFailed }: { mode: "new" | "edit"; role?: SystemRole; permissions: Array<{ code: string }>; canWrite: boolean; onClose: () => void; onSaved: () => void; onFailed: () => void }) {
  const [name, setName] = useState(role?.name ?? "");
  const [selected, setSelected] = useState(role?.permission_codes ?? []);
  const [expanded, setExpanded] = useState(true);
  const [saving, setSaving] = useState(false);
  const permissionLabel = (code: string) => ({ workbench: "工作台", bi: "驾驶舱 BI", factory: "工厂建模", organization: "工厂建模", equipment: "设备台账", fault: "故障上报", maintenance: "维修记录", system: "系统管理", identity: "系统管理", intelligence: "智能配置", user_management: "用户管理", "workbench:view": "查看工作台", "workbench:export": "导出工作台数据", "bi:view": "查看驾驶舱", "bi:export": "导出 BI 记录", "factory:view": "查看工厂建模", "factory:manage": "维护工厂建模", "organization:read": "查看组织", "organization:write": "维护组织", "equipment:read": "查看设备", "equipment:write": "维护设备", "equipment:view": "查看设备", "equipment:create": "新增设备", "equipment:edit": "编辑设备", "equipment:update": "编辑设备", "equipment:delete": "删除设备", "fault:view": "查看故障", "fault:create": "提交故障", "fault:repair": "执行维修", "fault:close": "关闭故障", "maintenance:view": "查看维修记录", "maintenance:detail": "查看维修详情", "maintenance:export": "导出维修记录", "system:role": "角色管理", "system:user": "用户管理", "system:org": "组织管理", "system:audit": "查看操作日志", "user_management.view_all": "查看全部用户", "identity:read": "查看系统管理", "identity:write": "维护用户和角色", "intelligence:view": "查看智能配置", "intelligence:model": "管理模型", "intelligence:agent": "使用智能助手", "intelligence:knowledge": "维护知识库", "intelligence:audit": "查看智能审计" } as Record<string, string>)[code] ?? "未命名权限";
  const permissionItems = Array.isArray(permissions) ? permissions : [];
  const groups = new Map<string, Array<{ code: string }>>();
  permissionItems.forEach((permission) => { const [group] = permission.code.split(":"); groups.set(group, [...(groups.get(group) ?? []), permission]); });
  async function save() {
    if (saving || !canWrite) return;
    if (!name.trim() || !selected.length) return;
    setSaving(true);
    try {
      if (mode === "new") {
        const readableCode = name.trim().toUpperCase().replace(/[^A-Z0-9]+/g, "_").replace(/^_+|_+$/g, "");
        const code = readableCode || `CUSTOM_${crypto.randomUUID().replaceAll("-", "").toUpperCase()}`;
        await createRole({ code, name: name.trim(), description: null, enabled: true, permission_codes: selected });
      } else {
        await updateRole(role!.id, { code: role!.code, name: name.trim(), description: role!.description, enabled: role!.enabled, permission_codes: selected });
      }
      onSaved();
    } catch { onFailed(); } finally { setSaving(false); }
  }
  return <div className="system-modal-layer" role="presentation"><div className="system-modal-scrim" onClick={onClose} /><section className="system-role-modal" role="dialog" aria-modal="true" aria-labelledby="role-editor-title"><header className="system-role-modal__head"><div><h3 id="role-editor-title">{mode === "new" ? "新增角色" : "编辑角色权限"}</h3><p>先定义角色基础信息，再配置菜单与按钮权限；保存后立即更新角色列表。</p></div><button type="button" className="icon-button" aria-label="关闭角色弹窗" onClick={onClose}>×</button></header><div className="system-role-modal__body"><section className="role-editor-card"><div className="role-editor-card-head"><div><h4>角色基础信息</h4><p>用于角色列表展示、状态管控和后续用户授权。</p></div><span className="role-editor-index">01</span></div><label>角色名称 <span className="required-mark">*</span><input value={name} onChange={(event) => setName(event.target.value)} placeholder="例如：生产调度员" /></label><label>角色类型<input className="readonly-input" value="自定义角色" readOnly /></label><label>角色状态<select defaultValue="启用"><option>启用</option><option>禁用</option></select></label><label>角色说明<textarea placeholder="描述该角色的职责边界" /></label><div className="role-save-note"><strong>配置规则</strong><span>系统管理员为内置角色；被用户绑定的角色不可直接禁用或删除。</span></div></section><section className="role-editor-card role-permission-card"><div className="role-editor-card-head"><div><h4>权限配置</h4><p>树结构包含菜单权限与按钮权限，支持展开、折叠、全选和父子联动。</p></div><span className="role-editor-index">02</span></div><label>权限选择 <span className="required-mark">*</span></label><div className="permission-tree"><div className="permission-tree__toolbar"><strong>菜单权限</strong><label><input type="checkbox" checked={expanded} onChange={(event) => setExpanded(event.target.checked)} /> 展开/折叠</label><label><input type="checkbox" checked={selected.length === permissionItems.length && permissionItems.length > 0} onChange={(event) => setSelected(event.target.checked ? permissionItems.map((item) => item.code) : [])} /> 全选/全不选</label><label><input type="checkbox" checked disabled /> 父子联动</label></div><div className="permission-tree__scroll">{expanded && [...groups.entries()].map(([group, items]) => <div className="permission-tree__group" key={group}><label className="permission-tree__parent"><span>⌄</span><input type="checkbox" checked={items.every((item) => selected.includes(item.code))} onChange={(event) => setSelected((current) => event.target.checked ? [...new Set([...current, ...items.map((item) => item.code)])] : current.filter((code) => !items.some((item) => item.code === code)))} />{permissionLabel(group)}</label>{items.map((item) => <label className="permission-tree__item" key={item.code}><input type="checkbox" aria-label={item.code} checked={selected.includes(item.code)} onChange={(event) => setSelected((current) => event.target.checked ? [...current, item.code] : current.filter((code) => code !== item.code))} />{permissionLabel(item.code)}</label>)}</div>)}</div></div></section></div><footer className="system-role-modal__foot"><button type="button" className="button-secondary" onClick={onClose}>取消</button><button type="button" className="button-primary" disabled={!canWrite || saving} onClick={() => void save()}>{saving ? "保存中…" : mode === "edit" ? "保存角色权限" : "保存角色"}</button></footer></section></div>;
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

  return <Page title="工厂建模"><p className="page-description">维护工厂、车间和产线层级；所有组织事实来自正式组织 API。</p>{notice && <p role="status">{notice}</p>}{!canWrite && <p role="status">当前账号只有组织读取权限，不能修改组织结构。</p>}<State state={state} empty={(items) => !items.length}>{(items) => {
    const organizations = items as OrganizationItem[];
    const selected = organizations.find((item) => item.id === selectedId) ?? organizations[0];
    if (!selected) return null;
    const children = organizations.filter((item) => item.parent_id === selected.id);
    const childType = selected.type === "ROOT" ? "FACTORY" : selected.type === "FACTORY" ? "WORKSHOP" : "LINE";
    const canAddChild = canWrite && selected.type !== "LINE";
    return <div className="factory-workspace"><aside className="factory-tree-panel"><div className="panel-heading"><div><h3>组织结构树</h3><p>按编码或名称定位节点</p></div><span className="status-chip status-chip--neutral">{organizations.length} 个节点</span></div><label className="search-field">搜索组织<input aria-label="搜索组织" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索编码 / 名称" /></label><OrganizationTree items={organizations} query={query} collapsed={collapsed} selectedId={selected.id} onSelect={setSelectedId} onToggle={(id) => setCollapsed((current) => current.includes(id) ? current.filter((value) => value !== id) : [...current, id])} /></aside><section className="factory-detail-panel"><header className="panel-heading"><div><h3>{creating ? "新增下级节点" : editing ? "编辑组织节点" : "节点详情"}</h3><p>{creating ? `父节点：${selected.name}` : editing ? `正在编辑：${editing.name}` : `${selected.type} · ${selected.code}`}</p></div>{!creating && !editing && <div className="context-actions">{canAddChild && <button type="button" className="button-primary" onClick={() => setCreating(true)}>新增下级节点</button>}{canWrite && selected.type !== "ROOT" && <button type="button" className="button-secondary" onClick={() => setEditing(selected)}>编辑</button>}</div>}</header>{creating ? <form className="portal-form" onSubmit={(event) => void submit(event, selected)}><fieldset disabled={!canWrite || saving}><label>类型<select name="type" defaultValue={childType}><option value={childType}>{childType}</option></select></label><label>编码<input name="code" required /></label><label>名称<input name="name" required /></label><label>排序<input name="sort_order" type="number" min="0" defaultValue="0" /></label><label className="form-field--wide">备注<input name="remark" /></label><div className="form-actions"><button type="button" className="button-secondary" onClick={() => setCreating(false)}>取消</button><button type="submit" className="button-primary">{saving ? "创建中…" : "创建节点"}</button></div></fieldset></form> : editing ? <form className="portal-form" onSubmit={saveEdit}><fieldset disabled={!canWrite || saving}><label>编码<input name="code" required defaultValue={editing.code} /></label><label>名称<input name="name" required defaultValue={editing.name} /></label><label>排序<input name="sort_order" type="number" min="0" defaultValue={editing.sort_order ?? 0} /></label><label>备注<input name="remark" defaultValue={editing.remark ?? ""} /></label><div className="form-actions"><button type="button" className="button-secondary" onClick={() => setEditing(null)}>取消</button><button type="submit" className="button-primary">{saving ? "保存中…" : "保存组织"}</button></div></fieldset></form> : <><div className="factory-summary"><article><span>组织名称</span><strong>{selected.name}</strong></article><article><span>组织编码</span><strong>{selected.code}</strong></article><article><span>当前状态</span><strong className={selected.enabled ? "status-chip status-chip--success" : "status-chip status-chip--muted"}>{selected.enabled ? "启用" : "停用"}</strong></article><article><span>下级节点</span><strong>{children.length} 个</strong></article></div><section className="detail-note"><h4>备注</h4><p>{selected.remark || "暂无备注。"}</p></section><section className="child-table"><header><h4>下级节点</h4><span>{children.length} 个</span></header>{children.length ? <table><thead><tr><th>编码</th><th>名称</th><th>类型</th><th>状态</th></tr></thead><tbody>{children.map((item) => <tr key={item.id}><td>{item.code}</td><td><button type="button" className="link-button" onClick={() => setSelectedId(item.id)}>{item.name}</button></td><td>{item.type}</td><td><span className={item.enabled ? "status-chip status-chip--success" : "status-chip status-chip--muted"}>{item.enabled ? "启用" : "停用"}</span></td></tr>)}</tbody></table> : <p className="empty-panel">当前节点暂无下级节点。</p>}</section>{canWrite && selected.type !== "ROOT" && <div className="danger-actions"><button type="button" className="button-secondary" onClick={() => void toggle(selected)}>{selected.enabled ? "停用" : "启用"}</button><button type="button" className="button-danger" onClick={() => void remove(selected)}>删除节点</button></div>}</>}</section></div>;
  }}</State></Page>;
}

function OrganizationTree({ items, query, collapsed, selectedId, onSelect, onToggle }: { items: OrganizationItem[]; query: string; collapsed: string[]; selectedId: string; onSelect: (id: string) => void; onToggle: (id: string) => void }) {
  const byParent = new Map<string | null, OrganizationItem[]>();
  for (const item of items) byParent.set(item.parent_id, [...(byParent.get(item.parent_id) ?? []), item]);
  const matches = (item: OrganizationItem): boolean => !query || item.name.includes(query) || item.code.includes(query) || (byParent.get(item.id) ?? []).some(matches);
  const rows: Array<{ item: OrganizationItem; depth: number }> = [];
  const visited = new Set<string>();
  const organizationIds = new Set(items.map((item) => item.id));
  function visit(parentId: string | null, depth: number) { for (const item of byParent.get(parentId) ?? []) { if (visited.has(item.id) || !matches(item)) continue; visited.add(item.id); rows.push({ item, depth }); if (!collapsed.includes(item.id) || query) visit(item.id, depth + 1); } }
  visit(null, 0);
  for (const item of items) if (!visited.has(item.id) && matches(item) && (item.parent_id === null || !organizationIds.has(item.parent_id))) { visited.add(item.id); rows.push({ item, depth: 0 }); }
  const expandableIds = items.filter((item) => (byParent.get(item.id) ?? []).length > 0).map((item) => item.id);
  function expandAll() { for (const id of collapsed) onToggle(id); }
  function collapseAll() { for (const id of expandableIds) if (!collapsed.includes(id)) onToggle(id); }
  return <>
    <div className="factory-tree-tools__actions" aria-label="组织树操作">
      <button type="button" className="button-secondary" onClick={expandAll}>全部展开</button>
      <button type="button" className="button-secondary" onClick={collapseAll}>全部折叠</button>
    </div>
    <div className="organization-tree" role="tree" aria-label="组织结构树">{rows.map(({ item, depth }) => { const hasChildren = (byParent.get(item.id) ?? []).length > 0; const expanded = !collapsed.includes(item.id); return <div className={`organization-tree__row ${selectedId === item.id ? "is-selected" : ""}`} key={item.id} style={{ paddingLeft: `${12 + depth * 18}px` }}><button type="button" className="tree-toggle" aria-label={`${expanded ? "收起" : "展开"} ${item.name}`} disabled={!hasChildren} onClick={() => onToggle(item.id)}>{hasChildren ? (expanded ? "−" : "+") : "·"}</button><button type="button" className="tree-node" onClick={() => onSelect(item.id)}><span>{item.name}</span><small>{item.code}</small></button><span className={item.enabled ? "status-chip status-chip--success" : "status-chip status-chip--muted"}>{item.enabled ? "启用" : "停用"}</span></div>; })}</div>
  </>;
}
export function AgentReportPage({ currentUsername = "当前登录用户" }: { currentUsername?: string } = {}) {
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

  const missingFields = [
    !equipmentId && "设备",
    !symptom && "故障现象",
    !occurredAt && "发生时间",
    durationMinutes <= 0 && "持续时长",
  ].filter(Boolean) as string[];
  const completedFields = 4 - missingFields.length;
  const completion = Math.round(completedFields / 4 * 100);
  return <Page title="AI 故障上报">
    <p className="page-description">AI 只负责受控收集；它不会直接写入故障事实。正式上报必须由用户完成结构化确认。</p>
    <div className="agent-statusbar" aria-label="Agent 上报状态"><span className="status-chip status-chip--success">权限已识别</span><span className={`status-chip ${collecting ? "status-chip--neutral" : "status-chip--success"}`}>{collecting ? "Agent 正在收集" : "Agent 服务在线"}</span><span className="status-chip status-chip--neutral">阶段：{collected ? "补齐必填项" : "等待开始"}</span></div>
    <div className="agent-report-workspace"><section className="agent-report-workspace__collect agent-chat-panel"><header className="section-title"><div><h3>对话主区域</h3><h4 className="agent-section-label">AI 受控收集</h4></div><span className={`status-chip ${missingFields.length ? "status-chip--warning" : "status-chip--success"}`}>{missingFields.length ? `缺 ${missingFields.length} 项` : "已补齐"}</span></header><div className="agent-chat-flow" aria-label="AI 上报对话">
      <p className="agent-bubble">请描述故障现象，我会先校验设备权限，再整理为结构化上报单。</p>
      {symptom && <p className="agent-bubble agent-bubble--user">{symptom}</p>}
      <p className="agent-bubble">{missingFields.length ? `还缺少${missingFields.join("、")}；可继续补充或上传现场附件。` : "必填字段已补齐，请核对右侧结构化摘要并正式确认。"}</p>
      {runtimeEvents.map((item, index) => <p className="agent-bubble" key={`${item.event}-${index}`}>运行状态：{String(item.data.status ?? item.event)}</p>)}
    </div><form className="agent-input-row" onSubmit={collect}>
      <fieldset disabled={collecting || submitting}><button type="button" className="button-secondary" onClick={() => document.getElementById("agent-natural-language-input")?.focus()}>继续补充</button><button type="button" className="button-secondary" onClick={() => document.getElementById("agent-attachment-input")?.click()}>附件</button><input id="agent-attachment-input" className="visually-hidden" aria-label="AI 故障附件" type="file" disabled={uploading} onChange={(event) => void addAttachment(event.target.files?.[0])} /><label className="agent-device-input">设备 ID<input aria-label="设备 ID" value={equipmentId} onChange={(event) => setEquipmentId(event.target.value)} required /></label><label className="agent-natural-input"><span className="visually-hidden">故障描述</span><input id="agent-natural-language-input" aria-label="自然语言输入" placeholder="补充发生时间、工况、持续时间或现场现象" value={symptom} onChange={(event) => setSymptom(event.target.value)} required /></label><button type="submit" className="button-primary" aria-label={collecting ? "AI 收集中…" : "开始 AI 收集"}>{collecting ? "发送中…" : "发送"}</button></fieldset>
    </form></section><aside className="agent-report-workspace__notice agent-summary-panel"><header className="section-title"><h3>结构化上报摘要</h3><span className={`status-chip ${missingFields.length ? "status-chip--warning" : "status-chip--success"}`}>{missingFields.length ? "未完成" : "可确认"}</span></header><div className="summary-box"><div><strong>当前用户</strong><br />{currentUsername}</div><div><strong>授权设备</strong><br />由服务端按当前账号权限校验</div><div><strong>已选设备</strong><br />{equipmentId || "尚未填写"}</div><div><strong>必填完成度</strong><div className="progress" aria-label={`必填完成度 ${completion}%`}><span style={{ width: `${completion}%` }} /></div><small>{completedFields}/4 项</small></div><div><strong>故障摘要</strong><br />{symptom || "尚未填写故障现象"}</div><div><strong>提交状态</strong><br />{missingFields.length ? <><span>缺少{missingFields.join("、")}</span><small>正式提交暂不可用。</small></> : "字段已齐全，等待人工确认。"}</div></div><div className="drawer-actions"><Link className="button-secondary" to="/fault-report">转人工表单</Link><button type="submit" className="button-primary" form="agent-confirmation-form" aria-label="确认并提交正式故障单" disabled={submitting || uploading || !collected || missingFields.length > 0}>{submitting ? "提交中…" : "提交故障单"}</button></div></aside></div>
    {collected && <section className="agent-confirmation-panel"><h3>正式字段确认</h3><form id="agent-confirmation-form" className="portal-form" onSubmit={confirm}><label>紧急程度<select value={urgency} onChange={(event) => setUrgency(event.target.value)}><option>HIGH</option><option>MEDIUM</option><option>LOW</option></select></label><label>发生时间<input aria-label="发生时间" type="datetime-local" value={occurredAt} onChange={(event) => setOccurredAt(event.target.value)} required /></label><label>持续时间（分钟）<input aria-label="持续时间（分钟）" type="number" min="0" value={durationMinutes} onChange={(event) => setDurationMinutes(Number(event.target.value))} /></label><label>补充说明<textarea value={description} onChange={(event) => setDescription(event.target.value)} /></label>{uploading && <p role="status">附件正在上传并进行安全检查…</p>}{attachments.length > 0 && <ul aria-label="AI 草稿附件">{attachments.map((item) => <li key={item.object_key}>{item.filename}</li>)}</ul>}</form></section>}
    {error && <p role="alert">{error}</p>}{notice && <p role="status">{notice}</p>}<p><Link to="/fault-report">转到人工故障上报</Link></p>
  </Page>;
}
