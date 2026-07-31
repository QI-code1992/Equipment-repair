import { FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ApiError, AuditEvent, BiDashboard, Equipment, MaintenanceRecord, WorkOrder, createOrganization, createUser, deleteOrganization, getAuditEvents, getBiDashboard, getEquipment, getEquipmentDetail, getEquipmentHistory, getIntelligenceUsage, getKnowledgeDocuments, getMaintenanceRecord, getMaintenanceRecords, getOrganizations, getPermissions, getRoles, getUsers, getWorkOrders, requestJson, retryKnowledgeDocument, startAgentRun, submitAgentFaultReport, updateOrganization, updateRolePermissions, updateUser } from "./api";

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
  const [organizationId, setOrganizationId] = useState("");
  const [period, setPeriod] = useState<"day" | "week" | "month">("week");
  const state = useData<BiDashboard>(() => getBiDashboard(organizationId || undefined, period === "week" ? undefined : period), [organizationId, period]);
  const organizations = useData(getOrganizations, []);
  return <Page title="驾驶舱 BI"><div className="filter-bar"><label>组织筛选<select aria-label="组织筛选" value={organizationId} onChange={(event) => setOrganizationId(event.target.value)} disabled={organizations.loading || !!organizations.error}><option value="">全部组织</option>{organizations.value?.filter((item) => item.enabled).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label>时间窗<select aria-label="时间窗" value={period} onChange={(event) => setPeriod(event.target.value as typeof period)}><option value="day">日</option><option value="week">周</option><option value="month">月</option></select></label></div>{organizations.error && <p role="alert">组织筛选不可用：{organizations.error}</p>}{state.error?.includes("ORGANIZATION_NOT_FOUND") && <p role="alert">所选组织不存在或已被移除。</p>}<State state={state}>{(value) => <div className="data-grid"><div className="metric"><b>{value.summary.fault_count}</b><span>故障总数</span></div><div className="metric"><b>{value.summary.active_fault_count}</b><span>活动故障</span></div><div className="metric"><b>{value.summary.completed_work_order_count}</b><span>完成工单</span></div><div className="metric"><b>{Math.round(value.summary.completion_rate * 100)}%</b><span>完成率</span></div><section className="data-card"><h3>{period === "day" ? "当日" : period === "month" ? "近 30 日" : "近 7 日"}趋势</h3>{value.trend.length ? <ul>{value.trend.map((item) => <li key={item.date}>{item.date}：故障 {item.fault_count}，完成 {item.completed_work_order_count}</li>)}</ul> : <p>暂无趋势数据。</p>}</section><section className="data-card"><h3>效率与历史对比</h3><p>{value.efficiency.average_completion_hours === null ? "暂无具有开始与完成时间的工单，无法计算平均完成时长。" : `平均完成 ${value.efficiency.average_completion_hours} 小时`}</p><p>当前窗口故障 {value.history_comparison.current_fault_count}，上一窗口故障 {value.history_comparison.previous_fault_count}。</p></section><section className="data-card"><h3>组织故障排行</h3>{value.organization_ranking.length ? <ol>{value.organization_ranking.map((item) => <li key={item.organization_id}>{item.organization_name}：{item.fault_count}</li>)}</ol> : <p>暂无排行数据。</p>}</section></div>}</State></Page>;
}

export function EquipmentLedgerPage() {
  const state = useData<Equipment[]>(getEquipment, []);
  const [query, setQuery] = useState("");
  return <Page title="设备台账"><p><Link to="/equipment/new">新增设备</Link></p><label>筛选设备<input aria-label="筛选设备" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="按编码、名称、型号筛选" /></label><State state={state} empty={(items) => !items.length}>{(items) => { const filtered = items.filter((item) => !query || [item.code, item.name, item.model, item.status].some((value) => value.includes(query))); return filtered.length ? <table><thead><tr><th>编码</th><th>名称</th><th>型号</th><th>状态</th><th>操作</th></tr></thead><tbody>{filtered.map((item) => <tr key={item.id}><td>{item.code}</td><td>{item.name}</td><td>{item.model}</td><td>{item.status}</td><td><Link to={`/equipment/${item.id}`}>详情</Link>　<Link to={`/equipment/${item.id}/edit`}>编辑</Link></td></tr>)}</tbody></table> : <p role="status">没有符合筛选条件的正式设备数据。</p>; }}</State></Page>;
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
  const organizations = useData(getOrganizations, []);
  const users = useData(getUsers, []);
  const [message, setMessage] = useState<string | null>(null);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const ownerUserId = String(form.get("owner_user_id") ?? "");
    const body = { code: String(form.get("code")), name: String(form.get("name")), model: String(form.get("model")), type: String(form.get("type")), manufacturer: String(form.get("manufacturer")), manufactured_at: null, commissioned_at: null, operating_hours: Number(form.get("operating_hours")), status: String(form.get("status")), organization_id: String(form.get("organization_id")), owner_user_id: ownerUserId || null, image_refs: [] };
    try { await requestJson(edit ? `/api/equipment/${id}` : "/api/equipment", { method: edit ? "PATCH" : "POST", headers: { "Content-Type": "application/json", "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify(body) }); setMessage("已保存正式设备数据。"); } catch (error) { setMessage(`保存失败：${error instanceof ApiError ? error.code : "REQUEST_FAILED"}`); }
  }
  const current = details.value;
  if (details.loading || organizations.loading || users.loading) return <Page title={edit ? "编辑设备" : "新增设备"}><p role="status">正在加载…</p></Page>;
  if (details.error || organizations.error || users.error) return <Page title={edit ? "编辑设备" : "新增设备"}><p role="alert">无法加载设备依赖：{details.error ?? organizations.error ?? users.error}</p></Page>;
  const lines = (organizations.value ?? []).filter((item) => item.type === "LINE" && item.enabled);
  const owners = (users.value ?? []).filter((item) => item.enabled);
  return <Page title={edit ? "编辑设备" : "新增设备"}><form className="portal-form" onSubmit={submit}><label>设备编码<input name="code" required defaultValue={current?.code} /></label><label>设备名称<input name="name" required defaultValue={current?.name} /></label><label>型号<input name="model" required defaultValue={current?.model} /></label><label>类型<input name="type" required defaultValue={current?.type} /></label><label>制造商<input name="manufacturer" required defaultValue={current?.manufacturer} /></label><label>所属产线<select name="organization_id" aria-label="所属产线" required defaultValue={current?.organization_id ?? lines[0]?.id ?? ""}><option value="" disabled>请选择启用产线</option>{lines.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label>负责人<select name="owner_user_id" aria-label="负责人" defaultValue={current?.owner_user_id ?? ""}><option value="">未分配</option>{owners.map((item) => <option key={item.id} value={item.id}>{item.username}</option>)}</select></label><label>运行工时<input name="operating_hours" type="number" min="0" defaultValue={current?.operating_hours ?? 0} /></label><label>状态<select name="status" defaultValue={current?.status ?? "NORMAL"}><option>NORMAL</option><option>FAULT</option><option>REPAIRING</option><option>DISABLED</option></select></label><button type="submit" disabled={!lines.length}>保存</button>{!lines.length && <p role="alert">没有可用产线，无法保存设备。</p>}{message && <p role="status">{message}</p>}</form></Page>;
}
export const EquipmentAddPage = () => <EquipmentForm />;
export const EquipmentEditPage = () => <EquipmentForm edit />;

function RecordsTable({ items }: { items: MaintenanceRecord[] }) { return <table><thead><tr><th>工单</th><th>状态</th><th>故障</th><th>结论</th><th>知识状态</th><th>操作</th></tr></thead><tbody>{items.map((item) => <tr key={item.maintenance_record_id}><td>{item.work_order_number}</td><td>{item.status}</td><td>{item.symptom}</td><td>{item.repair_result ?? "未完成"}</td><td>{item.knowledge_status}</td><td><Link to={`/maintenance-records/${item.maintenance_record_id}`}>详情</Link></td></tr>)}</tbody></table>; }

export function MaintenanceRecordsPage() {
  const [equipmentId, setEquipmentId] = useState("");
  const [page, setPage] = useState(1);
  const state = useData(() => getMaintenanceRecords({ equipmentId: equipmentId || undefined, page }), [equipmentId, page]);
  return <Page title="维修记录"><label>设备筛选<input aria-label="维修记录设备筛选" value={equipmentId} onChange={(event) => { setEquipmentId(event.target.value); setPage(1); }} /></label><State state={state} empty={(data) => !data.count}>{(data) => <><RecordsTable items={data.items} /><div className="pager"><button type="button" disabled={page <= 1} onClick={() => setPage((current) => current - 1)}>上一页</button><span>第 {page} 页</span><button type="button" disabled={data.items.length < data.page_size} onClick={() => setPage((current) => current + 1)}>下一页</button></div></>}</State></Page>;
}
export function MaintenanceRecordDetailPage() { const { id = "" } = useParams(); const state = useData(() => getMaintenanceRecord(id), [id]); return <Page title="维修记录详情"><State state={state}>{(item) => <dl className="detail-list"><dt>工单</dt><dd>{item.work_order_number}</dd><dt>故障现象</dt><dd>{item.symptom}</dd><dt>实际原因</dt><dd>{item.actual_cause ?? "未填写"}</dd><dt>解决方案</dt><dd>{item.actual_solution ?? "未填写"}</dd><dt>维修结果</dt><dd>{item.repair_result ?? "未完成"}</dd><dt>更换部件</dt><dd>{item.parts_replacement_notes ?? "无"}</dd><dt>知识状态</dt><dd>{item.knowledge_status}</dd></dl>}</State></Page>; }
export function WorkOrdersPage() { const state = useData(getWorkOrders, []); return <Page title="维修执行"><State state={state} empty={(data) => !data.count}>{(data) => <table><thead><tr><th>工单</th><th>设备</th><th>状态</th><th>故障</th></tr></thead><tbody>{data.items.map((item: WorkOrder) => <tr key={item.id}><td>{item.number}</td><td>{item.equipment_id}</td><td>{item.status}</td><td>{item.symptom}</td></tr>)}</tbody></table>}</State></Page>; }

export function SystemManagementPage() { return <SystemManagementContent />; }

function SystemManagementContent() {
  const audits = useData(getAuditEvents, []);
  const users = useData(getUsers, []);
  const roles = useData(getRoles, []);
  const permissions = useData(getPermissions, []);
  const [notice, setNotice] = useState<string | null>(null);

  async function toggle(user: { id: string; enabled: boolean; role_ids: string[] }) {
    try {
      await updateUser(user.id, { enabled: !user.enabled, role_ids: user.role_ids });
      setNotice("账号状态已提交更新，请刷新列表确认。");
    } catch {
      setNotice("账号更新失败，请检查权限或状态后重试。");
    }
  }

  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await createUser({
        username: String(form.get("username")),
        password: String(form.get("password")),
        role_ids: [String(form.get("role_id"))],
      });
      setNotice("账号已创建，请刷新列表确认。");
    } catch {
      setNotice("账号创建失败，请检查输入和权限后重试。");
    }
  }

  return <Page title="系统管理">
    {notice && <p role="status">{notice}</p>}
    <h3>账号</h3>
    <State state={users} empty={(items) => !items.length}>{(items) => <>
      <table><thead><tr><th>账号</th><th>状态</th><th>角色</th><th>操作</th></tr></thead><tbody>{items.map((item) => <tr key={item.id}><td>{item.username}</td><td>{item.enabled ? "启用" : "停用"}</td><td>{item.role_ids.join(", ") || "未分配"}</td><td><button type="button" onClick={() => void toggle(item)}>{item.enabled ? "停用" : "启用"}</button></td></tr>)}</tbody></table>
      <form className="portal-form" onSubmit={create}><label>用户名<input name="username" required /></label><label>初始密码<input name="password" type="password" minLength={8} required /></label><label>角色<select name="role_id">{roles.value?.map((role) => <option key={role.id} value={role.id}>{role.name}</option>)}</select></label><button type="submit">创建账号</button></form>
    </>}</State>
    <h3>角色</h3>
    <State state={roles} empty={(items) => !items.length}>{(items) => <div>{items.map((item) => <RolePermissionEditor key={item.id} role={item} permissions={permissions.value ?? []} onSaved={() => setNotice("角色权限已提交更新，请刷新列表确认。")} onFailed={() => setNotice("角色更新失败，请检查权限后重试。")} />)}</div>}</State>
    <h3>权限目录</h3><State state={permissions} empty={(items) => !items.length}>{(items) => <p>{items.map((item) => item.code).join("、")}</p>}</State>
    <h3>审计事件</h3><State state={audits} empty={(data) => !data.count}>{(data) => <table><thead><tr><th>时间</th><th>动作</th><th>资源</th><th>结果</th></tr></thead><tbody>{data.items.map((item: AuditEvent) => <tr key={item.id}><td>{item.created_at}</td><td>{item.action}</td><td>{item.resource_type}</td><td>{item.result}</td></tr>)}</tbody></table>}</State>
  </Page>;
}

function RolePermissionEditor({ role, permissions, onSaved, onFailed }: { role: { id: string; name: string; permission_codes: string[] }; permissions: Array<{ code: string }>; onSaved: () => void; onFailed: () => void }) {
  const [selected, setSelected] = useState(role.permission_codes);
  useEffect(() => setSelected(role.permission_codes), [role.id, role.permission_codes]);
  async function save() {
    try {
      await updateRolePermissions(role.id, selected);
      onSaved();
    } catch {
      onFailed();
    }
  }
  return <fieldset className="portal-form"><legend>{role.name}</legend><p>已选 {selected.length} 项权限。</p>{permissions.map((permission) => <label key={permission.code}><input type="checkbox" aria-label={permission.code} checked={selected.includes(permission.code)} onChange={(event) => setSelected((current) => event.target.checked ? [...current, permission.code] : current.filter((code) => code !== permission.code))} />{permission.code}</label>)}<button type="button" onClick={() => void save()}>保存角色权限</button></fieldset>;
}

export function IntelligentAuditPage() { const usage = useData(getIntelligenceUsage, []); const documents = useData(() => getKnowledgeDocuments({ page: 1 }), []); const [notice, setNotice] = useState<string | null>(null); const [action, setAction] = useState(""); async function retry(id: string) { try { await retryKnowledgeDocument(id); setNotice("已提交知识文档重试请求。"); } catch (error) { setNotice(`重试失败：${error instanceof ApiError ? error.code : "REQUEST_FAILED"}`); } } return <Page title="智能运维审计"><h3>调用统计</h3><State state={usage}>{(data) => <><p>保留期：{data.retention_days} 天；当前受控记录：{data.count} 条。</p><p>配置 Token 预算统计，不代表模型实际消耗。</p>{data.items.length ? <table><thead><tr><th>Agent</th><th>状态</th><th>调用数</th><th>配置 Token 预算</th></tr></thead><tbody>{data.items.map((item) => <tr key={`${item.agent_id}-${item.status}`}><td>{item.agent_id}</td><td>{item.status}</td><td>{item.run_count}</td><td>{item.configured_max_reply_tokens}</td></tr>)}</tbody></table> : <p>暂无受控调用记录。</p>}</>}</State><h3>知识文档状态</h3>{notice && <p role="status">{notice}</p>}<label>动作筛选<select aria-label="知识状态筛选" value={action} onChange={(event) => setAction(event.target.value)}><option value="">全部</option><option value="FAILED">失败</option><option value="READY">完成</option></select></label><State state={documents} empty={(data) => !data.count}>{(data) => <table><thead><tr><th>文件</th><th>状态</th><th>失败原因</th><th>操作</th></tr></thead><tbody>{data.items.filter((item) => !action || item.status === action).map((item) => <tr key={item.id}><td>{item.filename}</td><td>{item.status}</td><td>{item.failure_reason ?? "—"}</td><td>{item.retry_available ? <button type="button" onClick={() => void retry(item.id)}>重新同步</button> : "—"}</td></tr>)}</tbody></table>}</State></Page>; }

type OrganizationItem = { id: string; type: string; code: string; name: string; parent_id: string | null; enabled: boolean; sort_order?: number; remark?: string };

export function FactoryModelingPage() {
  const state = useData(getOrganizations, []);
  const [query, setQuery] = useState("");
  const [collapsed, setCollapsed] = useState<string[]>([]);
  const [notice, setNotice] = useState<string | null>(null);
  const [editing, setEditing] = useState<OrganizationItem | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await createOrganization({ type: String(form.get("type")), code: String(form.get("code")), name: String(form.get("name")), parent_id: String(form.get("parent_id")), sort_order: Number(form.get("sort_order")), enabled: true, remark: String(form.get("remark") ?? "") });
      setNotice("已创建组织节点，请刷新页面查看最新结构。");
    } catch (error) { setNotice(`创建失败：${error instanceof ApiError ? error.code : "REQUEST_FAILED"}`); }
  }

  async function toggle(item: OrganizationItem) {
    try {
      await updateOrganization(item.id, { code: item.code, name: item.name, sort_order: item.sort_order ?? 0, enabled: !item.enabled, remark: item.remark ?? "" });
      setNotice("组织状态已提交更新，请刷新页面确认。");
    } catch (error) { setNotice(`状态更新失败：${error instanceof ApiError ? error.code : "REQUEST_FAILED"}`); }
  }

  async function remove(item: OrganizationItem) {
    try {
      await deleteOrganization(item.id);
      setNotice("删除请求已提交，请刷新页面确认。");
    } catch (error) { setNotice(`删除受阻：${error instanceof ApiError ? error.code : "REQUEST_FAILED"}`); }
  }

  async function saveEdit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editing) return;
    const form = new FormData(event.currentTarget);
    try {
      await updateOrganization(editing.id, { code: String(form.get("code")), name: String(form.get("name")), sort_order: Number(form.get("sort_order")), enabled: editing.enabled, remark: String(form.get("remark") ?? "") });
      setEditing(null);
      setNotice("组织信息已提交更新，请刷新页面确认。");
    } catch (error) { setNotice(`编辑失败：${error instanceof ApiError ? error.code : "REQUEST_FAILED"}`); }
  }

  return <Page title="工厂建模"><p>组织结构由正式组织 API 提供。</p>{notice && <p role="status">{notice}</p>}<label>搜索组织<input aria-label="搜索组织" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="按编码或名称筛选" /></label><State state={state} empty={(items) => !items.length}>{(items) => <><OrganizationTree items={items as OrganizationItem[]} query={query} collapsed={collapsed} onToggle={(id) => setCollapsed((current) => current.includes(id) ? current.filter((value) => value !== id) : [...current, id])} onEdit={setEditing} onStateChange={toggle} onDelete={remove} /><h3>新增组织节点</h3><form className="portal-form" onSubmit={submit}><label>类型<select name="type"><option>FACTORY</option><option>WORKSHOP</option><option>LINE</option></select></label><label>编码<input name="code" required /></label><label>名称<input name="name" required /></label><label>父节点 ID<input name="parent_id" required /></label><label>排序<input name="sort_order" type="number" min="0" defaultValue="0" /></label><label>备注<input name="remark" /></label><button type="submit">创建节点</button></form>{editing && <form className="portal-form" onSubmit={saveEdit}><h3>编辑组织：{editing.name}</h3><label>编码<input name="code" required defaultValue={editing.code} /></label><label>名称<input name="name" required defaultValue={editing.name} /></label><label>排序<input name="sort_order" type="number" min="0" defaultValue={editing.sort_order ?? 0} /></label><label>备注<input name="remark" defaultValue={editing.remark ?? ""} /></label><button type="submit">保存组织</button><button type="button" onClick={() => setEditing(null)}>取消</button></form>}</>}</State></Page>;
}

function OrganizationTree({ items, query, collapsed, onToggle, onEdit, onStateChange, onDelete }: { items: OrganizationItem[]; query: string; collapsed: string[]; onToggle: (id: string) => void; onEdit: (item: OrganizationItem) => void; onStateChange: (item: OrganizationItem) => void; onDelete: (item: OrganizationItem) => void }) {
  const byParent = new Map<string | null, OrganizationItem[]>();
  for (const item of items) byParent.set(item.parent_id, [...(byParent.get(item.parent_id) ?? []), item]);
  const matches = (item: OrganizationItem): boolean => !query || item.name.includes(query) || item.code.includes(query) || (byParent.get(item.id) ?? []).some(matches);
  const rows: Array<{ item: OrganizationItem; depth: number }> = [];
  const visited = new Set<string>();
  function visit(parentId: string | null, depth: number) { for (const item of byParent.get(parentId) ?? []) { if (visited.has(item.id) || !matches(item)) continue; visited.add(item.id); rows.push({ item, depth }); if (!collapsed.includes(item.id) || query) visit(item.id, depth + 1); } }
  visit(null, 0);
  for (const item of items) if (!visited.has(item.id) && matches(item)) { visited.add(item.id); rows.push({ item, depth: 0 }); }
  return <table><thead><tr><th>类型</th><th>编码</th><th>名称</th><th>父节点</th><th>状态</th><th>操作</th></tr></thead><tbody>{rows.map(({ item, depth }) => { const hasChildren = (byParent.get(item.id) ?? []).length > 0; const root = item.type === "ROOT"; return <tr key={item.id}><td>{item.type}</td><td>{item.code}</td><td style={{ paddingLeft: `${depth * 20}px` }}>{hasChildren && <button type="button" aria-label={`${collapsed.includes(item.id) ? "展开" : "收起"} ${item.name}`} onClick={() => onToggle(item.id)}>{collapsed.includes(item.id) ? "+" : "−"}</button>} {item.name}</td><td>{item.parent_id ?? "—"}</td><td>{item.enabled ? "启用" : "停用"}</td><td>{root ? "根节点受保护" : <><button type="button" onClick={() => onEdit(item)}>编辑</button><button type="button" aria-label={`${item.enabled ? "停用" : "启用"} ${item.name}`} onClick={() => void onStateChange(item)}>{item.enabled ? "停用" : "启用"}</button><button type="button" onClick={() => void onDelete(item)}>删除</button></>}</td></tr>; })}</tbody></table>;
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

  async function collect(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    try {
      await startAgentRun("fault_reporting", { equipment_id: equipmentId }, symptom);
      setCollected(true);
      setNotice("AI 收集任务已创建，请补全并确认正式上报字段。");
    } catch (caught) { setError(`创建 AI 收集任务失败：${caught instanceof ApiError ? caught.code : "REQUEST_FAILED"}`); }
  }

  async function confirm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const created = await submitAgentFaultReport({ draft: { equipment_id: equipmentId, urgency, symptom, occurred_at: new Date(occurredAt).toISOString(), possible_location: undefined, description: description || undefined, attachment_refs: [], duration_minutes: 0 }, confirmed: true });
      if ("draft" in created) throw new Error("unexpected preview");
      setNotice(`故障已正式提交：${created.number}`);
    } catch (caught) { setError(`正式提交失败：${caught instanceof ApiError ? caught.code : "REQUEST_FAILED"}`); } finally { setSubmitting(false); }
  }

  return <Page title="AI 故障上报"><p>AI 只负责受控收集；它不会直接写入故障事实。正式上报必须由用户完成结构化确认。</p><form className="portal-form" onSubmit={collect}><label>设备 ID<input aria-label="设备 ID" value={equipmentId} onChange={(event) => setEquipmentId(event.target.value)} required /></label><label>故障描述<textarea aria-label="故障描述" value={symptom} onChange={(event) => setSymptom(event.target.value)} required /></label><button type="submit">开始 AI 收集</button></form>{collected && <form className="portal-form" onSubmit={confirm}><h3>结构化确认</h3><label>紧急程度<select value={urgency} onChange={(event) => setUrgency(event.target.value)}><option>HIGH</option><option>MEDIUM</option><option>LOW</option></select></label><label>发生时间<input aria-label="发生时间" type="datetime-local" value={occurredAt} onChange={(event) => setOccurredAt(event.target.value)} required /></label><label>补充说明<textarea value={description} onChange={(event) => setDescription(event.target.value)} /></label><button type="submit" disabled={submitting || !occurredAt}>{submitting ? "提交中…" : "确认并提交正式故障单"}</button></form>}{error && <p role="alert">{error}</p>}{notice && <p role="status">{notice}</p>}<p><Link to="/fault-report">转到人工故障上报</Link></p></Page>;
}
