import { FormEvent, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { ApiError, login } from "./api";

type LoginLocationState = { from?: string };

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [forgotOpen, setForgotOpen] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(username, password);
      const state = location.state as LoginLocationState | null;
      navigate(state?.from ?? "/", { replace: true });
    } catch (caught) {
      setError(caught instanceof ApiError && caught.status === 401 ? "账号或密码错误。" : "登录暂不可用，请稍后重试。");
    } finally {
      setSubmitting(false);
    }
  }

  return <main className="login-page"><div className="login-page__grid" aria-hidden="true" /><div className="login-page__beam" aria-hidden="true" />
    <div className="login-page__content">
      <section className="login-intro" aria-label="平台说明">
        <div className="login-intro__badge"><span aria-hidden="true">✦</span><span>新能源装载机设备故障智能运维平台</span></div>
        <h1>设备AI智能运维平台</h1>
        <p>面向工厂、车间、产线的设备故障智能运维演示系统，融合台账、诊断、工单与 Agent 辅助闭环。</p>
        <div className="login-features"><article><strong>24h</strong><span>故障追踪</span></article><article><strong>AI</strong><span>诊断辅助</span></article><article><strong>RAG</strong><span>知识检索</span></article><article><strong>KG</strong><span>知识图谱</span></article><article><strong>BI</strong><span>驾驶舱分析</span></article><article><strong>闭环</strong><span>工单协同</span></article></div>
      </section>
      <form className="login-form" onSubmit={(event) => void submit(event)}>
        <header><h2>登录</h2><p>请输入账号密码进行登录</p></header>
        {error && <p className="login-error" role="alert">{error}</p>}
        <label>账号<div className="login-field"><span aria-hidden="true">●</span><input aria-label="用户名" autoComplete="username" value={username} onChange={(event) => setUsername(event.target.value)} placeholder="请输入账号" required /></div></label>
        <label>密码<div className="login-field"><span aria-hidden="true">▣</span><input aria-label="密码" type={showPassword ? "text" : "password"} autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="请输入密码" required /><button type="button" aria-label={showPassword ? "隐藏密码" : "显示密码"} onClick={() => setShowPassword((visible) => !visible)}>{showPassword ? "◉" : "◌"}</button></div></label>
        <div className="login-options"><label><input type="checkbox" checked={remember} onChange={(event) => setRemember(event.target.checked)} />记住密码</label><button type="button" className="login-forgot" onClick={() => setForgotOpen(true)}>忘记密码</button></div>
        <button className="login-submit" aria-label="登录系统" type="submit" disabled={submitting}>{submitting ? "登录中…" : "登录"}</button>
        <p className="login-lock-hint">连续失败 3 次后临时锁定，锁定30s。</p>
      </form>
    </div>
    {forgotOpen && <div className="modal-scrim" role="presentation"><section className="modal-card" role="dialog" aria-modal="true" aria-labelledby="forgot-password-heading"><header><h2 id="forgot-password-heading">忘记密码</h2><button type="button" aria-label="关闭" onClick={() => setForgotOpen(false)}>×</button></header><p>请联系平台管理员重置账号密码，平台不会通过页面回显或发送密码。</p><button type="button" className="button-primary" onClick={() => setForgotOpen(false)}>知道了</button></section></div>}
  </main>;
}
