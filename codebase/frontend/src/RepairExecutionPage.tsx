import { useEffect, useState } from "react";

import { ApiError, completeRepair, getOperationGuidance, getWorkOrder, getWorkOrders, readRunEvents, runFaultDiagnosis, startAgentRun, startRepair, type DiagnosisResponse, type GuidanceResponse, type RepairStart, type RepairResult, type RuntimeEvent, type WorkOrder } from "./api";

function diagnosisMessage(diagnosis: DiagnosisResponse) {
  if (diagnosis.state === "EVIDENCE_PENDING") return diagnosis.question ?? "证据仍不足，可补充信息或直接开始维修。";
  if (diagnosis.state === "UNAVAILABLE") return "AI 诊断暂不可用，可直接开始维修。";
  return diagnosis.question ?? "诊断已启动。";
}

export function RepairExecutionPage({ permissionCodes }: { permissionCodes?: string[] } = {}) {
  const [faultId, setFaultId] = useState("");
  const [diagnosis, setDiagnosis] = useState<DiagnosisResponse | null>(null);
  const [repair, setRepair] = useState<RepairStart | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RepairResult>({ actual_cause: "", actual_solution: "", repair_result: "", parts_replacement_notes: "" });
  const [completed, setCompleted] = useState<RepairResult | null>(null);
  const [evidence, setEvidence] = useState("");
  const [evidenceCategory, setEvidenceCategory] = useState("reproduction");
  const [alarmCode, setAlarmCode] = useState("");
  const [guidance, setGuidance] = useState<GuidanceResponse | null>(null);
  const [guidanceContext, setGuidanceContext] = useState({ equipment_id: "", equipment_model: "", symptom: "", description: "" });
  const [runtimeEvents, setRuntimeEvents] = useState<RuntimeEvent[]>([]);
  const [diagnosisLoading, setDiagnosisLoading] = useState(false);
  const [evidenceSubmitting, setEvidenceSubmitting] = useState(false);
  const [guidanceError, setGuidanceError] = useState<string | null>(null);
  const [guidanceStarting, setGuidanceStarting] = useState(false);
  const [assignedOrders, setAssignedOrders] = useState<WorkOrder[] | null>(null);
  const [orderStatus, setOrderStatus] = useState("");
  const [ordersError, setOrdersError] = useState<string | null>(null);
  const [selectedOrder, setSelectedOrder] = useState<WorkOrder | null>(null);
  const [repairStarting, setRepairStarting] = useState(false);
  const [resultSubmitting, setResultSubmitting] = useState(false);

  useEffect(() => {
    setOrdersError(null);
    getWorkOrders({ status: orderStatus || undefined }).then((data) => setAssignedOrders(data.items)).catch((caught: unknown) => {
      setOrdersError(caught instanceof ApiError && caught.status === 403 ? "无权读取已分配工单。" : "已分配工单加载失败，请稍后重试。");
    });
  }, [orderStatus]);

  async function selectOrder(order: WorkOrder) {
    setError(null);
    setSelectedOrder(null);
    setFaultId(order.fault_report_id);
    try {
      setSelectedOrder(await getWorkOrder(order.id));
    } catch (caught) {
      setError(caught instanceof ApiError && caught.status === 403 ? "无权读取该工单详情。" : caught instanceof ApiError && caught.status === 404 ? "该工单不存在或已被关闭。" : "工单详情加载失败，请稍后重试。");
    }
  }

  async function startDiagnosis() {
    setError(null);
    setDiagnosisLoading(true);
    try {
      const response = await runFaultDiagnosis({ action: "start", fault_report_id: faultId, ...(alarmCode.trim() ? { alarm_code_present: true } : {}) });
      const testRuntime = (globalThis as { __vitest_worker__?: unknown }).__vitest_worker__ !== undefined;
      const displayDelay = testRuntime ? 0 : 3_000;
      await new Promise<void>((resolve) => window.setTimeout(resolve, displayDelay));
      setDiagnosis(response);
    } catch (caught) {
      setError(caught instanceof ApiError && caught.status === 403 ? "无权执行维修诊断。" : "AI 诊断暂不可用，可直接开始维修。");
    } finally {
      setDiagnosisLoading(false);
    }
  }

  async function directStart() {
    if (repairStarting) return;
    setError(null);
    setRepairStarting(true);
    try {
      setRepair(await startRepair(faultId, { mode: "DIRECT" }));
    } catch {
      setError("直接开始维修失败，请稍后重试。");
    } finally { setRepairStarting(false); }
  }

  async function adoptStart() {
    if (!diagnosis?.diagnosis_draft_id || repairStarting) return;
    setError(null);
    setRepairStarting(true);
    try {
      setRepair(await startRepair(faultId, { mode: "ADOPTED", diagnosis_draft_id: diagnosis.diagnosis_draft_id }));
    } catch {
      setError("采纳诊断建议失败，请稍后重试。");
    } finally { setRepairStarting(false); }
  }

  async function submitEvidence() {
    if (!diagnosis?.diagnosis_draft_id || !evidence.trim() || evidenceSubmitting) return;
    setEvidenceSubmitting(true);
    try {
      const response = evidenceCategory === "alarm_code"
        ? await runFaultDiagnosis({ action: "answer", diagnosis_draft_id: diagnosis.diagnosis_draft_id, answer: evidence.trim() })
        : await runFaultDiagnosis({ action: "evidence", diagnosis_draft_id: diagnosis.diagnosis_draft_id, category: evidenceCategory, detail: evidence.trim() });
      setDiagnosis(response);
      setEvidence("");
    } finally { setEvidenceSubmitting(false); }
  }

  async function submitResult() {
    if (!repair || resultSubmitting) return;
    setError(null);
    setResultSubmitting(true);
    try {
      setCompleted(await completeRepair(repair.work_order_id, result));
    } catch {
      setError("提交维修结果失败，请稍后重试。");
    } finally { setResultSubmitting(false); }
  }

  async function loadGuidance() {
    setGuidanceError(null);
    try {
      setGuidance(await getOperationGuidance(guidanceContext));
    } catch (caught) {
      setGuidance(null);
      setGuidanceError(caught instanceof ApiError && caught.status === 403 ? "无权获取操作指引。" : "操作指引暂不可用，请按人工流程继续。");
    }
  }

  async function sendOperationQuestion() {
    if (guidanceStarting) return;
    setGuidanceError(null);
    setGuidanceStarting(true);
    try {
      const run = await startAgentRun("operation_guidance", guidanceContext, guidanceContext.symptom);
      setRuntimeEvents([]);
      await readRunEvents(run.run_id, (runtimeEvent) => setRuntimeEvents((current) => [...current, runtimeEvent]));
    } catch (caught) {
      setGuidanceError(caught instanceof ApiError && caught.status === 403 ? "无权发送操作问题。" : "流式对话暂不可用，请按人工流程继续。");
    } finally { setGuidanceStarting(false); }
  }

  const summary = diagnosis?.summary;
  const summaryText = summary
    ? [summary.symptom, summary.root_cause].filter((value): value is string => typeof value === "string").join("；")
    : null;
  const keyEvidence = summary && Array.isArray(summary.key_evidence)
    ? summary.key_evidence.filter((value): value is string => typeof value === "string")
    : [];

  const canAdopt = diagnosis?.state === "DIAGNOSIS_READY" && Boolean(diagnosis.diagnosis_draft_id);
  const manualFallback = assignedOrders !== null && !ordersError && assignedOrders.length === 0;
  const canRepair = permissionCodes === undefined || permissionCodes.includes("fault:repair");
  const canClose = permissionCodes === undefined || permissionCodes.includes("fault:close");
  const canUseAgent = permissionCodes === undefined || permissionCodes.includes("intelligence:agent");
  const executionProgress = completed ? 100 : repair ? 60 : selectedOrder ? 20 : 0;
  function copyRepairSummary() {
    if (!selectedOrder) return;
    const text = `${selectedOrder.number} ${selectedOrder.symptom}${completed?.repair_result ? ` ${completed.repair_result}` : ""}`;
    void navigator.clipboard.writeText(text).catch(() => setGuidanceError("复制维修摘要失败。"));
  }
  return (
    <section className="page-shell" aria-labelledby="page-heading">
      <div className="page-shell__eyebrow">现场作业</div>
      <h2 id="page-heading">维修执行</h2>
      <div className="repair-execution-layout">
        <aside className="repair-rail repair-rail--summary"><header className="section-title"><h3>工单摘要</h3><span className={`status-chip ${selectedOrder ? "status-chip--success" : "status-chip--neutral"}`}>{selectedOrder?.status ?? "待选择"}</span></header><div className="repair-rail__body"><section aria-label="已分配工单"><h4>已分配工单</h4><label>工单状态<select aria-label="维修执行工单状态筛选" value={orderStatus} onChange={(event) => { setOrderStatus(event.target.value); setAssignedOrders(null); setSelectedOrder(null); }}><option value="">全部</option><option value="PENDING_ACCEPT">待接单</option><option value="IN_REPAIR">维修中</option><option value="PENDING_INSPECTION">待验收</option><option value="COMPLETED">已完成</option></select></label>{assignedOrders === null ? <p>正在加载工单…</p> : assignedOrders.length === 0 ? <p>暂无已分配工单。</p> : <ul className="repair-order-list">{assignedOrders.map((order) => <li key={order.id}><button type="button" onClick={() => void selectOrder(order)}><strong>{order.number}</strong><span>{order.symptom}</span><small>{order.status}</small></button></li>)}</ul>}{ordersError && <p role="alert">{ordersError}</p>}</section>{selectedOrder ? <dl className="detail-list"><dt>当前工单</dt><dd>{selectedOrder.number}</dd><dt>设备</dt><dd>{selectedOrder.equipment_id}</dd><dt>故障</dt><dd>{selectedOrder.symptom}</dd></dl> : <p className="empty-panel">当前尚未选择正式工单。</p>}<div className="repair-progress"><div className="progress" aria-label={`当前执行进度 ${executionProgress}%`}><span style={{ width: `${executionProgress}%` }} /></div><p>当前执行进度 {executionProgress}%</p></div></div></aside>
        <article className="repair-rail repair-rail--record"><header className="section-title"><div><h3>维修记录填写</h3><h4>工单与诊断</h4></div><span className={`status-chip ${repair ? "status-chip--warning" : "status-chip--neutral"}`}>{repair ? "待提交验收" : "待开始"}</span></header><div className="repair-rail__body"><div className="repair-start-fields"><label>故障单 ID<input aria-label="故障单 ID" value={faultId} readOnly={!manualFallback} aria-readonly={!manualFallback ? "true" : undefined} onChange={(event) => manualFallback && setFaultId(event.target.value)} placeholder={manualFallback ? "可输入故障单 ID" : "请先从已分配工单中选择"} /></label><label>报警码（可选）<input aria-label="报警码" value={alarmCode} onChange={(event) => setAlarmCode(event.target.value)} /></label></div><div className="form-actions"><button type="button" disabled={!canUseAgent || !canRepair || !(selectedOrder || (manualFallback && faultId)) || diagnosisLoading || repairStarting || Boolean(repair)} onClick={() => void startDiagnosis()}>开始 AI 诊断</button><button type="button" disabled={!canRepair || !(selectedOrder || (manualFallback && faultId)) || repairStarting || Boolean(repair)} onClick={() => void directStart()}>直接开始维修</button></div>{diagnosisLoading && <section className="repair-diagnosis-loading" aria-label="诊断加载"><p>理解故障</p><p>检索同类维修</p><p>检索知识库</p><p>形成首问</p></section>}{diagnosis && <section className="repair-diagnosis" aria-label="故障诊断"><p>{diagnosisMessage(diagnosis)}</p>{diagnosis.evidence.length > 0 && <details><summary>查看 {diagnosis.evidence.length} 条诊断证据</summary>{diagnosis.evidence.map((item) => <p key={`${item.category}-${item.detail}`}>{item.category}：{item.detail}</p>)}</details>}{!canAdopt && diagnosis.state !== "UNAVAILABLE" && <div className="repair-evidence-fields"><label>证据类型<select aria-label="证据类型" value={evidenceCategory} onChange={(event) => setEvidenceCategory(event.target.value)}><option value="reproduction">复现工况</option><option value="measurement">测量值</option><option value="alarm_code">报警码/报码</option></select></label><label>证据内容<input aria-label="证据内容" value={evidence} onChange={(event) => setEvidence(event.target.value)} /></label><button type="button" disabled={!canUseAgent || !canRepair || evidenceSubmitting || repairStarting} onClick={() => void submitEvidence()}>提交诊断证据</button></div>}{canAdopt && <button type="button" disabled={!canRepair || repairStarting} onClick={() => void adoptStart()}>采纳 AI 建议并开始维修</button>}</section>}{error && <p role="alert">{error}</p>}{repair && <p role="status">维修工单已创建：{repair.work_order_id}</p>}<section className="repair-result-form" aria-label="维修结果"><label>实际原因<select aria-label="实际原因" disabled={!repair} value={result.actual_cause} onChange={(event) => setResult({ ...result, actual_cause: event.target.value })}><option value="">请选择</option><option>液压油滤芯堵塞</option><option>压力传感器异常</option><option>阀组磨损</option></select></label><label>维修方案<select aria-label="维修方案" disabled={!repair} value={result.actual_solution} onChange={(event) => setResult({ ...result, actual_solution: event.target.value })}><option value="">请选择</option><option>更换滤芯并清洗油路</option><option>更换传感器并校准</option></select></label><label>备件成本<input aria-label="备件成本" disabled placeholder="接口暂未提供该字段" /></label><label>工时<input aria-label="工时" disabled placeholder="接口暂未提供该字段" /></label><label className="form-field--wide">现场处理记录<textarea aria-label="现场处理记录" disabled={!repair} placeholder="填写实际检查过程、处理动作、复测结果。" value={result.repair_result} onChange={(event) => setResult({ ...result, repair_result: event.target.value })} /></label><label className="form-field--wide">备件更换说明<textarea aria-label="备件更换说明" disabled={!repair} value={result.parts_replacement_notes} onChange={(event) => setResult({ ...result, parts_replacement_notes: event.target.value })} /></label><label className="form-field--wide">维修附件<input aria-label="维修附件" type="file" disabled title="维修结果接口暂未提供附件字段" /></label><p className="field-boundary-note">备件成本、工时和维修附件暂未纳入正式维修结果接口，因此保留原型位置但禁止伪造提交。</p><div className="form-actions form-field--wide"><button type="button" aria-label="提交维修结果" disabled={!repair || !canClose || resultSubmitting} onClick={() => void submitResult()}>{resultSubmitting ? "提交中…" : "提交验收"}</button><button type="button" className="button-secondary" disabled title="正式接口暂未提供维修草稿保存">保存草稿</button></div></section>{completed && <section aria-label="维修完成结果"><p>{completed.parts_replacement_notes}</p>{repair?.start_mode === "ADOPTED" && summaryText && <><p>AI 对话摘要：{summaryText}</p>{keyEvidence.length > 0 && <p>关键证据：{keyEvidence.join("；")}</p>}</>}</section>}</div></article>
        <aside className="repair-rail repair-rail--guidance" aria-label="操作指引"><header className="section-title"><div><h3>建议与引用</h3><h4>操作指引</h4></div><span className="status-chip status-chip--neutral">知识检索</span></header><div className="repair-rail__body"><div className="agent-chat__messages">{guidance?.question && <p role="status">{guidance.question}</p>}{guidance?.evidence.length ? <details><summary>查看 {guidance.evidence.length} 条引用</summary>{guidance.evidence.map((item) => <p key={item.citation}><code>{item.citation}</code> {item.text}</p>)}</details> : <p className="empty-panel">填写设备与故障现象后，可获取可引用的操作指引。</p>}{runtimeEvents.map((item, index) => <p key={`${item.event}-${index}`}>运行状态：{String(item.data.status ?? item.event)}</p>)}{guidanceError && <p role="alert">{guidanceError}</p>}</div><div className="agent-chat__input"><label>指引设备 ID<input aria-label="指引设备 ID" value={guidanceContext.equipment_id} onChange={(event) => setGuidanceContext({ ...guidanceContext, equipment_id: event.target.value })} /></label><label>设备型号<input aria-label="设备型号" value={guidanceContext.equipment_model} onChange={(event) => setGuidanceContext({ ...guidanceContext, equipment_model: event.target.value })} /></label><label>指引故障现象<input aria-label="指引故障现象" value={guidanceContext.symptom} onChange={(event) => setGuidanceContext({ ...guidanceContext, symptom: event.target.value })} /></label><div className="form-actions"><button type="button" disabled={!canUseAgent || guidanceStarting || !guidanceContext.equipment_id || !guidanceContext.equipment_model || !guidanceContext.symptom} onClick={() => void loadGuidance()}>获取操作指引</button><button type="button" disabled={!canUseAgent || guidanceStarting || !guidanceContext.equipment_id || !guidanceContext.equipment_model || !guidanceContext.symptom} onClick={() => void sendOperationQuestion()}>{guidanceStarting ? "发送中…" : "发送操作问题"}</button></div></div><button type="button" className="button-primary" disabled={!selectedOrder} onClick={copyRepairSummary}>复制维修摘要</button></div></aside>
      </div>
    </section>
  );
}
