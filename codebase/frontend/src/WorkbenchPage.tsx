import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { ApiError, getEquipment, getHealthScore, getWorkbenchAlertSummary, getWorkbenchShortcuts, getWorkbenchTodos, type Equipment, type HealthScore } from "./api";

export function WorkbenchPage() {
  const [equipmentId, setEquipmentId] = useState("");
  const [health, setHealth] = useState<HealthScore | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [todos, setTodos] = useState<Array<{ id: string; number: string; equipment_name: string; urgency: string; symptom: string; status: string }> | null>(null);
  const [summary, setSummary] = useState<{ active_fault_count: number; status_counts: Array<{ status: string; count: number }>; urgency_counts: Array<{ status: string; count: number }> } | null>(null);
  const [shortcuts, setShortcuts] = useState<Array<{ id: string; label: string; path: string }> | null>(null);
  const [equipment, setEquipment] = useState<Equipment[]>([]);
  const [todoFilter, setTodoFilter] = useState<"ALL" | "PENDING_ACCEPT" | "IN_REPAIR" | "VERY_HIGH" | "HIGH">("ALL");
  const [refreshing, setRefreshing] = useState(false);
  const [refresh, setRefresh] = useState(0);
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);

  useEffect(() => {
    setRefreshing(true);
    Promise.all([getWorkbenchTodos(), getWorkbenchAlertSummary(), getWorkbenchShortcuts(), getEquipment()])
      .then(([todoData, summaryData, shortcutData, equipmentData]) => { setTodos(todoData.items); setSummary(summaryData); setShortcuts(shortcutData.items); setEquipment(Array.isArray(equipmentData) ? equipmentData : (equipmentData && typeof equipmentData === "object" && Array.isArray((equipmentData as { items?: unknown }).items) ? (equipmentData as { items: Equipment[] }).items : [])); setUpdatedAt(new Date().toLocaleString()); })
      .catch((error: unknown) => setMessage(error instanceof ApiError && error.status === 403 ? "无权查看工作台数据。" : "工作台数据加载失败，请稍后重试。"))
      .finally(() => setRefreshing(false));
  }, [refresh]);

  async function loadHealth() {
    setMessage(null);
    setHealth(null);
    try {
      const result = await getHealthScore(equipmentId);
      if (result.status === "UNAVAILABLE") setMessage("健康分服务暂不可用。\n");
      else if (result.score === undefined) setMessage("暂无健康分数据。\n");
      else setHealth(result);
    } catch (error) {
      setMessage(error instanceof ApiError && error.status === 403 ? "无权查看工作台数据。" : "健康分加载失败，请稍后重试。");
    }
  }

  const countByStatus = (value: string) => summary?.status_counts.find((item) => item.status === value)?.count ?? 0;
  const countByUrgency = (value: string) => summary?.urgency_counts.find((item) => item.status === value)?.count ?? 0;
  const visibleTodos = todos?.filter((todo) => todoFilter === "ALL" ? true : todoFilter === "PENDING_ACCEPT" || todoFilter === "IN_REPAIR" ? todo.status === todoFilter : todo.urgency === todoFilter) ?? null;

  return <section className="portal-page workbench-page" aria-labelledby="page-heading">
    <header className="workbench-head"><div><p className="page-shell__eyebrow">今日运维态势</p><h2 id="page-heading">运维工作台</h2><p>聚焦当前风险、待办和快速处置；业务事实均来自正式 API。</p></div><div className="workbench-actions"><span className="workbench-updated">数据更新时间：{updatedAt ?? "—"}</span><button type="button" className="button-secondary" disabled={refreshing} onClick={() => setRefresh((value) => value + 1)}>{refreshing ? "刷新中…" : "↻ 刷新"}</button><a aria-label="创建新故障记录" className="button-primary" href="/fault-report">＋ 故障上报</a></div></header>
    <form className="workbench-scope-card" aria-label="组织范围筛选" onSubmit={(event) => event.preventDefault()}><label>组织范围<select disabled aria-label="组织范围"><option>当前 API 未提供组织范围筛选</option></select></label><label>区域<select disabled aria-label="区域"><option>当前 API 未提供区域筛选</option></select></label><label>设备类型<select disabled aria-label="设备类型"><option>当前 API 未提供设备类型筛选</option></select></label></form>
    {message && <p role="alert">{message}</p>}
    {summary?.active_fault_count ? <div className="workbench-attention" role="status"><span className="workbench-attention__icon" aria-hidden="true">!</span><span>当前有 {summary.active_fault_count} 项活动风险，需要优先处理。</span><Link to="/fault-report">进入故障上报</Link></div> : null}
    <section className="workbench-metrics" aria-label="工作台关键指标"><button type="button" className={`metric metric-action ${todoFilter === "PENDING_ACCEPT" ? "is-active" : ""}`} onClick={() => setTodoFilter("PENDING_ACCEPT")}><span className="label">待接单故障</span><span className="metric-icon" aria-hidden="true">待</span><strong>{summary ? countByStatus("PENDING_ACCEPT") : "—"}</strong><span className="metric-delta">等待设备管理员接单</span></button><button type="button" className={`metric metric-action ${todoFilter === "IN_REPAIR" ? "is-active" : ""}`} onClick={() => setTodoFilter("IN_REPAIR")}><span className="label">维修中故障</span><span className="metric-icon" aria-hidden="true">修</span><strong>{summary ? countByStatus("IN_REPAIR") : "—"}</strong><span className="metric-delta metric-delta--warn">正在现场处置</span></button><button type="button" className={`metric metric-action ${todoFilter === "VERY_HIGH" ? "is-active" : ""}`} onClick={() => setTodoFilter("VERY_HIGH")}><span className="label">非常紧急故障</span><span className="metric-icon" aria-hidden="true">急</span><strong>{summary ? countByUrgency("VERY_HIGH") : "—"}</strong><span className="metric-delta metric-delta--bad">建议优先查看</span></button><button type="button" className={`metric metric-action ${todoFilter === "HIGH" ? "is-active" : ""}`} onClick={() => setTodoFilter("HIGH")}><span className="label">紧急故障</span><span className="metric-icon" aria-hidden="true">重</span><strong>{summary ? countByUrgency("HIGH") : "—"}</strong><span className="metric-delta metric-delta--warn">关注当前处置进展</span></button><button type="button" className="metric metric-action metric--risk" onClick={() => setTodoFilter("ALL")}><span className="label">活动风险设备</span><span className="metric-icon" aria-hidden="true">险</span><strong>{summary?.active_fault_count ?? "—"}</strong><span className="metric-delta metric-delta--bad">当前健康分快照</span></button></section>
    <div className="workbench-layout">
      <section className="data-card queue-card" aria-label="当前待办"><div className="panel-heading"><div><h3 aria-label="待办处置">故障待办</h3><p>按紧急程度优先处理正式工单</p></div>{todos && <span className="status-chip status-chip--neutral">{visibleTodos?.length ?? 0} 项</span>}</div><div className="workbench-filters" role="group" aria-label="故障待办筛选"><button type="button" aria-pressed={todoFilter === "ALL"} onClick={() => setTodoFilter("ALL")}>全部</button><button type="button" aria-pressed={todoFilter === "PENDING_ACCEPT"} onClick={() => setTodoFilter("PENDING_ACCEPT")}>待接单</button><button type="button" aria-pressed={todoFilter === "IN_REPAIR"} onClick={() => setTodoFilter("IN_REPAIR")}>维修中</button><button type="button" aria-pressed={todoFilter === "VERY_HIGH"} onClick={() => setTodoFilter("VERY_HIGH")}>非常紧急</button><button type="button" aria-pressed={todoFilter === "HIGH"} onClick={() => setTodoFilter("HIGH")}>紧急</button><button type="button" disabled title="当前 API 未提供高风险关联筛选">高风险关联</button></div>
        {todos === null ? <p role="status">正在加载待办…</p> : visibleTodos?.length === 0 ? <p className="empty-panel">暂无符合筛选条件的活动待办。</p> : <ul className="todo-list">{visibleTodos?.map((todo) => <li key={todo.id}><div><strong>{todo.number}</strong><span>{todo.equipment_name} · {todo.symptom}</span></div><span className={`status-chip ${todo.urgency === "HIGH" ? "status-chip--danger" : "status-chip--warning"}`}>{todo.urgency}</span></li>)}</ul>}
      </section>
      <div className="workbench-side-stack">
        <section className="data-card risk-card"><div><h3>风险总览</h3><strong>{summary?.active_fault_count ?? "—"}</strong><span>活动故障</span></div><p>风险计数来自正式告警汇总，不展示推测值。</p></section>
        <section className="data-card quick-card" aria-label="快捷事项"><h3>快捷事项</h3>{shortcuts === null ? <p role="status">正在加载快捷入口…</p> : shortcuts.length === 0 ? <p className="empty-panel">暂无可用快捷入口。</p> : <div className="shortcut-list">{shortcuts.map((item) => <Link key={item.id} to={item.path} aria-label="快捷入口">{item.label}<span>→</span></Link>)}</div>}</section>
        <section className="data-card today-card" aria-label="今日处置概览"><div className="panel-heading"><div><h3>今日处置概览</h3><p>当前状态汇总来自正式告警接口。</p></div></div><dl className="workbench-today-list"><div><dt>活动故障</dt><dd>{summary?.active_fault_count ?? "—"}</dd></div><div><dt>待接单</dt><dd>{summary ? countByStatus("PENDING_ACCEPT") : "—"}</dd></div><div><dt>维修中</dt><dd>{summary ? countByStatus("IN_REPAIR") : "—"}</dd></div></dl></section>
        <section className="data-card health-card" aria-label="设备健康查询"><div className="panel-heading"><div><h3>设备健康查询</h3><p>选择已授权设备后获取实时健康状态</p></div></div><div className="health-query"><label>设备<select aria-label="设备 ID" value={equipmentId} onChange={(event) => setEquipmentId(event.target.value)}><option value="">请选择正式设备</option>{equipment.map((item) => <option key={item.id} value={item.id}>{item.code} · {item.name}</option>)}</select></label><button type="button" className="button-primary" disabled={!equipmentId} onClick={() => void loadHealth()}>查询健康分</button>{health && <p role="status">当前健康分：<strong>{health.score}</strong></p>}</div></section>
      </div>
    </div>
    <section className="workbench-secondary-grid"><article className="data-card trend-card"><div className="panel-heading"><div><h3>故障趋势</h3><p>时间范围只影响历史故障统计。</p></div></div><p className="empty-panel">当前 API 未提供故障趋势数据。</p></article><article className="data-card activity-card"><div className="panel-heading"><div><h3>最新维修动态</h3><p>接单、维修与处理结果实时汇总。</p></div></div><p className="empty-panel">当前 API 未提供维修动态数据。</p></article></section>
  </section>;
}
