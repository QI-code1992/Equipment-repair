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

  return <section className="page-shell" aria-labelledby="page-heading">
    <div className="page-shell__eyebrow">工作台</div><h2 id="page-heading">运维工作台</h2>
    <p>工作台只展示正式业务服务返回的待办、告警与快捷入口。</p>
    {summary && <p role="status">活动故障：{summary.active_fault_count}</p>}
    {todos === null ? <p>正在加载待办…</p> : todos.length === 0 ? <p>暂无活动待办。</p> : <section aria-label="当前待办"><h3>当前待办</h3><ul>{todos.map((todo) => <li key={todo.id}>{todo.number} · {todo.equipment_name} · {todo.urgency} · {todo.symptom}</li>)}</ul></section>}
    {shortcuts && <section aria-label="快捷事项">{shortcuts.map((item) => <Link key={item.id} to={item.path}>{item.label}</Link>)}</section>}
    <label>设备 ID<select aria-label="设备 ID" value={equipmentId} onChange={(event) => setEquipmentId(event.target.value)}><option value="">请选择正式设备</option>{equipment.map((item) => <option key={item.id} value={item.id}>{item.code} · {item.name}</option>)}</select></label>
    <button type="button" disabled={!equipmentId} onClick={() => void loadHealth()}>查询健康分</button>
    {health && <p role="status">当前健康分：{health.score}</p>}
    {message && <p role="alert">{message}</p>}
  </section>;
}
