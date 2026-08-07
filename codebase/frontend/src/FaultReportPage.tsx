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

  function startNewReport() {
    setForm(initialForm);
    setAttachments([]);
    setPreview(null);
    setNotice(null);
    setError(null);
  }

  return <section className="portal-page fault-report-page">
    <section className="fault-query-panel" aria-label="故障查询筛选"><header><h3>查询筛选</h3><p>当前公开契约只提供创建与 AI 预览，不提供故障列表查询。</p></header><div className="fault-query-fields"><label>故障编号<input disabled placeholder="接口暂未提供" /></label><label>设备名称<input disabled placeholder="接口暂未提供" /></label><label>故障状态<select disabled><option>全部状态</option></select></label><button type="button" className="button-primary" disabled title="接口暂未提供故障列表查询">查询</button><button type="button" className="button-secondary" onClick={startNewReport}>重置</button></div></section>
    <section className="fault-list-panel"><header><div><h3>故障上报列表</h3><p>正式故障列表查询接口尚未提供。</p></div><button type="button" className="button-primary" onClick={startNewReport}>新增故障上报</button></header><p className="empty-panel">当前接口未提供故障列表查询。</p></section>
    <div className="fault-workspace"><section className="fault-workspace__form"><h3>现场故障信息</h3><p>先核对设备、故障现象、发生时间和受控附件。</p><form className="fault-form" onSubmit={(event) => void submit(event)}>
      <h4>基础信息</h4>
      <label>设备 ID<input aria-label="设备 ID" required value={form.equipment_id} onChange={(event) => setForm({ ...form, equipment_id: event.target.value })} /></label>
      <label>紧急程度<select value={form.urgency} onChange={(event) => setForm({ ...form, urgency: event.target.value })}><option>HIGH</option><option>MEDIUM</option><option>LOW</option></select></label>
      <h4>故障描述</h4>
      <label>故障现象<textarea aria-label="故障现象" required value={form.symptom} onChange={(event) => setForm({ ...form, symptom: event.target.value })} /></label>
      <label>发生时间<input aria-label="发生时间" type="datetime-local" required value={form.occurred_at} onChange={(event) => setForm({ ...form, occurred_at: event.target.value })} /></label>
      <label>可能位置<input value={form.possible_location} onChange={(event) => setForm({ ...form, possible_location: event.target.value })} /></label>
      <label>补充说明<textarea value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} /></label>
      <h4>现场附件</h4><label>附件<input aria-label="故障附件" type="file" accept="image/jpeg,image/png,image/webp,application/pdf,text/plain" disabled={uploading || submitting} onChange={(event) => void addAttachment(event.target.files?.[0])} /></label>
      {uploading && <p role="status">附件正在上传并进行安全检查…</p>}
      {attachments.length > 0 && <ul aria-label="已上传附件">{attachments.map((item) => <li key={item.object_key}>{item.filename}（{item.size_bytes} bytes）</li>)}</ul>}
      {preview && <section className="data-card" aria-label="AI 草稿预览"><h3>AI 草稿预览</h3><p>设备：{preview.draft.equipment_id}；紧急程度：{preview.draft.urgency}</p><p>故障现象：{preview.draft.symptom}</p><button type="button" disabled={submitting || uploading} onClick={() => void confirmPreview()}>确认并提交 AI 草稿</button></section>}
      {error && <p role="alert">{error}</p>}{notice && <p role="status">{notice}</p>}
      <div className="form-actions"><button type="button" disabled={submitting || uploading || Boolean(preview)} onClick={() => void generatePreview()}>生成 AI 草稿</button><button type="submit" disabled={submitting || uploading || Boolean(preview)}>{submitting ? "提交中…" : "提交故障"}</button></div>
    </form></section><aside className="fault-workspace__assistant"><h3>AI 辅助与人工确认</h3><p>AI 仅生成可编辑预览；没有人工确认，不会写入正式故障单。</p><span className="status-chip status-chip--neutral">{preview ? "待人工确认" : "等待现场信息"}</span></aside></div>
  </section>;
}
