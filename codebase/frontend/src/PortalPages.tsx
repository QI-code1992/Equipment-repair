import { FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ApiError, AuditEvent, BiDashboard, Equipment, MaintenanceRecord, WorkOrder, getAuditEvents, getBiDashboard, getEquipment, getEquipmentDetail, getEquipmentHistory, getIntelligenceUsage, getKnowledgeDocuments, getMaintenanceRecords, getWorkOrders, requestJson } from "./api";

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
  return <section className="portal-page"><header><p className="page-shell__eyebrow">正式业务数据</p><h2>{title}</h2></header>{children}</section>;
}

function State<T>({ state, children, empty }: { state: LoadState<T>; children: (value: T) => React.ReactNode; empty?: (value: T) => boolean }) {
  if (state.loading) return <p role="status">正在加载…</p>;
  if (state.error) return <p role="alert">请求失败：{state.error}</p>;
  if (state.value !== null && empty?.(state.value)) return <p role="status">暂无可展示的正式业务数据。</p>;
  return state.value !== null ? <>{children(state.value)}</> : null;
}

export function BiDashboardPage() {
  const state = useData<BiDashboard>(getBiDashboard, []);
  return <Page title="驾驶舱 BI"><State state={state}>{(value) => <div className="data-grid"><div className="metric"><b>{value.summary.fault_count}</b><span>故障总数</span></div><div className="metric"><b>{value.summary.active_fault_count}</b><span>活动故障</span></div><div className="metric"><b>{value.summary.completed_work_order_count}</b><span>完成工单</span></div><div className="metric"><b>{Math.round(value.summary.completion_rate * 100)}%</b><span>完成率</span></div><section className="data-card"><h3>近 7 日趋势</h3><ul>{value.trend.map((item) => <li key={item.date}>{item.date}：故障 {item.fault_count}，完成 {item.completed_work_order_count}</li>)}</ul></section><section className="data-card"><h3>组织故障排行</h3>{value.organization_ranking.length ? <ol>{value.organization_ranking.map((item) => <li key={item.organization_id}>{item.organization_name}：{item.fault_count}</li>)}</ol> : <p>暂无排行数据。</p>}</section></div>}</State></Page>;
}

export function EquipmentLedgerPage() {
  const state = useData<Equipment[]>(getEquipment, []);
  return <Page title="设备台账"><p><Link to="/equipment/new">新增设备</Link></p><State state={state} empty={(items) => !items.length}>{(items) => <table><thead><tr><th>编码</th><th>名称</th><th>型号</th><th>状态</th><th>操作</th></tr></thead><tbody>{items.map((item) => <tr key={item.id}><td>{item.code}</td><td>{item.name}</td><td>{item.model}</td><td>{item.status}</td><td><Link to={`/equipment/${item.id}`}>详情</Link>　<Link to={`/equipment/${item.id}/edit`}>编辑</Link></td></tr>)}</tbody></table>}</State></Page>;
}

export function EquipmentDetailPage() {
  const { id = "" } = useParams();
  const equipment = useData(() => getEquipmentDetail(id), [id]);
  const history = useData(() => getEquipmentHistory(id), [id]);
  return <Page title="设备详情"><State state={equipment}>{(item) => <><dl className="detail-list"><dt>设备编码</dt><dd>{item.code}</dd><dt>设备名称</dt><dd>{item.name}</dd><dt>运行状态</dt><dd>{item.status}</dd><dt>累计工时</dt><dd>{item.operating_hours}</dd></dl><Link to={`/equipment/${item.id}/edit`}>编辑设备</Link></>}</State><h3>维修历史</h3><State state={history} empty={(data) => !data.count}>{(data) => <RecordsTable items={data.items} />}</State></Page>;
}

function EquipmentForm({ edit = false }: { edit?: boolean }) {
  const { id = "" } = useParams();
  const details = useData(() => edit ? getEquipmentDetail(id) : Promise.resolve(null), [id, edit]);
  const [message, setMessage] = useState<string | null>(null);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const body = { code: String(form.get("code")), name: String(form.get("name")), model: String(form.get("model")), type: String(form.get("type")), manufacturer: String(form.get("manufacturer")), manufactured_at: null, commissioned_at: null, operating_hours: Number(form.get("operating_hours")), status: String(form.get("status")), organization_id: String(form.get("organization_id")), owner_user_id: null, image_refs: [] };
    try { await requestJson(edit ? `/api/equipment/${id}` : "/api/equipment", { method: edit ? "PATCH" : "POST", headers: { "Content-Type": "application/json", "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify(body) }); setMessage("已保存正式设备数据。"); } catch (error) { setMessage(`保存失败：${error instanceof ApiError ? error.code : "REQUEST_FAILED"}`); }
  }
  const current = details.value;
  return <Page title={edit ? "编辑设备" : "新增设备"}>{edit && details.loading ? <p>正在加载…</p> : <form className="portal-form" onSubmit={submit}><label>设备编码<input name="code" required defaultValue={current?.code} /></label><label>设备名称<input name="name" required defaultValue={current?.name} /></label><label>型号<input name="model" required defaultValue={current?.model} /></label><label>类型<input name="type" required defaultValue={current?.type} /></label><label>制造商<input name="manufacturer" required defaultValue={current?.manufacturer} /></label><label>组织 ID<input name="organization_id" required defaultValue={current?.organization_id} /></label><label>运行工时<input name="operating_hours" type="number" min="0" defaultValue={current?.operating_hours ?? 0} /></label><label>状态<select name="status" defaultValue={current?.status ?? "NORMAL"}><option>NORMAL</option><option>FAULT</option><option>REPAIRING</option><option>DISABLED</option></select></label><button type="submit">保存</button>{message && <p role="status">{message}</p>}</form>}</Page>;
}
export const EquipmentAddPage = () => <EquipmentForm />;
export const EquipmentEditPage = () => <EquipmentForm edit />;

function RecordsTable({ items }: { items: MaintenanceRecord[] }) { return <table><thead><tr><th>工单</th><th>状态</th><th>故障</th><th>结论</th><th>知识状态</th></tr></thead><tbody>{items.map((item) => <tr key={item.maintenance_record_id}><td>{item.work_order_number}</td><td>{item.status}</td><td>{item.symptom}</td><td>{item.repair_result ?? "未完成"}</td><td>{item.knowledge_status}</td></tr>)}</tbody></table>; }

export function MaintenanceRecordsPage() { const state = useData(getMaintenanceRecords, []); return <Page title="维修记录"><State state={state} empty={(data) => !data.count}>{(data) => <RecordsTable items={data.items} />}</State></Page>; }
export function WorkOrdersPage() { const state = useData(getWorkOrders, []); return <Page title="维修执行"><State state={state} empty={(data) => !data.count}>{(data) => <table><thead><tr><th>工单</th><th>设备</th><th>状态</th><th>故障</th></tr></thead><tbody>{data.items.map((item: WorkOrder) => <tr key={item.id}><td>{item.number}</td><td>{item.equipment_id}</td><td>{item.status}</td><td>{item.symptom}</td></tr>)}</tbody></table>}</State></Page>; }

export function SystemManagementPage() { const state = useData(getAuditEvents, []); return <Page title="系统管理"><h3>审计事件</h3><State state={state} empty={(data) => !data.count}>{(data) => <table><thead><tr><th>时间</th><th>动作</th><th>资源</th><th>结果</th></tr></thead><tbody>{data.items.map((item: AuditEvent) => <tr key={item.id}><td>{item.created_at}</td><td>{item.action}</td><td>{item.resource_type}</td><td>{item.result}</td></tr>)}</tbody></table>}</State></Page>; }

export function IntelligentAuditPage() { const usage = useData(getIntelligenceUsage, []); const documents = useData(getKnowledgeDocuments, []); return <Page title="智能运维审计"><h3>调用统计</h3><State state={usage}>{(data) => <p>保留期：{data.retention_days} 天；当前受控记录：{data.count} 条。</p>}</State><h3>知识文档状态</h3><State state={documents} empty={(data) => !data.count}>{(data) => <table><thead><tr><th>文件</th><th>状态</th><th>失败原因</th><th>可重试</th></tr></thead><tbody>{data.items.map((item) => <tr key={item.id}><td>{item.filename}</td><td>{item.status}</td><td>{item.failure_reason ?? "—"}</td><td>{item.retry_available ? "是" : "否"}</td></tr>)}</tbody></table>}</State></Page>; }

export function FactoryModelingPage() { return <Page title="工厂建模"><p>组织树数据由正式组织 API 提供。当前页面使用现有组织管理入口维护，不展示原型样例数据。</p><Link to="/system-management">进入系统管理</Link></Page>; }
export function AgentReportPage() { return <Page title="AI 故障上报"><p>请从正式故障上报页面发起受控 Agent 线程和确认提交。</p><Link to="/fault-report">进入故障上报</Link></Page>; }
