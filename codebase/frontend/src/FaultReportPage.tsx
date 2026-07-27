import { FormEvent, useState } from "react";

import {
  ApiError,
  createFaultReport,
  submitAgentFaultReport,
  type FaultReportCreate,
} from "./api";

const initialForm = {
  equipment_id: "",
  urgency: "HIGH",
  symptom: "",
  occurred_at: "",
  possible_location: "",
  description: "",
};

function messageFor(error: unknown) {
  if (error instanceof ApiError && error.status === 403) return "无权执行故障上报。";
  if (error instanceof ApiError && error.status === 503) return "AI 故障上报暂不可用，请继续人工填写。";
  return "提交失败，请稍后重试。";
}

export function FaultReportPage() {
  const [form, setForm] = useState(initialForm);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const payload: FaultReportCreate = {
    ...form,
    occurred_at: form.occurred_at ? new Date(form.occurred_at).toISOString() : "",
    possible_location: form.possible_location || undefined,
    description: form.description || undefined,
    attachment_refs: [],
  };

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const created = await createFaultReport(payload);
      setNotice(`故障已提交：${created.number}`);
    } catch (caught) {
      setError(messageFor(caught));
    } finally {
      setSubmitting(false);
    }
  }

  async function useAi() {
    setError(null);
    try {
      const created = await submitAgentFaultReport({
        draft: { ...payload, duration_minutes: 0 },
        confirmed: true,
      });
      setNotice(`故障已提交：${created.number}`);
    } catch (caught) {
      setError(messageFor(caught));
    }
  }

  return (
    <section className="page-shell" aria-labelledby="page-heading">
      <div className="page-shell__eyebrow">现场作业</div>
      <h2 id="page-heading">故障上报</h2>
      <p>请先确认设备和故障现象；AI 不可用时仍可人工提交。</p>
      <form className="fault-form" onSubmit={(event) => void submit(event)}>
        <label>设备 ID<input aria-label="设备 ID" required value={form.equipment_id} onChange={(event) => setForm({ ...form, equipment_id: event.target.value })} /></label>
        <label>紧急程度<select value={form.urgency} onChange={(event) => setForm({ ...form, urgency: event.target.value })}><option>HIGH</option><option>MEDIUM</option><option>LOW</option></select></label>
        <label>故障现象<textarea aria-label="故障现象" required value={form.symptom} onChange={(event) => setForm({ ...form, symptom: event.target.value })} /></label>
        <label>发生时间<input aria-label="发生时间" type="datetime-local" required value={form.occurred_at} onChange={(event) => setForm({ ...form, occurred_at: event.target.value })} /></label>
        <label>可能位置<input value={form.possible_location} onChange={(event) => setForm({ ...form, possible_location: event.target.value })} /></label>
        <label>补充说明<textarea value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} /></label>
        {error && <p role="alert">{error}</p>}
        {notice && <p role="status">{notice}</p>}
        <div className="form-actions"><button type="button" onClick={() => void useAi()}>使用 AI 整理</button><button type="submit" disabled={submitting}>{submitting ? "提交中…" : "提交故障"}</button></div>
      </form>
    </section>
  );
}
