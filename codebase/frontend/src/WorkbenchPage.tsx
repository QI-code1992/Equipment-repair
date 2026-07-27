import { useState } from "react";

import { ApiError, getHealthScore, type HealthScore } from "./api";

export function WorkbenchPage() {
  const [equipmentId, setEquipmentId] = useState("");
  const [health, setHealth] = useState<HealthScore | null>(null);
  const [message, setMessage] = useState<string | null>(null);

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
    <p>输入设备编号后读取业务服务提供的健康分。</p>
    <label>设备 ID<input aria-label="设备 ID" value={equipmentId} onChange={(event) => setEquipmentId(event.target.value)} /></label>
    <button type="button" disabled={!equipmentId} onClick={() => void loadHealth()}>查询健康分</button>
    {health && <p role="status">当前健康分：{health.score}</p>}
    {message && <p role="alert">{message}</p>}
  </section>;
}
