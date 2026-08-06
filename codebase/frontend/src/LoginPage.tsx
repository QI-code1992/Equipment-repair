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
    <section className="login-intro" aria-label="平台说明">
      <div className="login-intro__mark" aria-hidden="true">智</div>
      <p className="page-shell__eyebrow">现场运维 · 受控访问</p>
      <h1>新能源装载机智能运维平台</h1>
      <p>统一查看设备状态、处置故障、执行维修，并在权限范围内使用智能运维能力。</p>
      <ul><li>设备与组织数据由正式业务接口提供</li><li>智能任务、附件与维修结果均保留受控边界</li><li>请使用已分配的平台账号登录</li></ul>
    </section>
    <form className="login-form" onSubmit={(event) => void submit(event)}>
      <div className="page-shell__eyebrow">Fault Ops Console</div>
      <h2>欢迎回来</h2>
      <p className="login-form__hint">登录后将按账号权限展示可用业务页面。</p>
      <label>用户名<input aria-label="用户名" autoComplete="username" value={username} onChange={(event) => setUsername(event.target.value)} aria-invalid={Boolean(usernameError)} />{usernameError && <small>{usernameError}</small>}</label>
      <label>密码<div className="login-form__password"><input aria-label="密码" type={passwordVisible ? "text" : "password"} autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} aria-invalid={Boolean(passwordError)} /><button type="button" aria-label={passwordVisible ? "隐藏密码" : "显示密码"} onClick={() => setPasswordVisible((current) => !current)}>{passwordVisible ? "隐藏" : "显示"}</button></div>{passwordError && <small>{passwordError}</small>}</label>
      <div className="login-form__options"><label><input type="checkbox" defaultChecked />记住密码</label><button type="button" onClick={() => setForgotOpen(true)}>忘记密码</button></div>
      {error && <p role="alert">{error}</p>}
      {submitting && <p role="status" aria-label="登录状态">正在验证账号，请稍候…</p>}
      <button type="submit" disabled={submitting || lockedSeconds > 0}>{submitting ? "登录中…" : "登录系统"}</button>
      <p className="login-form__hint">连续失败 3 次后临时锁定，锁定 30 秒。</p>
    </form>
    {forgotOpen && <div className="login-modal" role="dialog" aria-modal="true" aria-label="忘记密码"><section><h3>忘记密码</h3><p>请联系系统管理员重置密码。</p><button type="button" onClick={() => setForgotOpen(false)}>知道了</button></section></div>}
  </main>;
}
