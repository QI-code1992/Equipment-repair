import { useState } from "react";

import { ApiError, runFaultDiagnosis, startRepair, type DiagnosisResponse, type RepairStart } from "./api";

function diagnosisMessage(diagnosis: DiagnosisResponse) {
  if (diagnosis.state === "EVIDENCE_PENDING") return "证据仍不足，可补充信息或直接开始维修。";
  if (diagnosis.state === "UNAVAILABLE") return "AI 诊断暂不可用，可直接开始维修。";
  return diagnosis.question ?? "诊断已启动。";
}

export function RepairExecutionPage() {
  const [faultId, setFaultId] = useState("");
  const [diagnosis, setDiagnosis] = useState<DiagnosisResponse | null>(null);
  const [repair, setRepair] = useState<RepairStart | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function startDiagnosis() {
    setError(null);
    try {
      setDiagnosis(await runFaultDiagnosis({ action: "start", fault_report_id: faultId }));
    } catch (caught) {
      setError(caught instanceof ApiError && caught.status === 403 ? "无权执行维修诊断。" : "AI 诊断暂不可用，可直接开始维修。");
    }
  }

  async function directStart() {
    setError(null);
    try {
      setRepair(await startRepair(faultId, { mode: "DIRECT" }));
    } catch {
      setError("直接开始维修失败，请稍后重试。");
    }
  }

  async function adoptStart() {
    if (!diagnosis?.diagnosis_draft_id) return;
    setRepair(await startRepair(faultId, { mode: "ADOPTED", diagnosis_draft_id: diagnosis.diagnosis_draft_id }));
  }

  const canAdopt = diagnosis?.state === "DIAGNOSIS_READY" && Boolean(diagnosis.diagnosis_draft_id);
  return (
    <section className="page-shell" aria-labelledby="page-heading">
      <div className="page-shell__eyebrow">现场作业</div>
      <h2 id="page-heading">维修执行</h2>
      <label>故障单 ID<input aria-label="故障单 ID" value={faultId} onChange={(event) => setFaultId(event.target.value)} /></label>
      <div className="form-actions"><button type="button" disabled={!faultId} onClick={() => void startDiagnosis()}>开始 AI 诊断</button><button type="button" disabled={!faultId} onClick={() => void directStart()}>直接开始维修</button></div>
      {diagnosis && <section aria-label="故障诊断"><p>{diagnosisMessage(diagnosis)}</p>{diagnosis.evidence.length > 0 && <details><summary>查看 {diagnosis.evidence.length} 条诊断证据</summary>{diagnosis.evidence.map((item) => <p key={`${item.category}-${item.detail}`}>{item.category}：{item.detail}</p>)}</details>}{canAdopt && <button type="button" onClick={() => void adoptStart()}>采纳 AI 建议并开始维修</button>}</section>}
      {error && <p role="alert">{error}</p>}
      {repair && <p role="status">维修工单已创建：{repair.work_order_id}</p>}
    </section>
  );
}
