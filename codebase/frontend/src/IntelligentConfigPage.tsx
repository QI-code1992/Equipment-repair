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
  const [activePanel, setActivePanel] = useState<"models" | "agents" | "knowledge" | "calls" | "tokens">("models");
  const [modelTypeFilter, setModelTypeFilter] = useState<"all" | "LLM" | "Embedding" | "Rerank">("all");
  const [providerFilter, setProviderFilter] = useState("all");
  const [modelEditorOpen, setModelEditorOpen] = useState(false);

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
  const visibleBindings = bindings.filter((binding) => providerFilter === "all" || binding.provider_id === providerFilter).filter(() => modelTypeFilter === "all");
  const providerName = (providerId: string) => providers.find((provider) => provider.id === providerId)?.name ?? "未提供";

  return <section className="config-page">
    {error && <p role="alert">{error}</p>}
    {notice && <p role="status">{notice}</p>}
    <nav className="config-tabs" role="tablist" aria-label="智能配置中心一级页签">{[["models", "模型配置"], ["agents", "智能体配置"], ["knowledge", "知识库配置"], ["calls", "调用记录"], ["tokens", "Token 消耗统计"]].map(([id, label]) => <button key={id} className={activePanel === id ? "config-tab is-active" : "config-tab"} type="button" role="tab" aria-selected={activePanel === id} onClick={() => setActivePanel(id as typeof activePanel)}>{label}</button>)}</nav>
    {activePanel === "models" && <section className="config-model-workspace" role="tabpanel" aria-label="模型配置" aria-labelledby="catalogue-heading">
      <header className="config-toolbar"><div><h3 id="catalogue-heading">模型配置</h3><p>维护 LLM、Embedding、Rerank 模型资源；测试连接可选，不影响启用。</p></div><button className="button-primary" type="button" onClick={() => { setEditingProvider(null); setEditingBinding(null); setModelEditorOpen(true); }}>新增模型</button></header>
      <div className="config-card-grid config-card-grid--three">
        {["LLM", "Embedding", "Rerank"].map((type) => <article className="model-card is-default" key={type}><div className="card-head"><div><h3>默认 {type}</h3><p>未提供默认模型配置</p></div><span className="config-status">未提供</span></div><div className="card-kv"><div><span>供应商 provider</span><strong>未提供</strong></div><div><span>调用模型</span><strong>未提供</strong></div><div><span>Token 单价</span><strong>未提供</strong></div></div></article>)}
      </div>
      <section className="config-toolbar config-filter-toolbar" aria-label="模型资源筛选"><div className="filter-row"><button className={modelTypeFilter === "all" ? "seg-btn is-active" : "seg-btn"} type="button" onClick={() => setModelTypeFilter("all")}>全部</button>{["LLM", "Embedding", "Rerank"].map((type) => <button key={type} className={modelTypeFilter === type ? "seg-btn is-active" : "seg-btn"} type="button" onClick={() => setModelTypeFilter(type as typeof modelTypeFilter)}>{type}</button>)}<select aria-label="按提供商筛选模型" value={providerFilter} onChange={(event) => setProviderFilter(event.target.value)}><option value="all">全部供应商</option>{providers.map((provider) => <option value={provider.id} key={provider.id}>{provider.name}</option>)}</select></div></section>
      <div className="config-card-grid config-card-grid--models">{visibleBindings.length ? visibleBindings.map((binding) => <article className="model-card" key={binding.id}><div className="card-head"><div><h4>{binding.name}</h4><p>模型类型 · 未提供；provider {providerName(binding.provider_id)}</p></div><span className={binding.enabled ? "config-status config-status--ok" : "config-status config-status--warn"}>{binding.enabled ? "启用" : "停用"}</span></div><div className="card-kv"><div><span>调用模型</span><strong>{binding.model_name}</strong></div><div><span>接口地址 api_base_url</span><strong>未提供</strong></div><div><span>价格</span><strong>未提供</strong></div></div><div className="config-actions"><button type="button" onClick={() => { setEditingBinding(binding); setEditingProvider(null); setModelEditorOpen(true); }} aria-label={`编辑模型绑定：${binding.name}`}>编辑</button><button type="button" disabled title="正式 API 未提供默认模型设置">设为默认</button><button type="button" disabled title="正式 API 未提供模型连接测试">测试连接</button><button type="button" onClick={() => void removeBinding(binding.id)}>删除</button></div></article>) : <p className="config-empty">暂无符合筛选条件的模型资源。</p>}</div>
      {modelEditorOpen && <aside className="model-editor" aria-label="模型编辑抽屉">
        <header>
          <div><h3>{editingProvider ? "编辑模型提供商" : editingBinding ? `编辑模型：${editingBinding.name}` : "新增模型"}</h3><p>密钥仅以安全引用提交，不会在页面回显。</p></div>
          <button type="button" aria-label="关闭模型编辑" onClick={() => { setModelEditorOpen(false); setEditingProvider(null); setEditingBinding(null); }}>关闭</button>
        </header>
        <div className="model-editor__body">
          <section className="model-editor__section">
            <div className="model-editor__section-heading"><span>1</span><div><h4>选择模型</h4><p>选择已启用提供商，并填写模型在平台中的显示名称。</p></div></div>
            {editingBinding ? <form className="portal-form model-editor__form" onSubmit={saveBindingEdit}>
              <label>提供商<select aria-label="编辑绑定提供商" name="provider_id" defaultValue={editingBinding.provider_id} required>{providers.filter((provider) => provider.enabled).map((provider) => <option key={provider.id} value={provider.id}>{provider.name}</option>)}</select></label>
              <label>绑定名称<input aria-label="编辑绑定名称" name="binding_name" defaultValue={editingBinding.name} required /></label>
              <label>模型名称<input aria-label="编辑模型名称" name="model_name" defaultValue={editingBinding.model_name} required /></label>
              <label className="model-editor__check"><input aria-label="编辑绑定支持深度思考" name="supports_reasoning" type="checkbox" defaultChecked={editingBinding.supports_reasoning} /> 支持深度思考</label>
              <label className="model-editor__check"><input name="enabled" type="checkbox" defaultChecked={editingBinding.enabled} /> 启用模型绑定</label>
              <div className="model-editor__actions"><button type="submit">保存模型绑定</button><button type="button" onClick={() => setEditingBinding(null)}>取消</button></div>
            </form> : <form className="portal-form model-editor__form" onSubmit={addBinding}>
              <label>提供商<select name="provider_id" aria-label="绑定提供商" required defaultValue=""><option value="" disabled>请选择启用提供商</option>{providers.filter((provider) => provider.enabled).map((provider) => <option key={provider.id} value={provider.id}>{provider.name}</option>)}</select></label>
              <label>绑定名称<input aria-label="绑定名称" name="binding_name" required /></label>
              <label>模型名称<input aria-label="模型名称" name="model_name" required /></label>
              <label className="model-editor__check"><input name="supports_reasoning" type="checkbox" /> 支持深度思考</label>
              <div className="model-editor__actions"><button type="submit" disabled={!providers.some((provider) => provider.enabled)}>新增模型绑定</button><button type="button" disabled title="正式 API 未提供供应商模型目录">获取模型列表</button></div>
            </form>}
          </section>
          <section className="model-editor__section">
            <div className="model-editor__section-heading"><span>2</span><div><h4>连接配置</h4><p>创建或更新模型提供商的安全密钥引用。</p></div></div>
            {editingProvider ? <form className="portal-form model-editor__form" onSubmit={saveProviderEdit}>
              <label>提供商名称<input aria-label="编辑提供商名称" name="provider_name" defaultValue={editingProvider.name} required /></label>
              <label>新的密钥引用<input aria-label="新的密钥引用" name="secret_ref" required autoComplete="off" /></label>
              <label className="model-editor__check"><input aria-label="启用编辑提供商" name="enabled" type="checkbox" defaultChecked={editingProvider.enabled} /> 启用提供商</label>
              <div className="model-editor__actions"><button type="submit">保存模型提供商</button><button type="button" onClick={() => setEditingProvider(null)}>取消</button></div>
            </form> : <form className="portal-form model-editor__form" onSubmit={addProvider}>
              <label>提供商名称<input aria-label="提供商名称" name="provider_name" required /></label>
              <label>密钥引用<input aria-label="密钥引用" name="secret_ref" required autoComplete="off" /></label>
              <div className="model-editor__actions"><button type="submit">新增模型提供商</button><button type="button" disabled title="正式 API 未提供模型连接测试">测试连接</button></div>
            </form>}
            {providers.length > 0 && <div className="provider-actions">{providers.map((provider) => <button type="button" key={provider.id} aria-label={`编辑模型提供商：${provider.name}`} onClick={() => { setEditingProvider(provider); setEditingBinding(null); }}>{provider.name}</button>)}</div>}
          </section>
          <section className="model-editor__section model-editor__section--settings">
            <div className="model-editor__section-heading"><span>3</span><div><h4>使用设置</h4><p>默认模型、价格和连接校验均须由正式模型目录接口提供。</p></div></div>
            <div className="model-editor__unavailable"><strong>当前可用性</strong><span>正式 API 未提供默认模型、价格或连接测试配置。</span><button type="button" disabled title="正式 API 未提供默认模型设置">设为默认</button></div>
          </section>
        </div>
      </aside>}
    </section>}
    {activePanel === "knowledge" && <section className="data-card config-knowledge-panel" role="tabpanel" aria-label="知识库配置" aria-labelledby="knowledge-heading"><h3 id="knowledge-heading">知识文档入口</h3><p>仅提交安全扫描后的正式文档引用；页面不显示对象键、扫描内部细节或正文。</p>{!canWriteKnowledge && <p role="status">当前账号没有知识库写入权限。</p>}<label>正式 Dataset ID<input aria-label="正式 Dataset ID" disabled={!canWriteKnowledge} value={knowledgeDatasetId} onChange={(event) => setKnowledgeDatasetId(event.target.value)} /></label><label>上传知识文档<input aria-label="上传知识文档" type="file" disabled={!canWriteKnowledge || knowledgeUploading} onChange={(event) => void uploadKnowledge(event.target.files?.[0])} /></label>{knowledgeUploading && <p role="status">正在上传并扫描知识文档…</p>}</section>}
    {activePanel === "agents" && <section className="config-control-plane" role="tabpanel" aria-label="智能体配置" aria-labelledby="agent-control-heading"><header><h3 id="agent-control-heading">Agent 控制面</h3><p>每个 Agent 仅使用自己的正式模型绑定与运行策略。</p></header><div className="config-layout"><div className="config-agent-list" aria-label="Agent 配置列表">{configs.map((config) => <button className={config.agent_id === selectedId ? "config-agent config-agent--active" : "config-agent"} key={config.agent_id} type="button" onClick={() => select(config.agent_id)}>{agentLabel(config.agent_id)}</button>)}</div>
      {draft ? <form className="config-form" onSubmit={(event) => { event.preventDefault(); void save(); }}><h3>{agentLabel(draft.agent_id)}</h3><p className="config-form__model">当前模型：{selectedBinding ? `${selectedBinding.name}（${selectedBinding.model_name}）` : "未绑定模型"}</p><label>模型绑定<select aria-label="Agent 模型绑定" value={draft.model_binding_id ?? ""} onChange={(event) => setDraft({ ...draft, model_binding_id: event.target.value || null })}><option value="">未绑定模型</option>{usableBindings.map((binding) => <option key={binding.id} value={binding.id}>{binding.name}（{binding.model_name}）</option>)}</select></label><label><input type="checkbox" checked={draft.enabled} onChange={(event) => setDraft({ ...draft, enabled: event.target.checked })} /> 启用 Agent</label><label><input aria-label="启用深度思考" type="checkbox" checked={draft.deep_thinking_enabled} onChange={(event) => setDraft({ ...draft, deep_thinking_enabled: event.target.checked })} /> 启用深度思考</label>{reasoningUnsupported && <p role="alert">当前模型不支持深度思考，请关闭开关或改绑支持推理的模型。</p>}<label>上下文轮数<input aria-label="上下文轮数" type="number" min="0" max="10" value={draft.context_turns} onChange={(event) => setDraft({ ...draft, context_turns: Number(event.target.value) })} /></label><button type="submit" disabled={saving || reasoningUnsupported}>{saving ? "保存中…" : "保存 Agent 配置"}</button></form> : <p>尚无可配置的 Agent。</p>}
    </div></section>}
    {activePanel === "calls" && <section className="config-reference-panel" role="tabpanel" aria-label="调用记录"><h3>调用记录</h3><p>调用状态、保留期和配置 Token 预算由正式审计接口提供。</p><a className="button-primary" href="/intelligence-audit">查看正式调用审计</a></section>}
    {activePanel === "tokens" && <section className="config-reference-panel" role="tabpanel" aria-label="Token 消耗统计"><h3>Token 消耗统计</h3><p>当前正式接口仅提供受控调用记录及配置 Token 预算，未提供可用于图表统计的实际 Token 消耗明细。</p><a className="button-primary" href="/intelligence-audit">查看正式调用审计</a></section>}
  </section>;
}
