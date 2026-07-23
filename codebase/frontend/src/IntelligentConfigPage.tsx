import { useEffect, useState } from "react";

import { type AgentConfig, getAgentConfig, getAgentConfigs, saveAgentConfig } from "./api";

const agentLabels: Record<string, string> = {
  fault_reporting: "AI 故障上报",
  metric_query: "智能问数",
  operation_guidance: "操作指引",
  fault_diagnosis: "故障诊断",
};
const agentIds = Object.keys(agentLabels);

function agentLabel(agentId: string) {
  return agentLabels[agentId] ?? agentId;
}

export function IntelligentConfigPage() {
  const [configs, setConfigs] = useState<AgentConfig[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [draft, setDraft] = useState<AgentConfig | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getAgentConfigs()
      .then((items) => {
        setConfigs(items);
        return items.find((item) => item.agent_id === "fault_reporting")
          ?? getAgentConfig("fault_reporting");
      })
      .then((first) => {
        setSelectedId(first.agent_id);
        setDraft(first);
        setConfigs((items) => items.some((item) => item.agent_id === first.agent_id) ? items : [...items, first]);
      })
      .catch(() => setError("智能配置加载失败，请稍后重试。"))
      .finally(() => setLoading(false));
  }, []);

  async function select(agentId: string) {
    const existing = configs.find((item) => item.agent_id === agentId);
    if (existing) {
      setSelectedId(existing.agent_id);
      setDraft(existing);
      setError(null);
      setNotice(null);
      return;
    }
    setLoading(true);
    setError(null);
    setNotice(null);
    try {
      const config = await getAgentConfig(agentId);
      setConfigs((items) => [...items, config]);
      setSelectedId(config.agent_id);
      setDraft(config);
    } catch {
      setError("智能配置加载失败，请稍后重试。");
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <section className="page-shell"><p>正在加载智能配置…</p></section>;
  if (error && !draft) return <section className="page-shell"><p role="alert">{error}</p></section>;
  if (!draft) return <section className="page-shell"><p>尚无可配置的 Agent。</p></section>;

  const reasoningUnsupported = draft.deep_thinking_enabled && !draft.model_capability?.supports_reasoning;

  async function save() {
    if (!draft) return;
    if (reasoningUnsupported) {
      setError("当前模型不支持深度思考，请关闭开关或改绑支持推理的模型。");
      return;
    }
    setSaving(true);
    setError(null);
    setNotice(null);
    try {
      const { model_capability: _capability, ...payload } = draft;
      const saved = await saveAgentConfig(payload);
      setConfigs((items) => items.map((item) => item.agent_id === saved.agent_id ? saved : item));
      setDraft(saved);
      setNotice("配置已保存");
    } catch {
      setError("保存配置失败，请检查配置后重试。");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="config-page" aria-labelledby="page-heading">
      <div className="config-page__intro">
        <div><div className="page-shell__eyebrow">智能运维</div><h2 id="page-heading">智能配置</h2><p>每个 Agent 的配置彼此独立；保存只影响后续运行。</p></div>
      </div>
      <div className="config-layout">
        <div className="config-agent-list" aria-label="Agent 配置列表">
          {agentIds.map((agentId) => <button className={agentId === selectedId ? "config-agent config-agent--active" : "config-agent"} key={agentId} type="button" onClick={() => void select(agentId)}>{agentLabel(agentId)}</button>)}
        </div>
        <form className="config-form" onSubmit={(event) => { event.preventDefault(); void save(); }}>
          <h3>{agentLabel(draft.agent_id)}</h3>
          <p className="config-form__model">当前模型：{draft.model_capability?.display_name ?? "未绑定模型"}</p>
          <label><input type="checkbox" checked={draft.enabled} onChange={(event) => setDraft({ ...draft, enabled: event.target.checked })} /> 启用 Agent</label>
          <label><input aria-label="启用深度思考" type="checkbox" checked={draft.deep_thinking_enabled} onChange={(event) => { const next = { ...draft, deep_thinking_enabled: event.target.checked }; setDraft(next); if (!event.target.checked) setError(null); }} /> 启用深度思考</label>
          <label>上下文轮数<input aria-label="上下文轮数" type="number" min="0" max="10" value={draft.context_turns} onChange={(event) => setDraft({ ...draft, context_turns: Number(event.target.value) })} /></label>
          {reasoningUnsupported && <p role="alert">当前模型不支持深度思考，请关闭开关或改绑支持推理的模型。</p>}
          {error && <p role="alert">{error}</p>}
          {notice && <p role="status">{notice}</p>}
          <button type="submit" disabled={saving}>{saving ? "保存中…" : "保存配置"}</button>
        </form>
      </div>
    </section>
  );
}
