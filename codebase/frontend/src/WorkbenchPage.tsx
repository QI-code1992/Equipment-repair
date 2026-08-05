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

  useEffect(() => {
    setRefreshing(true);
    Promise.all([getWorkbenchTodos(), getWorkbenchAlertSummary(), getWorkbenchShortcuts(), getEquipment()])
      .then(([todoData, summaryData, shortcutData, equipmentData]) => { setTodos(todoData.items); setSummary(summaryData); setShortcuts(shortcutData.items); setEquipment(Array.isArray(equipmentData) ? equipmentData : (equipmentData && typeof equipmentData === "object" && Array.isArray((equipmentData as { items?: unknown }).items) ? (equipmentData as { items: Equipment[] }).items : [])); })
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
    <header className="workbench-head"><div><p className="page-shell__eyebrow">今日运维态势</p><h2 id="page-heading">运维工作台</h2><p>聚焦当前风险、待办和快速处置；业务事实均来自正式 API。</p></div><button type="button" className="button-secondary" disabled={refreshing} onClick={() => setRefresh((value) => value + 1)}>{refreshing ? "刷新中…" : "↻ 刷新"}</button></header>
    {message && <p role="alert">{message}</p>}
    <section className="workbench-metrics" aria-label="工作台关键指标"><article className="metric"><span className="label">待接单故障</span><strong>{summary ? countByStatus("PENDING_ACCEPT") : "—"}</strong></article><article className="metric"><span className="label">维修中故障</span><strong>{summary ? countByStatus("IN_REPAIR") : "—"}</strong></article><article className="metric"><span className="label">非常紧急故障</span><strong>{summary ? countByUrgency("VERY_HIGH") : "—"}</strong></article><article className="metric"><span className="label">紧急故障</span><strong>{summary ? countByUrgency("HIGH") : "—"}</strong></article><article className="metric metric--risk"><span className="label">活动风险设备</span><strong>{summary?.active_fault_count ?? "—"}</strong></article></section>
    <div className="workbench-layout">
      <section className="data-card queue-card" aria-label="当前待办"><div className="panel-heading"><div><h3 aria-label="待办处置">故障待办</h3><p>按紧急程度优先处理正式工单</p></div>{todos && <span className="status-chip status-chip--neutral">{visibleTodos?.length ?? 0} 项</span>}</div><div className="workbench-filters" role="group" aria-label="故障待办筛选"><button type="button" aria-pressed={todoFilter === "ALL"} onClick={() => setTodoFilter("ALL")}>全部</button><button type="button" aria-pressed={todoFilter === "PENDING_ACCEPT"} onClick={() => setTodoFilter("PENDING_ACCEPT")}>待接单</button><button type="button" aria-pressed={todoFilter === "IN_REPAIR"} onClick={() => setTodoFilter("IN_REPAIR")}>维修中</button><button type="button" aria-pressed={todoFilter === "VERY_HIGH"} onClick={() => setTodoFilter("VERY_HIGH")}>非常紧急</button><button type="button" aria-pressed={todoFilter === "HIGH"} onClick={() => setTodoFilter("HIGH")}>紧急</button><button type="button" disabled title="当前 API 未提供高风险关联筛选">高风险关联</button></div>
        {todos === null ? <p role="status">正在加载待办…</p> : visibleTodos?.length === 0 ? <p className="empty-panel">暂无符合筛选条件的活动待办。</p> : <ul className="todo-list">{visibleTodos?.map((todo) => <li key={todo.id}><div><strong>{todo.number}</strong><span>{todo.equipment_name} · {todo.symptom}</span></div><span className={`status-chip ${todo.urgency === "HIGH" ? "status-chip--danger" : "status-chip--warning"}`}>{todo.urgency}</span></li>)}</ul>}
      </section>
      <div className="workbench-side-stack">
        <section className="data-card risk-card"><div><h3>风险总览</h3><strong>{summary?.active_fault_count ?? "—"}</strong><span>活动故障</span></div><p>风险计数来自正式告警汇总，不展示推测值。</p></section>
        <section className="data-card quick-card" aria-label="快捷事项"><h3>快捷事项</h3>{shortcuts === null ? <p role="status">正在加载快捷入口…</p> : shortcuts.length === 0 ? <p className="empty-panel">暂无可用快捷入口。</p> : <div className="shortcut-list">{shortcuts.map((item) => <Link key={item.id} to={item.path}>{item.label}<span>→</span></Link>)}</div>}</section>
      </div>
    </div>
    <section className="data-card workbench-unavailable-grid"><article><div className="panel-heading"><div><h3>故障趋势</h3><p>时间范围只影响历史故障统计。</p></div></div><p className="empty-panel">当前 API 未提供故障趋势数据。</p></article><article><div className="panel-heading"><div><h3>最新维修动态</h3><p>接单、维修与处理结果实时汇总。</p></div></div><p className="empty-panel">当前 API 未提供维修动态数据。</p></article></section>
    <section className="data-card health-card" aria-label="设备健康查询"><div className="panel-heading"><div><h3>设备健康查询</h3><p>选择已授权设备后获取实时健康状态</p></div></div><div className="health-query"><label>设备<select aria-label="设备 ID" value={equipmentId} onChange={(event) => setEquipmentId(event.target.value)}><option value="">请选择正式设备</option>{equipment.map((item) => <option key={item.id} value={item.id}>{item.code} · {item.name}</option>)}</select></label><button type="button" className="button-primary" disabled={!equipmentId} onClick={() => void loadHealth()}>查询健康分</button>{health && <p role="status">当前健康分：<strong>{health.score}</strong></p>}</div></section>
  </section>;
}
