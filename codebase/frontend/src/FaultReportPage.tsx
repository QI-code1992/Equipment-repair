import { FormEvent, useMemo, useState } from "react";

import {
  ApiError,
  createFaultReport,
  submitAgentFaultReport,
  uploadAttachment,
  type AttachmentRef,
  type AgentFaultDraft,
  type AgentFaultPreview,
  type FaultReportCreate,
} from "./api";

const initialForm = { equipment_id: "", urgency: "HIGH", symptom: "", occurred_at: "", possible_location: "", description: "" };

function messageFor(error: unknown) {
  if (error instanceof ApiError && error.status === 403) return "无权执行故障上报。";
  if (error instanceof ApiError && error.status === 503) return "AI 故障上报暂不可用，请继续人工填写。";
  return "提交失败，请稍后重试。";
}

function isPreview(value: Awaited<ReturnType<typeof submitAgentFaultReport>>): value is AgentFaultPreview {
  return value.agent_status === "PREVIEW";
}

export function FaultReportPage() {
  const [form, setForm] = useState(initialForm);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [preview, setPreview] = useState<AgentFaultPreview | null>(null);
  const [attachments, setAttachments] = useState<AttachmentRef[]>([]);
  const [uploading, setUploading] = useState(false);
  const [faultNumber, setFaultNumber] = useState("");
  const [equipmentName, setEquipmentName] = useState("");
  const [faultStatus, setFaultStatus] = useState("");

  const payload = useMemo<FaultReportCreate>(() => ({
    ...form,
    occurred_at: form.occurred_at ? new Date(form.occurred_at).toISOString() : "",
    possible_location: form.possible_location || undefined,
    description: form.description || undefined,
    attachment_refs: attachments,
  }), [form, attachments]);

  async function addAttachment(file: File | undefined) {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const attachment = await uploadAttachment(file);
      setAttachments((current) => [...current, attachment]);
      setNotice(`附件已通过安全检查：${attachment.filename}`);
    } catch (caught) {
      setError(caught instanceof ApiError && caught.code === "ATTACHMENT_INFECTED" ? "附件未通过安全检查，未加入故障单。" : "附件上传失败，未加入故障单。 ");
    } finally {
      setUploading(false);
    }
  }

  function draft(): AgentFaultDraft {
    return { ...payload, duration_minutes: 0 };
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const created = await createFaultReport(payload);
      setNotice(`故障已提交：${created.number}`);
    } catch (caught) { setError(messageFor(caught)); } finally { setSubmitting(false); }
  }

  async function generatePreview() {
    if (submitting || uploading) return;
    setError(null);
    setNotice(null);
    setSubmitting(true);
    try {
      const result = await submitAgentFaultReport({ draft: draft(), confirmed: false });
      if (!isPreview(result)) {
        setError("AI 草稿响应无效，请继续人工填写。");
        return;
      }
      setPreview(result);
      setNotice("请核对 AI 草稿后再正式提交。");
    } catch (caught) { setError(messageFor(caught)); } finally { setSubmitting(false); }
  }

  async function confirmPreview() {
    if (!preview) return;
    setSubmitting(true);
    setError(null);
    try {
      const created = await submitAgentFaultReport({ draft: { ...preview.draft, ...payload, duration_minutes: preview.draft.duration_minutes }, confirmed: true });
      if (isPreview(created)) throw new Error("unexpected preview");
      setPreview(null);
      setNotice(`故障已提交：${created.number}`);
    } catch (caught) { setError(messageFor(caught)); } finally { setSubmitting(false); }
  }

  return <section className="page-shell" aria-labelledby="fault-report-page-title">
    <h2 id="fault-report-page-title" className="sr-only">故障上报</h2>
    <section className="fault-module-index" aria-label="故障上报模块"><h3>查询筛选</h3><h3>故障上报列表</h3><div className="fault-filter-fields"><label>故障编号<input aria-label="故障编号" value={faultNumber} onChange={(event) => setFaultNumber(event.target.value)} /></label><label>设备名称<input aria-label="故障设备名称" value={equipmentName} onChange={(event) => setEquipmentName(event.target.value)} /></label><label>故障状态<select aria-label="故障状态" value={faultStatus} onChange={(event) => setFaultStatus(event.target.value)}><option value="">全部</option><option value="OPEN">处理中</option><option value="CLOSED">已关闭</option></select></label><div className="filter-actions"><button type="button" className="button-primary" disabled title="当前 API 未提供故障列表查询接口">查询</button><button type="button" className="button-secondary" onClick={() => { setFaultNumber(""); setEquipmentName(""); setFaultStatus(""); }}>重置</button></div></div><p className="prototype-unavailable">当前 API 未提供故障列表查询接口；正式创建仍通过故障上报 API。</p></section>
    <section className="fault-list-card" role="region" aria-label="故障上报列表"><header className="section-heading"><div><p className="section-title-text">故障上报列表</p><p>列表数据仅来自正式故障 API；当前接口未提供查询能力。</p></div><button type="button" className="button-primary" onClick={() => document.querySelector<HTMLInputElement>('input[aria-label="设备 ID"]')?.focus()}>新增故障上报</button></header><table><caption className="sr-only">故障上报列表，包含故障编号、设备名称、所属车间、所属产线、故障现象、紧急程度、上报时间、状态和操作。</caption><thead><tr><th>故障编号</th><th>设备名称</th><th>所属车间</th><th>所属产线</th><th>故障现象</th><th>紧急程度</th><th>上报时间</th><th>状态</th><th>操作</th></tr></thead><tbody><tr><td colSpan={9}><p className="prototype-unavailable" role="status" aria-label="故障列表状态">当前 API 未提供故障列表查询接口，暂无可展示的正式故障记录。</p></td></tr></tbody></table></section>
    <section className="prototype-module-grid" aria-label="故障上报原型模块"><article><h3>基础信息</h3><p>设备、紧急程度和发生时间由下方正式表单维护。</p></article><article><h3>故障描述</h3><p>故障现象与补充说明由下方正式表单维护。</p></article><article><h3>现场附件</h3><p>附件上传会经过正式安全扫描。</p></article><article><h3>维修接单信息</h3><p className="prototype-unavailable">当前 API 未提供维修接单信息展示。</p></article><article><h3>接单前智能预判</h3><p className="prototype-unavailable">当前 API 未提供独立预判结果展示。</p></article><article><h3>AI 诊断对话摘要</h3><p className="prototype-unavailable">当前 API 未提供诊断对话摘要。</p></article><article><h3>故障详情</h3><p className="prototype-unavailable">当前 API 未提供已创建故障详情读取。</p></article><article><h3>确认删除</h3><p className="prototype-unavailable">当前 API 未提供故障删除接口。</p></article><article><h3>故障摘要</h3><p className="prototype-unavailable">当前 API 未提供摘要字段读取。</p></article><article><h3>现场描述</h3><p>现场描述由故障现象和补充说明承载。</p></article><article><h3>维修进度</h3><p className="prototype-unavailable">当前 API 未提供维修进度读取。</p></article><article><h3>处理闭环</h3><p className="prototype-unavailable">当前 API 未提供处理闭环详情。</p></article><article><h3>附件证据</h3><p>已通过扫描的附件会绑定到正式故障单。</p></article></section>
    <div className="fault-workspace"><section className="fault-workspace__form"><h3>现场故障信息</h3><p>先核对设备、故障现象、发生时间和受控附件。</p><form className="fault-form" onSubmit={(event) => void submit(event)}>
      <label>设备 ID<input aria-label="设备 ID" required value={form.equipment_id} onChange={(event) => setForm({ ...form, equipment_id: event.target.value })} /></label>
      <label>紧急程度<select value={form.urgency} onChange={(event) => setForm({ ...form, urgency: event.target.value })}><option>HIGH</option><option>MEDIUM</option><option>LOW</option></select></label>
      <label>故障现象<textarea aria-label="故障现象" required value={form.symptom} onChange={(event) => setForm({ ...form, symptom: event.target.value })} /></label>
      <label>发生时间<input aria-label="发生时间" type="datetime-local" required value={form.occurred_at} onChange={(event) => setForm({ ...form, occurred_at: event.target.value })} /></label>
      <label>可能位置<input value={form.possible_location} onChange={(event) => setForm({ ...form, possible_location: event.target.value })} /></label>
      <label>补充说明<textarea value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} /></label>
      <label>附件<input aria-label="故障附件" type="file" accept="image/jpeg,image/png,image/webp,application/pdf,text/plain" disabled={uploading || submitting} onChange={(event) => void addAttachment(event.target.files?.[0])} /></label>
      {uploading && <p role="status">附件正在上传并进行安全检查…</p>}
      {attachments.length > 0 && <ul aria-label="已上传附件">{attachments.map((item) => <li key={item.object_key}>{item.filename}（{item.size_bytes} bytes）</li>)}</ul>}
      {preview && <section className="data-card" aria-label="AI 草稿预览"><h3>AI 草稿预览</h3><p>设备：{preview.draft.equipment_id}；紧急程度：{preview.draft.urgency}</p><p>故障现象：{preview.draft.symptom}</p><button type="button" disabled={submitting || uploading} onClick={() => void confirmPreview()}>确认并提交 AI 草稿</button></section>}
      {error && <p role="alert">{error}</p>}{notice && <p role="status">{notice}</p>}
      <div className="form-actions"><button type="button" disabled={submitting || uploading || Boolean(preview)} onClick={() => void generatePreview()}>生成 AI 草稿</button><button type="submit" disabled={submitting || uploading || Boolean(preview)}>{submitting ? "提交中…" : "提交故障"}</button></div>
    </form></section><aside className="fault-workspace__assistant"><h3>AI 辅助与人工确认</h3><p>AI 仅生成可编辑预览；没有人工确认，不会写入正式故障单。</p><span className="status-chip status-chip--neutral">{preview ? "待人工确认" : "等待现场信息"}</span></aside></div>
  </section>;
}
