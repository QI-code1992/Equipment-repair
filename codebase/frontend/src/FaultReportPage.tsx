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
  const [formOpen, setFormOpen] = useState(false);

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
    <section className="fault-module-index" aria-label="故障上报模块"><h3>查询筛选</h3><div className="fault-filter-fields"><label>故障编号<input aria-label="故障编号" value={faultNumber} onChange={(event) => setFaultNumber(event.target.value)} /></label><label>设备名称<input aria-label="故障设备名称" value={equipmentName} onChange={(event) => setEquipmentName(event.target.value)} /></label><label>故障状态<select aria-label="故障状态" value={faultStatus} onChange={(event) => setFaultStatus(event.target.value)}><option value="">全部</option><option value="OPEN">处理中</option><option value="CLOSED">已关闭</option></select></label><div className="filter-actions"><button type="button" className="button-primary" disabled title="当前 API 未提供故障列表查询接口">查询</button><button type="button" className="button-secondary" onClick={() => { setFaultNumber(""); setEquipmentName(""); setFaultStatus(""); }}>重置</button></div></div><p className="prototype-unavailable">当前 API 未提供故障列表查询接口；正式创建仍通过故障上报 API。</p></section>
    <section className="fault-list-card" role="region" aria-label="故障上报列表"><header className="section-heading"><div><p className="section-title-text">故障上报列表</p><p>列表数据仅来自正式故障 API；当前接口未提供查询能力。</p></div><button type="button" className="button-primary" onClick={() => setFormOpen(true)}>新增故障上报</button></header><table><caption className="sr-only">故障上报列表，包含故障编号、设备名称、所属车间、所属产线、故障现象、紧急程度、上报时间、状态和操作。</caption><thead><tr><th>故障编号</th><th>设备名称</th><th>所属车间</th><th>所属产线</th><th>故障现象</th><th>紧急程度</th><th>上报时间</th><th>状态</th><th>操作</th></tr></thead><tbody><tr><td colSpan={9}><p className="prototype-unavailable" role="status" aria-label="故障列表状态">当前 API 未提供故障列表查询接口，暂无可展示的正式故障记录。</p></td></tr></tbody></table></section>
    <section className="fault-action-surface" role="region" aria-label="故障处理动作"><header className="section-heading"><div><h3>故障处理动作</h3><p>原型保留的处理入口；当前公开 API 未提供故障列表详情及维修流转接口。</p></div><span className="status-chip status-chip--neutral">不可用</span></header><div className="fault-action-grid"><button type="button" disabled title="当前 API 未提供故障列表详情和接单接口">维修接单</button><button type="button" disabled title="当前 API 未提供维修闭环接口">维修闭环</button><button type="button" disabled title="当前 API 未提供故障详情接口">故障详情</button><button type="button" disabled title="当前 API 未提供故障删除接口">删除故障</button></div><p className="prototype-unavailable">接口补齐后将沿用原型中的详情、接单、闭环与删除交互；当前不生成演示数据。</p></section>
    <section className="fault-prototype-modules" aria-label="故障处理原型模块">
      <article className="data-card"><h3>维修接单信息</h3><div className="fault-readonly-grid"><div><span>维修人</span><strong>当前 API 未提供</strong></div><div><span>接单状态</span><strong>不可用</strong></div></div><p className="prototype-unavailable">当前 API 未提供维修接单详情，未生成演示信息。</p></article>
      <article className="data-card"><h3>故障上报现场附件</h3><div className="fault-evidence-grid"><div><span>现场图片</span><strong>当前 API 未提供</strong></div><div><span>日志 / 视频附件</span><strong>当前 API 未提供</strong></div></div><p className="prototype-unavailable">当前 API 未提供故障列表附件读取，开始维修时不可自动带出。</p></article>
      <article className="data-card fault-agent-card"><h3>接单前智能预判</h3><p className="prototype-unavailable">当前 API 未提供接单前预判结果，未生成演示内容。</p><div className="agent-input-row"><input aria-label="接单前智能预判追问" placeholder="继续追问或修正判断" disabled /><button type="button" className="button-primary" disabled title="当前 API 未提供接单前预判对话接口">发送</button></div></article>
      <article className="data-card"><h3>维修闭环</h3><div className="fault-readonly-grid"><div><span>故障类型</span><strong>当前 API 未提供</strong></div><div><span>设备状态</span><strong>当前 API 未提供</strong></div><div className="wide"><span>故障原因</span><strong>当前 API 未提供</strong></div><div className="wide"><span>处理措施</span><strong>当前 API 未提供</strong></div></div><button type="button" className="button-primary" disabled title="当前 API 未提供维修闭环接口">提交处理结果</button></article>
      <article className="data-card"><h3>故障上报现场附件</h3><div className="fault-evidence-grid"><div><span>现场图片</span><strong>当前 API 未提供</strong></div><div><span>日志 / 视频附件</span><strong>当前 API 未提供</strong></div></div><p className="prototype-unavailable">当前 API 未提供维修闭环附件回显，未生成演示内容。</p></article>
      <article className="data-card"><h3>AI 诊断对话摘要</h3><p className="prototype-unavailable">当前 API 未提供故障详情对话摘要，未生成演示内容。</p></article>
      <article className="data-card"><h3>故障详情</h3><p className="prototype-unavailable">当前 API 未提供故障详情查询，操作入口保持禁用。</p></article>
      <article className="data-card"><h3>确认删除</h3><button type="button" className="button-danger" disabled title="当前 API 未提供故障删除接口">删除故障</button><p className="prototype-unavailable">当前 API 未提供删除接口，未执行任何业务操作。</p></article>
    </section>
    {formOpen && <div className="fault-workspace" role="dialog" aria-modal="true" aria-labelledby="fault-entry-title"><section className="fault-workspace__form"><header className="fault-entry-header"><div><p className="page-shell__eyebrow">故障上报</p><h3 id="fault-entry-title">故障上报</h3><p>提交后生成待接单故障单，并进入故障分析与维修处理流转。</p></div><button type="button" className="icon-button" aria-label="关闭故障上报" onClick={() => setFormOpen(false)}>×</button></header><form className="fault-form" onSubmit={(event) => void submit(event)}>
      <section className="fault-report-section is-primary"><header className="section-heading"><div><h4>基础信息</h4><p>请选择设备，系统会自动带出车间与产线。</p></div><span className="status-chip status-chip--warning">待接单</span></header><div className="fault-report-basic-grid"><label className="field full">选择设备 *<input aria-label="设备 ID" required value={form.equipment_id} onChange={(event) => setForm({ ...form, equipment_id: event.target.value })} /></label><label className="field">所属车间<input aria-label="所属车间" value="当前 API 未提供" readOnly /></label><label className="field">所属产线<input aria-label="所属产线" value="当前 API 未提供" readOnly /></label><label className="field">紧急程度 *<select value={form.urgency} onChange={(event) => setForm({ ...form, urgency: event.target.value })}><option>HIGH</option><option>MEDIUM</option><option>LOW</option></select></label></div></section>
      <section className="fault-report-section is-primary"><header className="section-heading"><div><h4>故障描述</h4><p>用现场可复核的语言描述现象、持续时间和影响范围。</p></div></header><div className="fault-report-form-grid"><label className="field full">故障现象 *<textarea aria-label="故障现象" required value={form.symptom} onChange={(event) => setForm({ ...form, symptom: event.target.value })} /></label><label className="field">发生时间<input aria-label="发生时间" type="datetime-local" required value={form.occurred_at} onChange={(event) => setForm({ ...form, occurred_at: event.target.value })} /></label><label className="field">可能故障位置<input value={form.possible_location} onChange={(event) => setForm({ ...form, possible_location: event.target.value })} /></label><label className="field full">故障说明<textarea value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} /></label></div></section>
      <section className="fault-report-section"><header className="section-heading"><div><h4>现场附件</h4><p>可上传仪表照片、故障视频或日志文件，便于诊断中心引用。</p></div></header><div className="fault-upload-grid"><label className="fault-upload-card report-upload">现场附件<input aria-label="故障附件" type="file" accept="image/jpeg,image/png,image/webp,application/pdf,text/plain" disabled={uploading || submitting} onChange={(event) => void addAttachment(event.target.files?.[0])} /><span>{attachments.length ? `已选择 ${attachments.length} 个附件` : "未选择附件"}</span></label></div></section>
      {uploading && <p role="status">附件正在上传并进行安全检查…</p>}
      {attachments.length > 0 && <ul aria-label="已上传附件">{attachments.map((item) => <li key={item.object_key}>{item.filename}（{item.size_bytes} bytes）</li>)}</ul>}
      {preview && <section className="data-card" aria-label="AI 草稿预览"><h3>AI 草稿预览</h3><p>设备：{preview.draft.equipment_id}；紧急程度：{preview.draft.urgency}</p><p>故障现象：{preview.draft.symptom}</p><button type="button" disabled={submitting || uploading} onClick={() => void confirmPreview()}>确认并提交 AI 草稿</button></section>}
      {error && <p role="alert">{error}</p>}{notice && <p role="status">{notice}</p>}
      <div className="form-actions"><button type="button" disabled={submitting || uploading || Boolean(preview)} onClick={() => void generatePreview()}>生成 AI 草稿</button><button type="submit" disabled={submitting || uploading || Boolean(preview)}>{submitting ? "提交中…" : "提交故障"}</button></div>
    </form></section><aside className="fault-workspace__assistant"><h3>AI 辅助与人工确认</h3><p>AI 仅生成可编辑预览；没有人工确认，不会写入正式故障单。</p><span className="status-chip status-chip--neutral">{preview ? "待人工确认" : "等待现场信息"}</span></aside></div>}
  </section>;
}
