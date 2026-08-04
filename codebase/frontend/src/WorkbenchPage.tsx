import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { ApiError, getEquipment, getHealthScore, getWorkbenchAlertSummary, getWorkbenchShortcuts, getWorkbenchTodos, type Equipment, type HealthScore } from "./api";

export function WorkbenchPage() {
  const [equipmentId, setEquipmentId] = useState("");
  const [health, setHealth] = useState<HealthScore | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [todos, setTodos] = useState<Array<{ id: string; number: string; equipment_name: string; urgency: string; symptom: string; status: string }> | null>(null);
  const [summary, setSummary] = useState<{ active_fault_count: number } | null>(null);
  const [shortcuts, setShortcuts] = useState<Array<{ id: string; label: string; path: string }> | null>(null);
  const [equipment, setEquipment] = useState<Equipment[]>([]);

  useEffect(() => {
    Promise.all([getWorkbenchTodos(), getWorkbenchAlertSummary(), getWorkbenchShortcuts(), getEquipment()])
      .then(([todoData, summaryData, shortcutData, equipmentData]) => { setTodos(todoData.items); setSummary(summaryData); setShortcuts(shortcutData.items); setEquipment(Array.isArray(equipmentData) ? equipmentData : (equipmentData && typeof equipmentData === "object" && Array.isArray((equipmentData as { items?: unknown }).items) ? (equipmentData as { items: Equipment[] }).items : [])); })
      .catch((error: unknown) => setMessage(error instanceof ApiError && error.status === 403 ? "无权查看工作台数据。" : "工作台数据加载失败，请稍后重试。"));
  }, []);

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

  return <section className="portal-page workbench-page" aria-labelledby="page-heading">
    <header className="workbench-head"><div><p className="page-shell__eyebrow">今日运维态势</p><h2 id="page-heading">运维工作台</h2><p>聚焦当前风险、待办和快速处置；业务事实均来自正式 API。</p></div></header>
    {message && <p role="alert">{message}</p>}
    <div className="workbench-layout">
      <section className="data-card queue-card" aria-label="当前待办"><div className="panel-heading"><div><h3>待办处置</h3><p>按紧急程度优先处理正式工单</p></div>{todos && <span className="status-chip status-chip--neutral">{todos.length} 项</span>}</div>
        {todos === null ? <p role="status">正在加载待办…</p> : todos.length === 0 ? <p className="empty-panel">暂无活动待办。</p> : <ul className="todo-list">{todos.map((todo) => <li key={todo.id}><div><strong>{todo.number}</strong><span>{todo.equipment_name} · {todo.symptom}</span></div><span className={`status-chip ${todo.urgency === "HIGH" ? "status-chip--danger" : "status-chip--warning"}`}>{todo.urgency}</span></li>)}</ul>}
      </section>
      <div className="workbench-side-stack">
        <section className="data-card risk-card"><div><h3>风险总览</h3><strong>{summary?.active_fault_count ?? "—"}</strong><span>活动故障</span></div><p>风险计数来自正式告警汇总，不展示推测值。</p></section>
        <section className="data-card quick-card" aria-label="快捷事项"><h3>快捷事项</h3>{shortcuts === null ? <p role="status">正在加载快捷入口…</p> : shortcuts.length === 0 ? <p className="empty-panel">暂无可用快捷入口。</p> : <div className="shortcut-list">{shortcuts.map((item) => <Link key={item.id} to={item.path}>{item.label}<span>→</span></Link>)}</div>}</section>
      </div>
    </div>
    <section className="data-card health-card" aria-label="设备健康查询"><div className="panel-heading"><div><h3>设备健康查询</h3><p>选择已授权设备后获取实时健康状态</p></div></div><div className="health-query"><label>设备<select aria-label="设备 ID" value={equipmentId} onChange={(event) => setEquipmentId(event.target.value)}><option value="">请选择正式设备</option>{equipment.map((item) => <option key={item.id} value={item.id}>{item.code} · {item.name}</option>)}</select></label><button type="button" className="button-primary" disabled={!equipmentId} onClick={() => void loadHealth()}>查询健康分</button>{health && <p role="status">当前健康分：<strong>{health.score}</strong></p>}</div></section>
  </section>;
}
