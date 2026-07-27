import { useState } from "react";

import { ApiError, completeRepair, runFaultDiagnosis, startRepair, type DiagnosisResponse, type RepairStart, type RepairResult } from "./api";

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
  const [result, setResult] = useState<RepairResult>({ actual_cause: "", actual_solution: "", repair_result: "", parts_replacement_notes: "" });
  const [completed, setCompleted] = useState<RepairResult | null>(null);
  const [evidence, setEvidence] = useState("");

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

  async function submitEvidence() {
    if (!diagnosis?.diagnosis_draft_id || !evidence.trim()) return;
    setDiagnosis(await runFaultDiagnosis({
      action: "evidence", diagnosis_draft_id: diagnosis.diagnosis_draft_id,
      category: "reproduction", detail: evidence.trim(),
    }));
    setEvidence("");
  }

  async function submitResult() {
    if (!repair) return;
    setError(null);
    try {
      setCompleted(await completeRepair(repair.work_order_id, result));
    } catch {
      setError("提交维修结果失败，请稍后重试。");
    }
  }

  const summaryText = diagnosis?.summary
    ? [diagnosis.summary.symptom, diagnosis.summary.root_cause].filter((value): value is string => typeof value === "string").join("；")
    : null;

  const canAdopt = diagnosis?.state === "DIAGNOSIS_READY" && Boolean(diagnosis.diagnosis_draft_id);
  return (
    <section className="page-shell" aria-labelledby="page-heading">
      <div className="page-shell__eyebrow">现场作业</div>
      <h2 id="page-heading">维修执行</h2>
      <label>故障单 ID<input aria-label="故障单 ID" value={faultId} onChange={(event) => setFaultId(event.target.value)} /></label>
      <div className="form-actions"><button type="button" disabled={!faultId} onClick={() => void startDiagnosis()}>开始 AI 诊断</button><button type="button" disabled={!faultId} onClick={() => void directStart()}>直接开始维修</button></div>
      {diagnosis && <section aria-label="故障诊断"><p>{diagnosisMessage(diagnosis)}</p>{diagnosis.evidence.length > 0 && <details><summary>查看 {diagnosis.evidence.length} 条诊断证据</summary>{diagnosis.evidence.map((item) => <p key={`${item.category}-${item.detail}`}>{item.category}：{item.detail}</p>)}</details>}{!canAdopt && diagnosis.state !== "UNAVAILABLE" && <><label>证据内容<input aria-label="证据内容" value={evidence} onChange={(event) => setEvidence(event.target.value)} /></label><button type="button" onClick={() => void submitEvidence()}>提交诊断证据</button></>}{canAdopt && <button type="button" onClick={() => void adoptStart()}>采纳 AI 建议并开始维修</button>}</section>}
      {error && <p role="alert">{error}</p>}
      {repair && <p role="status">维修工单已创建：{repair.work_order_id}</p>}
      {repair && <section aria-label="维修结果">
        <h3>结束维修</h3>
        <label>实际原因<textarea value={result.actual_cause} onChange={(event) => setResult({ ...result, actual_cause: event.target.value })} /></label>
        <label>处理方案<textarea value={result.actual_solution} onChange={(event) => setResult({ ...result, actual_solution: event.target.value })} /></label>
        <label>维修结果<textarea value={result.repair_result} onChange={(event) => setResult({ ...result, repair_result: event.target.value })} /></label>
        <label>备件更换说明<textarea aria-label="备件更换说明" value={result.parts_replacement_notes} onChange={(event) => setResult({ ...result, parts_replacement_notes: event.target.value })} /></label>
        <button type="button" onClick={() => void submitResult()}>提交维修结果</button>
      </section>}
      {completed && <section aria-label="维修完成结果"><p>{completed.parts_replacement_notes}</p>{repair?.start_mode === "ADOPTED" && summaryText && <p>AI 对话摘要：{summaryText}</p>}</section>}
    </section>
  );
}
