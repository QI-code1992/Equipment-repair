import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { ApiError, getEquipment, getHealthScore, getWorkbenchAlertSummary, getWorkbenchShortcuts, getWorkbenchTodos, type Equipment, type HealthScore } from "./api";

type Todo = { id: string; number: string; equipment_name: string; urgency: string; symptom: string; status: string };
type Summary = { active_fault_count: number; status_counts: Array<{ status: string; count: number }>; urgency_counts: Array<{ urgency: string; count: number }> };
type QueueFilter = "all" | "pending" | "repairing" | "veryUrgent" | "urgent" | "risk";

const unavailableMessage = "当前接口未提供该正式数据。";

function countBy<Key extends "status" | "urgency">(items: Array<Record<Key, string> & { count: number }>, key: Key, value: string) {
  return items.find((item) => item[key] === value)?.count ?? 0;
}

function isFiltered(todo: Todo, filter: QueueFilter) {
  if (filter === "pending") return todo.status === "PENDING_ACCEPT";
  if (filter === "repairing") return todo.status === "IN_REPAIR";
  if (filter === "veryUrgent") return ["CRITICAL", "VERY_HIGH", "URGENT"].includes(todo.urgency);
  if (filter === "urgent") return todo.urgency === "HIGH";
  return filter !== "risk";
}

export function WorkbenchPage() {
  const [equipmentId, setEquipmentId] = useState("");
  const [health, setHealth] = useState<HealthScore | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [todos, setTodos] = useState<Todo[] | null>(null);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [shortcuts, setShortcuts] = useState<Array<{ id: string; label: string; path: string }> | null>(null);
  const [equipment, setEquipment] = useState<Equipment[]>([]);
  const [filter, setFilter] = useState<QueueFilter>("pending");

  const loadWorkbench = useCallback(() => {
    setMessage(null);
    return Promise.all([getWorkbenchTodos(), getWorkbenchAlertSummary(), getWorkbenchShortcuts(), getEquipment()])
      .then(([todoData, summaryData, shortcutData, equipmentData]) => {
        setTodos(todoData.items);
        setSummary(summaryData);
        setShortcuts(shortcutData.items);
        setEquipment(Array.isArray(equipmentData) ? equipmentData : (equipmentData && typeof equipmentData === "object" && Array.isArray((equipmentData as { items?: unknown }).items) ? (equipmentData as { items: Equipment[] }).items : []));
      })
      .catch((error: unknown) => setMessage(error instanceof ApiError && error.status === 403 ? "无权查看工作台数据。" : "工作台数据加载失败，请稍后重试。"));
  }, []);

  useEffect(() => { void loadWorkbench(); }, [loadWorkbench]);

  const visibleTodos = useMemo(() => (todos ?? []).filter((todo) => isFiltered(todo, filter)), [filter, todos]);
  const statusCounts = summary?.status_counts ?? [];
  const urgencyCounts = summary?.urgency_counts ?? [];
  const metrics: Array<{ id: Exclude<QueueFilter, "all">; label: string; icon: string; value: number | string; detail: string }> = [
    { id: "pending", label: "待接单故障", icon: "待", value: countBy(statusCounts, "status", "PENDING_ACCEPT"), detail: "等待设备管理员接单" },
    { id: "repairing", label: "维修中故障", icon: "修", value: countBy(statusCounts, "status", "IN_REPAIR"), detail: "正在现场处置" },
    { id: "veryUrgent", label: "非常紧急故障", icon: "急", value: countBy(urgencyCounts, "urgency", "CRITICAL") + countBy(urgencyCounts, "urgency", "VERY_HIGH") + countBy(urgencyCounts, "urgency", "URGENT"), detail: "建议优先查看" },
    { id: "urgent", label: "紧急故障", icon: "重", value: countBy(urgencyCounts, "urgency", "HIGH"), detail: "关注当前处置进展" },
    { id: "risk", label: "高/严重风险设备", icon: "险", value: "—", detail: "需要健康概览接口" },
  ];

  async function loadHealth() {
    setMessage(null);
    setHealth(null);
    try {
      const result = await getHealthScore(equipmentId);
      if (result.status === "UNAVAILABLE") setMessage("健康分服务暂不可用。");
      else if (result.score === undefined) setMessage("暂无健康分数据。");
      else setHealth(result);
    } catch (error) {
      setMessage(error instanceof ApiError && error.status === 403 ? "无权查看工作台数据。" : "健康分加载失败，请稍后重试。");
    }
  }

  return <section className="portal-page workbench-page" aria-labelledby="page-heading">
    <header className="workbench-head">
      <div><p className="page-shell__eyebrow">首页 / 实时处置中心</p><h2 id="page-heading">实时处置中心</h2><p>聚焦待接单、维修中和高紧急程度故障；业务事实均来自正式 API。</p></div>
      <div className="workbench-actions"><button type="button" className="button-secondary" onClick={() => void loadWorkbench()}>↻ 刷新</button>{shortcuts?.map((item) => <Link className="button-primary" key={item.id} to={item.path}>＋ {item.label}</Link>)}</div>
    </header>
    {message && <p role="alert">{message}</p>}

    <form className="data-card workbench-scope-card" aria-label="组织范围筛选">
      <label>工厂<select disabled aria-label="工厂"><option>当前接口未提供组织范围</option></select></label>
      <label>车间<select disabled aria-label="车间"><option>当前接口未提供组织范围</option></select></label>
      <label>产线<select disabled aria-label="产线"><option>当前接口未提供组织范围</option></select></label>
    </form>

    <div className="workbench-metric-grid">{metrics.map((metric) => <button key={metric.id} className={`data-card workbench-metric ${filter === metric.id ? "is-active" : ""}`} type="button" onClick={() => setFilter(metric.id)}>
      <span className="workbench-metric__top"><span>{metric.label}</span><b>{metric.icon}</b></span><strong>{summary ? metric.value : "—"}</strong><small>{metric.detail}</small>
    </button>)}</div>

    <div className="workbench-attention"><span>!</span><p>{summary?.active_fault_count ? `当前有 ${summary.active_fault_count} 项活动故障，请优先处置高紧急事项。` : "当前没有需要升级的活动故障。"}</p></div>

    <div className="workbench-primary-grid">
      <section className="data-card workbench-queue-card" aria-label="故障待办">
        <div className="workbench-module-heading"><div><span>故</span><div><h3>故障待办</h3><p>按紧急程度和正式提交时间排序</p></div></div><b className="status-chip status-chip--neutral">{visibleTodos.length} 条任务</b></div>
        <div role="tablist" aria-label="故障待办筛选" className="workbench-tabs">{(["all", "pending", "repairing", "veryUrgent", "urgent", "risk"] as QueueFilter[]).map((item) => <button key={item} role="tab" aria-selected={filter === item} className={filter === item ? "is-active" : ""} type="button" onClick={() => setFilter(item)}>{({ all: "全部", pending: "待接单", repairing: "维修中", veryUrgent: "非常紧急", urgent: "紧急", risk: "高风险关联" })[item]}</button>)}</div>
        {todos === null ? <p role="status">正在加载故障待办…</p> : filter === "risk" ? <p className="empty-panel">{unavailableMessage}</p> : visibleTodos.length === 0 ? <p className="empty-panel">暂无符合当前筛选条件的正式待办。</p> : <ul className="workbench-todo-list">{visibleTodos.map((todo) => <li key={todo.id}><div><b>{todo.number}</b><strong>{todo.equipment_name}</strong><p>{todo.symptom}</p></div><span className={`status-chip ${todo.urgency === "HIGH" || todo.urgency === "VERY_HIGH" ? "status-chip--danger" : "status-chip--warning"}`}>{todo.urgency}</span></li>)}</ul>}
      </section>
      <div className="workbench-side-stack">
        <section className="data-card workbench-health-card"><div className="workbench-module-heading"><div><span>健</span><div><h3>当前健康风险概览</h3><p>统一健康分服务实时快照</p></div></div><b className="status-chip status-chip--success">当前快照</b></div><div className="workbench-health-query"><label>设备<select aria-label="设备 ID" value={equipmentId} onChange={(event) => setEquipmentId(event.target.value)}><option value="">请选择正式设备</option>{equipment.map((item) => <option key={item.id} value={item.id}>{item.code} · {item.name}</option>)}</select></label><button type="button" className="button-primary" disabled={!equipmentId} onClick={() => void loadHealth()}>查询健康分</button></div>{health ? <p role="status">当前健康分：<strong>{health.score}</strong></p> : <p className="empty-panel">选择设备后查看正式健康分快照。</p>}</section>
        <section className="data-card workbench-today-card"><div className="workbench-module-heading"><div><span>今</span><div><h3>今日处置概览</h3><p>截至当前更新时间</p></div></div><b className="status-chip status-chip--neutral">今日</b></div><p className="empty-panel">{unavailableMessage}</p></section>
      </div>
    </div>
    <section className="data-card workbench-trend-card"><div className="workbench-module-heading"><div><span>趋</span><div><h3>故障趋势</h3><p>时间范围只影响历史故障统计，不影响当前健康分。</p></div></div><label className="workbench-select">趋势时间范围<select disabled aria-label="趋势时间范围"><option>近 7 天</option></select></label></div><div className="workbench-empty-chart"><p>{unavailableMessage}</p></div></section>
    <section className="data-card workbench-activity-card"><div className="workbench-module-heading"><div><span>动</span><div><h3>最新维修动态</h3><p>接单、维修与处理结果实时汇总</p></div></div><Link to="/maintenance-records">查看全部维修记录 →</Link></div><p className="empty-panel">{unavailableMessage}</p></section>
  </section>;
}
