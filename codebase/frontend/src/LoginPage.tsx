import { FormEvent, useState } from "react";
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
      <label>用户名<input aria-label="用户名" autoComplete="username" value={username} onChange={(event) => setUsername(event.target.value)} required /></label>
      <label>密码<input aria-label="密码" type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} required /></label>
      {error && <p role="alert">{error}</p>}
      <button type="submit" disabled={submitting}>{submitting ? "登录中…" : "登录系统"}</button>
      <button type="button" className="login-forgot" onClick={() => setForgotOpen(true)}>忘记密码</button>
    </form>
    {forgotOpen && <div className="modal-scrim" role="presentation"><section className="modal-card" role="dialog" aria-modal="true" aria-labelledby="forgot-password-heading"><header><h2 id="forgot-password-heading">忘记密码</h2><button type="button" aria-label="关闭" onClick={() => setForgotOpen(false)}>×</button></header><p>请联系平台管理员重置账号密码，平台不会通过页面回显或发送密码。</p><button type="button" className="button-primary" onClick={() => setForgotOpen(false)}>知道了</button></section></div>}
  </main>;
}
