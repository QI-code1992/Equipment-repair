import { FormEvent, useEffect, useState } from "react";

import {
  ApiError,
  type AgentConfig,
  type ModelBinding,
  type ModelProvider,
  createModelBinding,
  createModelProvider,
  deleteModelBinding,
  deleteModelProvider,
  getAgentConfigs,
  getModelBindings,
  getModelProviders,
  saveAgentConfig,
  updateModelBinding,
  updateModelProvider,
  uploadKnowledgeDocument,
} from "./api";

const agentLabels: Record<string, string> = {
  fault_reporting: "AI 故障上报",
  metric_query: "智能问数",
  operation_guidance: "操作指引",
  fault_diagnosis: "故障诊断",
};

function agentLabel(agentId: string) {
  return agentLabels[agentId] ?? agentId;
}

function errorText(error: unknown) {
  return error instanceof ApiError ? error.code ?? "REQUEST_FAILED" : "REQUEST_FAILED";
}

export function IntelligentConfigPage({ permissionCodes = [] }: { permissionCodes?: string[] }) {
  const [configs, setConfigs] = useState<AgentConfig[]>([]);
  const [providers, setProviders] = useState<ModelProvider[]>([]);
  const [bindings, setBindings] = useState<ModelBinding[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [draft, setDraft] = useState<AgentConfig | null>(null);
  const [editingProvider, setEditingProvider] = useState<ModelProvider | null>(null);
  const [editingBinding, setEditingBinding] = useState<ModelBinding | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [knowledgeDatasetId, setKnowledgeDatasetId] = useState("");
  const [knowledgeUploading, setKnowledgeUploading] = useState(false);
  const [knowledgeTab, setKnowledgeTab] = useState<"params" | "upload">("params");
  const [activeTab, setActiveTab] = useState<"models" | "agents" | "knowledge" | "calls" | "tokens">("models");

  useEffect(() => {
    Promise.all([getAgentConfigs(), getModelProviders(), getModelBindings()])
      .then(([loadedConfigs, loadedProviders, loadedBindings]) => {
        setConfigs(loadedConfigs);
        setProviders(loadedProviders);
        setBindings(loadedBindings);
        const first = loadedConfigs.find((item) => item.agent_id === "fault_reporting") ?? loadedConfigs[0] ?? null;
        setSelectedId(first?.agent_id ?? null);
        setDraft(first);
      })
      .catch(() => setError("智能配置加载失败，请稍后重试。"))
      .finally(() => setLoading(false));
  }, []);

  function select(agentId: string) {
    const selected = configs.find((item) => item.agent_id === agentId) ?? null;
    setSelectedId(agentId);
    setDraft(selected);
    setError(null);
    setNotice(null);
  }

  async function save() {
    if (!draft) return;
    const binding = bindings.find((item) => item.id === draft.model_binding_id) ?? null;
    if (draft.deep_thinking_enabled && binding && !binding.supports_reasoning) {
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
      setNotice("Agent 配置已保存。");
    } catch (caught) {
      setError(`保存配置失败：${errorText(caught)}`);
    } finally {
      setSaving(false);
    }
  }

  async function addProvider(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setError(null);
    try {
      const created = await createModelProvider({ name: String(form.get("provider_name")), secret_ref: String(form.get("secret_ref")), enabled: true });
      setProviders((items) => [...items, created]);
      event.currentTarget.reset();
      setNotice("模型提供商已创建；密钥引用不会在页面回显。");
    } catch (caught) { setError(`创建模型提供商失败：${errorText(caught)}`); }
  }

  async function addBinding(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setError(null);
    try {
      const created = await createModelBinding({
        provider_id: String(form.get("provider_id")), name: String(form.get("binding_name")),
        model_name: String(form.get("model_name")), supports_reasoning: form.get("supports_reasoning") === "on", enabled: true,
      });
      setBindings((items) => [...items, created]);
      event.currentTarget.reset();
      setNotice("模型绑定已创建。");
    } catch (caught) { setError(`创建模型绑定失败：${errorText(caught)}`); }
  }

  async function removeProvider(id: string) {
    setError(null);
    try {
      await deleteModelProvider(id);
      setProviders((items) => items.filter((item) => item.id !== id));
      setNotice("模型提供商已删除。");
    } catch (caught) { setError(`删除模型提供商失败：${errorText(caught)}`); }
  }

  async function removeBinding(id: string) {
    setError(null);
    try {
      await deleteModelBinding(id);
      setBindings((items) => items.filter((item) => item.id !== id));
      setNotice("模型绑定已删除。");
    } catch (caught) { setError(`删除模型绑定失败：${errorText(caught)}`); }
  }

  async function saveProviderEdit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editingProvider) return;
    const form = new FormData(event.currentTarget);
    setError(null);
    try {
      const updated = await updateModelProvider(editingProvider.id, {
        name: String(form.get("provider_name")),
        secret_ref: String(form.get("secret_ref")),
        enabled: form.get("enabled") === "on",
      });
      setProviders((items) => items.map((item) => item.id === updated.id ? updated : item));
      setEditingProvider(null);
      setNotice("模型提供商已更新；密钥引用不会在页面回显。");
    } catch (caught) { setError(`更新模型提供商失败：${errorText(caught)}`); }
  }

  async function saveBindingEdit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editingBinding) return;
    const form = new FormData(event.currentTarget);
    setError(null);
    try {
      const updated = await updateModelBinding(editingBinding.id, {
        provider_id: String(form.get("provider_id")),
        name: String(form.get("binding_name")),
        model_name: String(form.get("model_name")),
        supports_reasoning: form.get("supports_reasoning") === "on",
        enabled: form.get("enabled") === "on",
      });
      setBindings((items) => items.map((item) => item.id === updated.id ? updated : item));
      setEditingBinding(null);
      setNotice("模型绑定已更新。");
    } catch (caught) { setError(`更新模型绑定失败：${errorText(caught)}`); }
  }

  async function uploadKnowledge(file: File | undefined) {
    if (!file || !knowledgeDatasetId.trim()) {
      setError("请先填写正式知识库 Dataset ID。");
      return;
    }
    setKnowledgeUploading(true);
    setError(null);
    try {
      await uploadKnowledgeDocument(knowledgeDatasetId.trim(), file);
      setNotice("知识文档已提交，后续状态由正式 Worker 更新。");
    } catch (caught) {
      setError(`知识文档上传失败：${errorText(caught)}`);
    } finally {
      setKnowledgeUploading(false);
    }
  }

  if (loading) return <section className="page-shell"><p role="status">正在加载智能配置…</p></section>;
  if (error && !draft) return <section className="page-shell"><p role="alert">{error}</p></section>;

  const selectedBinding = bindings.find((item) => item.id === draft?.model_binding_id) ?? null;
  const usableBindings = bindings.filter((item) => item.enabled && providers.some((provider) => provider.id === item.provider_id && provider.enabled));
  const reasoningUnsupported = Boolean(draft?.deep_thinking_enabled && selectedBinding && !selectedBinding.supports_reasoning);
  const canWriteKnowledge = permissionCodes.includes("intelligence:knowledge");

  return <section className="config-page" aria-labelledby="page-heading">
    <h2 id="page-heading" className="sr-only">智能配置</h2>
    {error && <p role="alert">{error}</p>}
    {notice && <p role="status">{notice}</p>}
    <div className="config-tabs" role="tablist" aria-label="智能配置中心一级页签">{[["models", "模型配置"], ["agents", "智能体配置"], ["knowledge", "知识库配置"], ["calls", "调用记录"], ["tokens", "Token 消耗统计"]].map(([id, label]) => <button key={id} type="button" role="tab" aria-selected={activeTab === id} aria-controls={`config-panel-${id}`} className={`config-tab ${activeTab === id ? "active" : ""}`} onClick={() => setActiveTab(id as typeof activeTab)}>{label}</button>)}</div>
    <section id="config-panel-models" className="config-panel" role="tabpanel" hidden={activeTab !== "models"} aria-label="模型配置"><section className="config-catalogue" aria-labelledby="catalogue-heading"><header><h3 id="catalogue-heading">模型与绑定</h3><p>提供商、模型绑定和 Agent 配置保持独立的正式管理边界。</p></header><section className="config-default-models" aria-label="默认模型资源"><article className="data-card config-default-model"><h3>默认 LLM</h3><p className="prototype-unavailable">当前 API 未提供默认资源绑定。</p></article><article className="data-card config-default-model"><h3>默认 Embedding</h3><p className="prototype-unavailable">当前 API 未提供默认资源绑定。</p></article><article className="data-card config-default-model"><h3>默认 Rerank</h3><p className="prototype-unavailable">当前 API 未提供默认资源绑定。</p></article></section><div className="config-catalogue__grid"><section className="data-card" aria-labelledby="provider-heading"><h3 id="provider-heading">模型提供商</h3>
      {providers.length ? <ul>{providers.map((provider) => <li key={provider.id}>{provider.name}（{provider.enabled ? "启用" : "停用"}） <button type="button" aria-label={`编辑模型提供商：${provider.name}`} onClick={() => setEditingProvider(provider)}>编辑</button> <button type="button" onClick={() => void removeProvider(provider.id)}>删除</button></li>)}</ul> : <p>暂无模型提供商。</p>}
      <form className="portal-form" onSubmit={addProvider}><label>提供商名称<input aria-label="提供商名称" name="provider_name" required /></label><label>密钥引用<input aria-label="密钥引用" name="secret_ref" required autoComplete="off" /></label><button type="submit">新增模型提供商</button></form>
      {editingProvider && <form className="portal-form" onSubmit={saveProviderEdit}><h4>编辑模型提供商</h4><label>提供商名称<input aria-label="编辑提供商名称" name="provider_name" defaultValue={editingProvider.name} required /></label><label>新的密钥引用<input aria-label="新的密钥引用" name="secret_ref" required autoComplete="off" /></label><label><input aria-label="启用编辑提供商" name="enabled" type="checkbox" defaultChecked={editingProvider.enabled} /> 启用提供商</label><button type="submit">保存模型提供商</button><button type="button" onClick={() => setEditingProvider(null)}>取消</button></form>}
    </section>
    <section className="data-card" aria-labelledby="binding-heading"><h3 id="binding-heading">模型绑定</h3>
      {bindings.length ? <ul>{bindings.map((binding) => <li key={binding.id}>{binding.name}（{binding.model_name}） · {binding.enabled ? "启用" : "停用"} <button type="button" aria-label={`编辑模型绑定：${binding.name}`} onClick={() => setEditingBinding(binding)}>编辑</button> <button type="button" onClick={() => void removeBinding(binding.id)}>删除</button></li>)}</ul> : <p>暂无模型绑定。</p>}
      <form className="portal-form" onSubmit={addBinding}><label>提供商<select name="provider_id" aria-label="绑定提供商" required defaultValue=""><option value="" disabled>请选择启用提供商</option>{providers.filter((provider) => provider.enabled).map((provider) => <option key={provider.id} value={provider.id}>{provider.name}</option>)}</select></label><label>绑定名称<input aria-label="绑定名称" name="binding_name" required /></label><label>模型名称<input aria-label="模型名称" name="model_name" required /></label><label><input name="supports_reasoning" type="checkbox" /> 支持深度思考</label><button type="submit" disabled={!providers.some((provider) => provider.enabled)}>新增模型绑定</button></form>
      {editingBinding && <form className="portal-form" onSubmit={saveBindingEdit}><h4>编辑模型绑定</h4><label>提供商<select aria-label="编辑绑定提供商" name="provider_id" defaultValue={editingBinding.provider_id} required>{providers.filter((provider) => provider.enabled).map((provider) => <option key={provider.id} value={provider.id}>{provider.name}</option>)}</select></label><label>绑定名称<input aria-label="编辑绑定名称" name="binding_name" defaultValue={editingBinding.name} required /></label><label>模型名称<input aria-label="编辑模型名称" name="model_name" defaultValue={editingBinding.model_name} required /></label><label><input aria-label="编辑绑定支持深度思考" name="supports_reasoning" type="checkbox" defaultChecked={editingBinding.supports_reasoning} /> 支持深度思考</label><label><input name="enabled" type="checkbox" defaultChecked={editingBinding.enabled} /> 启用模型绑定</label><button type="submit">保存模型绑定</button><button type="button" onClick={() => setEditingBinding(null)}>取消</button></form>}
    </section></div></section></section>
    <section id="config-panel-agents" className="config-panel" role="tabpanel" hidden={activeTab !== "agents"} aria-label="智能体配置"><section className="config-control-plane" aria-labelledby="agent-control-heading"><header><h3 id="agent-control-heading">Agent 控制面</h3><p>每个 Agent 仅使用自己的正式模型绑定与运行策略。</p></header><div className="config-layout"><div className="config-agent-list" aria-label="Agent 配置列表">{configs.map((config) => <button className={config.agent_id === selectedId ? "config-agent config-agent--active" : "config-agent"} key={config.agent_id} type="button" onClick={() => select(config.agent_id)}>{agentLabel(config.agent_id)}</button>)}</div>
      {draft ? <form className="config-form" onSubmit={(event) => { event.preventDefault(); void save(); }}><h3>{agentLabel(draft.agent_id)}</h3><p className="config-form__model">当前模型：{selectedBinding ? `${selectedBinding.name}（${selectedBinding.model_name}）` : "未绑定模型"}</p><label>模型绑定<select aria-label="Agent 模型绑定" value={draft.model_binding_id ?? ""} onChange={(event) => setDraft({ ...draft, model_binding_id: event.target.value || null })}><option value="">未绑定模型</option>{usableBindings.map((binding) => <option key={binding.id} value={binding.id}>{binding.name}（{binding.model_name}）</option>)}</select></label><label><input type="checkbox" checked={draft.enabled} onChange={(event) => setDraft({ ...draft, enabled: event.target.checked })} /> 启用 Agent</label><label><input aria-label="启用深度思考" type="checkbox" checked={draft.deep_thinking_enabled} onChange={(event) => setDraft({ ...draft, deep_thinking_enabled: event.target.checked })} /> 启用深度思考</label>{reasoningUnsupported && <p role="alert">当前模型不支持深度思考，请关闭开关或改绑支持推理的模型。</p>}<label>上下文轮数<input aria-label="上下文轮数" type="number" min="0" max="10" value={draft.context_turns} onChange={(event) => setDraft({ ...draft, context_turns: Number(event.target.value) })} /></label><button type="submit" disabled={saving || reasoningUnsupported}>{saving ? "保存中…" : "保存 Agent 配置"}</button></form> : <p>尚无可配置的 Agent。</p>}
    </div></section></section>
    <section id="config-panel-knowledge" className="config-panel" role="tabpanel" hidden={activeTab !== "knowledge"} aria-label="知识库配置"><div className="config-subtabs" role="tablist" aria-label="知识库配置二级页签"><button type="button" role="tab" aria-selected={knowledgeTab === "params"} onClick={() => setKnowledgeTab("params")}>知识库参数</button><button type="button" role="tab" aria-selected={knowledgeTab === "upload"} onClick={() => setKnowledgeTab("upload")}>知识上传</button></div>{knowledgeTab === "params" ? <section className="data-card" aria-labelledby="knowledge-params-heading"><h3 id="knowledge-params-heading">知识库参数</h3><p className="prototype-unavailable">当前 API 未提供知识库参数、解析策略和混合检索配置接口。</p></section> : <section className="data-card" aria-labelledby="knowledge-heading"><h3 id="knowledge-heading">知识文档入口</h3><p>仅提交安全扫描后的正式文档引用；页面不显示对象键、扫描内部细节或正文。</p>{!canWriteKnowledge && <p role="status">当前账号没有知识库写入权限。</p>}<label>正式 Dataset ID<input aria-label="正式 Dataset ID" disabled={!canWriteKnowledge} value={knowledgeDatasetId} onChange={(event) => setKnowledgeDatasetId(event.target.value)} /></label><label>上传知识文档<input aria-label="上传知识文档" type="file" disabled={!canWriteKnowledge || knowledgeUploading} onChange={(event) => void uploadKnowledge(event.target.files?.[0])} /></label>{knowledgeUploading && <p role="status">正在上传并扫描知识文档…</p>}</section>}</section>
    <section id="config-panel-calls" className="config-panel" role="tabpanel" hidden={activeTab !== "calls"} aria-label="调用记录"><section className="data-card"><header className="section-heading"><div><h3>Agent 调用记录</h3><p>记录 Agent 调用及其知识库、模型调用情况。</p></div><span className="status-chip status-chip--neutral">当前 API 未提供</span></header><table className="config-report-table"><thead><tr><th>调用时间</th><th>调用类型</th><th>调用对象</th><th>触发入口</th><th>状态</th><th>耗时</th><th>Token 消耗</th><th>用户</th><th>操作</th></tr></thead><tbody><tr><td colSpan={9} className="prototype-unavailable">当前 API 未提供调用记录数据。</td></tr></tbody></table></section></section>
    <section id="config-panel-tokens" className="config-panel" role="tabpanel" hidden={activeTab !== "tokens"} aria-label="Token 消耗统计"><section className="config-token-grid"><article className="data-card"><header className="section-heading"><h3>Token 趋势</h3><span className="status-chip status-chip--info">按天统计</span></header><p className="prototype-unavailable">当前 API 未提供 Token 趋势数据。</p></article><article className="data-card"><header className="section-heading"><h3>异常消耗提醒</h3><span className="status-chip status-chip--warning">需关注</span></header><p className="prototype-unavailable">当前 API 未提供异常消耗提醒。</p></article><article className="data-card"><header className="section-heading"><h3>模型消耗分析</h3><span className="status-chip status-chip--neutral">按资源类型</span></header><p className="prototype-unavailable">当前 API 未提供模型消耗分析。</p></article><article className="data-card"><header className="section-heading"><h3>Agent 消耗分析</h3><span className="status-chip status-chip--info">按 Token</span></header><p className="prototype-unavailable">当前 API 未提供 Agent 消耗分析。</p></article></section><section className="data-card"><header className="section-heading"><div><h3>Token 明细</h3><p>费用无价格配置时不估算。</p></div><span className="status-chip status-chip--warning">无价格时费用不估算</span></header><table className="config-report-table"><thead><tr><th>时间</th><th>Agent</th><th>模型/服务</th><th>用户</th><th>输入 Token</th><th>输出 Token</th><th>Embedding Token</th><th>Rerank 调用次数</th><th>费用估算</th><th>关联调用记录</th></tr></thead><tbody><tr><td colSpan={10} className="prototype-unavailable">当前 API 未提供 Token 明细数据。</td></tr></tbody></table></section></section>
  </section>;
}
