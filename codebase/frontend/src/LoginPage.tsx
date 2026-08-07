import { FormEvent, useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { ApiError, login } from "./api";

type LoginLocationState = { from?: string };

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [usernameError, setUsernameError] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [failureCount, setFailureCount] = useState(0);
  const [lockedSeconds, setLockedSeconds] = useState(0);
  const [passwordVisible, setPasswordVisible] = useState(false);
  const [forgotOpen, setForgotOpen] = useState(false);
  const [browserPasswordManagerEnabled, setBrowserPasswordManagerEnabled] = useState(true);

  useEffect(() => {
    if (lockedSeconds <= 0) return;
    const timer = window.setInterval(() => {
      setLockedSeconds((current) => Math.max(0, current - 1));
    }, 1000);
    return () => window.clearInterval(timer);
  }, [lockedSeconds > 0]);

  useEffect(() => {
    if (lockedSeconds === 0 && failureCount >= 3) {
      setFailureCount(0);
      setError("账号锁定已解除，请重新登录。");
    }
  }, [failureCount, lockedSeconds]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextUsernameError = username.trim() ? null : "请输入账号。";
    const nextPasswordError = password ? null : "请输入密码。";
    setUsernameError(nextUsernameError);
    setPasswordError(nextPasswordError);
    if (nextUsernameError || nextPasswordError || submitting || lockedSeconds > 0) return;
    setError(null);
    setSubmitting(true);
    try {
      await login(username, password);
      const state = location.state as LoginLocationState | null;
      navigate(state?.from ?? "/", { replace: true });
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 401) {
        const nextFailureCount = failureCount + 1;
        setFailureCount(nextFailureCount);
        if (nextFailureCount >= 3) {
          setLockedSeconds(30);
          setError("账号已临时锁定，请 30s 后再试。");
        } else setError(`账号或密码错误，剩余 ${3 - nextFailureCount} 次机会。`);
      } else setError("登录暂不可用，请稍后重试。");
    } finally {
      setSubmitting(false);
    }
  }

  return <main className="login-page">
    <div className="login-page__gridline" aria-hidden="true" />
    <div className="login-page__beam" aria-hidden="true" />
    <section className="login-intro" aria-label="平台说明">
      <p className="login-intro__badge"><span aria-hidden="true">✦</span>新能源装载机设备故障智能运维平台</p>
      <h1>设备AI智能运维平台</h1>
      <p>面向工厂、车间、产线的设备故障智能运维系统，融合台账、诊断、工单与 Agent 辅助闭环。</p>
      <div className="login-feature-grid" aria-label="平台能力"><article><strong>24h</strong><span>故障追踪</span></article><article><strong>AI</strong><span>诊断辅助</span></article><article><strong>RAG</strong><span>知识检索</span></article><article><strong>KG</strong><span>知识图谱</span></article><article><strong>BI</strong><span>驾驶舱分析</span></article><article><strong>闭环</strong><span>工单协同</span></article></div>
    </section>
    <form className="login-form" onSubmit={(event) => void submit(event)}>
      <h2>登录</h2>
      <p className="login-form__hint">请输入账号密码进行登录</p>
      <label>账号<div className="login-form__field"><span className="login-form__field-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="3.5" /><path d="M4.5 20c.8-4 3.3-6 7.5-6s6.7 2 7.5 6" /></svg></span><input aria-label="用户名" name="username" autoComplete="username" value={username} onChange={(event) => setUsername(event.target.value)} aria-invalid={Boolean(usernameError)} placeholder="请输入账号" /></div>{usernameError && <small>{usernameError}</small>}</label>
      <label>密码<div className="login-form__field login-form__password"><span className="login-form__field-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><rect x="5" y="10" width="14" height="10" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3" /></svg></span><input aria-label="密码" name="password" type={passwordVisible ? "text" : "password"} autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} aria-invalid={Boolean(passwordError)} /><button type="button" className="login-form__password-toggle" aria-label={passwordVisible ? "隐藏密码" : "显示密码"} onClick={() => setPasswordVisible((current) => !current)}><svg aria-hidden="true" viewBox="0 0 24 24"><path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z" /><circle cx="12" cy="12" r="2.8" />{passwordVisible && <path d="m4 4 16 16" />}</svg></button></div>{passwordError && <small>{passwordError}</small>}</label>
      <div className="login-form__options"><label><input type="checkbox" checked={browserPasswordManagerEnabled} onChange={(event) => setBrowserPasswordManagerEnabled(event.target.checked)} />记住密码</label><button type="button" onClick={() => setForgotOpen(true)}>忘记密码</button></div>
      {error && <p role="alert">{error}</p>}
      {submitting && <p role="status" aria-label="登录状态">正在验证账号，请稍候…</p>}
      <button type="submit" disabled={submitting || lockedSeconds > 0}>{submitting ? "登录中…" : "登录"}</button>
      <p className="login-form__hint">连续失败 3 次后临时锁定，锁定 30 秒。</p>
    </form>
    {forgotOpen && <div className="login-modal" role="dialog" aria-modal="true" aria-label="忘记密码"><section><h3>忘记密码</h3><p>请联系系统管理员重置密码。管理员可在系统管理中启用账号并重置初始密码。</p><button type="button" className="login-modal__confirm" onClick={() => setForgotOpen(false)}>知道了</button></section></div>}
  </main>;
}
