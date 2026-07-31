import { FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ApiError, AuditEvent, BiDashboard, Equipment, MaintenanceRecord, WorkOrder, createOrganization, getAuditEvents, getBiDashboard, getEquipment, getEquipmentDetail, getEquipmentHistory, getIntelligenceUsage, getKnowledgeDocuments, getMaintenanceRecords, getOrganizations, getPermissions, getRoles, getUsers, getWorkOrders, requestJson, retryKnowledgeDocument } from "./api";

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

export function SystemManagementPage() { const state = useData(getAuditEvents, []); const users = useData(getUsers, []); const roles = useData(getRoles, []); const permissions = useData(getPermissions, []); return <Page title="系统管理"><h3>账号</h3><State state={users} empty={(items) => !items.length}>{(items) => <table><thead><tr><th>账号</th><th>状态</th><th>角色</th></tr></thead><tbody>{items.map((item) => <tr key={item.id}><td>{item.username}</td><td>{item.enabled ? "启用" : "停用"}</td><td>{item.role_ids.join(", ") || "未分配"}</td></tr>)}</tbody></table>}</State><h3>角色</h3><State state={roles} empty={(items) => !items.length}>{(items) => <table><thead><tr><th>角色</th><th>权限数</th></tr></thead><tbody>{items.map((item) => <tr key={item.id}><td>{item.name}</td><td>{item.permission_codes.length}</td></tr>)}</tbody></table>}</State><h3>权限目录</h3><State state={permissions} empty={(items) => !items.length}>{(items) => <p>{items.map((item) => item.code).join("、")}</p>}</State><h3>审计事件</h3><State state={state} empty={(data) => !data.count}>{(data) => <table><thead><tr><th>时间</th><th>动作</th><th>资源</th><th>结果</th></tr></thead><tbody>{data.items.map((item: AuditEvent) => <tr key={item.id}><td>{item.created_at}</td><td>{item.action}</td><td>{item.resource_type}</td><td>{item.result}</td></tr>)}</tbody></table>}</State></Page>; }

export function IntelligentAuditPage() { const usage = useData(getIntelligenceUsage, []); const documents = useData(getKnowledgeDocuments, []); const [notice, setNotice] = useState<string | null>(null); async function retry(id: string) { try { await retryKnowledgeDocument(id); setNotice("已提交知识文档重试请求。"); } catch (error) { setNotice(`重试失败：${error instanceof ApiError ? error.code : "REQUEST_FAILED"}`); } } return <Page title="智能运维审计"><h3>调用统计</h3><State state={usage}>{(data) => <p>保留期：{data.retention_days} 天；当前受控记录：{data.count} 条。</p>}</State><h3>知识文档状态</h3>{notice && <p role="status">{notice}</p>}<State state={documents} empty={(data) => !data.count}>{(data) => <table><thead><tr><th>文件</th><th>状态</th><th>失败原因</th><th>操作</th></tr></thead><tbody>{data.items.map((item) => <tr key={item.id}><td>{item.filename}</td><td>{item.status}</td><td>{item.failure_reason ?? "—"}</td><td>{item.retry_available ? <button type="button" onClick={() => void retry(item.id)}>重新同步</button> : "—"}</td></tr>)}</tbody></table>}</State></Page>; }

export function FactoryModelingPage() { const state = useData(getOrganizations, []); const [notice, setNotice] = useState<string | null>(null); async function submit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); const form = new FormData(event.currentTarget); try { await createOrganization({ type: String(form.get("type")), code: String(form.get("code")), name: String(form.get("name")), parent_id: String(form.get("parent_id")), sort_order: Number(form.get("sort_order")), enabled: true, remark: String(form.get("remark") ?? "") }); setNotice("已创建组织节点，请刷新页面查看最新结构。"); } catch (error) { setNotice(`创建失败：${error instanceof ApiError ? error.code : "REQUEST_FAILED"}`); } } return <Page title="工厂建模"><p>组织结构由正式组织 API 提供。</p><State state={state} empty={(items) => !items.length}>{(items) => <><table><thead><tr><th>类型</th><th>编码</th><th>名称</th><th>父节点</th><th>状态</th></tr></thead><tbody>{items.map((item) => <tr key={item.id}><td>{item.type}</td><td>{item.code}</td><td>{item.name}</td><td>{item.parent_id ?? "—"}</td><td>{item.enabled ? "启用" : "停用"}</td></tr>)}</tbody></table><h3>新增组织节点</h3><form className="portal-form" onSubmit={submit}><label>类型<select name="type"><option>FACTORY</option><option>WORKSHOP</option><option>LINE</option></select></label><label>编码<input name="code" required /></label><label>名称<input name="name" required /></label><label>父节点 ID<input name="parent_id" required /></label><label>排序<input name="sort_order" type="number" min="0" defaultValue="0" /></label><label>备注<input name="remark" /></label><button type="submit">创建节点</button></form>{notice && <p role="status">{notice}</p>}</>}</State></Page>; }
export function AgentReportPage() { return <Page title="AI 故障上报"><p>请从正式故障上报页面发起受控 Agent 线程和确认提交。</p><Link to="/fault-report">进入故障上报</Link></Page>; }
