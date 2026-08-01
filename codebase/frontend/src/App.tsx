import { FormEvent, useEffect, useMemo, useState } from "react";
import { Navigate, NavLink, Route, Routes, useLocation, useNavigate } from "react-router-dom";

import { IntelligentConfigPage } from "./IntelligentConfigPage";
import { FaultReportPage } from "./FaultReportPage";
import { RepairExecutionPage } from "./RepairExecutionPage";
import { WorkbenchPage } from "./WorkbenchPage";
import { ApiError, clearActiveSession, getAgentThread, getAgentThreads, getCurrentUser, hasActiveSession, logout, readRunEvents, resumeAgentThread, startAgentRun, type AgentThread, type AgentThreadSummary, type RuntimeEvent } from "./api";
import { LoginPage } from "./LoginPage";
import { AgentReportPage, BiDashboardPage, EquipmentAddPage, EquipmentDetailPage, EquipmentEditPage, EquipmentLedgerPage, FactoryModelingPage, IntelligentAuditPage, MaintenanceRecordDetailPage, MaintenanceRecordsPage, SystemManagementPage } from "./PortalPages";

type Page = {
  path: string;
  label: string;
  group: string;
  mark: string;
};

const pages: Page[] = [
  { path: "/", label: "运维工作台", group: "工作台", mark: "台" },
  { path: "/bi-dashboard", label: "驾驶舱 BI", group: "工作台", mark: "BI" },
  { path: "/factory-modeling", label: "工厂建模", group: "资产管理", mark: "厂" },
  { path: "/equipment", label: "设备台账", group: "资产管理", mark: "设" },
  { path: "/intelligent-config", label: "智能配置", group: "智能运维", mark: "智" },
  { path: "/intelligence-audit", label: "智能审计", group: "智能运维", mark: "审" },
  { path: "/fault-report", label: "故障上报", group: "现场作业", mark: "报" },
  { path: "/agent-report", label: "AI 故障上报", group: "现场作业", mark: "AI" },
  { path: "/maintenance-records", label: "维修记录", group: "现场作业", mark: "记" },
  { path: "/repair-execution", label: "维修执行", group: "现场作业", mark: "修" },
  { path: "/system-management", label: "系统管理", group: "系统管理", mark: "管" },
];

function PageShell({ label }: { label: string }) {
  return (
    <section className="page-shell" aria-labelledby="page-heading">
      <div className="page-shell__eyebrow">正式前端基础</div>
      <h2 id="page-heading">{label}</h2>
      <p>业务内容将在对应任务中接入</p>
    </section>
  );
}

function RequireAuthentication({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  if (!hasActiveSession()) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  return children;
}

function ApplicationShell() {
  const location = useLocation();
  const navigate = useNavigate();
  const [agentOpen, setAgentOpen] = useState(false);
  const [permissionCodes, setPermissionCodes] = useState<string[] | null>(null);
  const [permissionError, setPermissionError] = useState<string | null>(null);
  const [authFailed, setAuthFailed] = useState(false);
  useEffect(() => {
    getCurrentUser().then((user) => setPermissionCodes(user.permission_codes)).catch(() => {
      clearActiveSession();
      setPermissionError("当前会话权限加载失败，请重新登录。");
      setAuthFailed(true);
    });
  }, []);
  const activePage = pages.find((page) => page.path === location.pathname) ?? pages[0];
  const visiblePages = useMemo(() => permissionCodes === null ? [] : pages.filter((page) => pagePermission(page.path, permissionCodes)), [permissionCodes]);
  const groups = [...new Set(visiblePages.map((page) => page.group))];
  function guarded(path: string, element: React.ReactNode) {
    if (permissionCodes === null || permissionError) return element;
    return pagePermission(path, permissionCodes) ? element : <section className="page-shell"><p role="alert">你没有访问此页面的权限。</p></section>;
  }
  if (authFailed) return <LoginPage />;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand__mark" aria-hidden="true">运</div>
          <div>
            <strong>设备智能运维平台</strong>
            <span>新能源装载机</span>
          </div>
        </div>

        <nav aria-label="主导航">
          {permissionError && <p role="alert">{permissionError}</p>}
          {groups.map((group) => (
            <div className="nav-group" key={group}>
              <div className="nav-group__label">{group}</div>
              {visiblePages.filter((page) => page.group === group).map((page) => (
                <NavLink className="nav-item" key={page.path} to={page.path} end={page.path === "/"}>
                  <span aria-hidden="true">{page.mark}</span>
                  {page.label}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>

        <div className="sidebar__footer">
          <strong>平台状态</strong>
          <span>前端基础工程已启用</span>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div>
            <p>设备智能运维平台 / {activePage.group}</p>
            <h1>设备智能运维平台</h1>
          </div>
          <div className="topbar__actions">{permissionCodes?.includes("intelligence:agent") && <button type="button" className="agent-trigger" onClick={() => setAgentOpen(true)}>全局 Agent</button>}<button type="button" className="agent-trigger" onClick={() => void logout().finally(() => navigate("/login", { replace: true }))}>退出</button><div className="topbar__avatar" aria-label="当前用户">管</div></div>
        </header>
        {permissionCodes === null && !permissionError ? <section className="page-shell" aria-live="polite"><p role="status">正在加载会话权限…</p></section> : <Routes>
          <Route path="/" element={guarded("/", <WorkbenchPage />)} />
          <Route path="/bi-dashboard" element={guarded("/bi-dashboard", <BiDashboardPage />)} />
          <Route path="/factory-modeling" element={guarded("/factory-modeling", <FactoryModelingPage />)} />
          <Route path="/equipment" element={guarded("/equipment", <EquipmentLedgerPage />)} />
          <Route path="/equipment/new" element={guarded("/equipment/new", <EquipmentAddPage />)} />
          <Route path="/equipment/:id" element={guarded("/equipment/:id", <EquipmentDetailPage />)} />
          <Route path="/equipment/:id/edit" element={guarded("/equipment/:id/edit", <EquipmentEditPage />)} />
          <Route path="/intelligent-config" element={guarded("/intelligent-config", <IntelligentConfigPage />)} />
          <Route path="/intelligence-audit" element={guarded("/intelligence-audit", <IntelligentAuditPage permissionCodes={permissionCodes ?? []} />)} />
          <Route path="/fault-report" element={guarded("/fault-report", <FaultReportPage />)} />
          <Route path="/agent-report" element={guarded("/agent-report", <AgentReportPage />)} />
          <Route path="/maintenance-records" element={guarded("/maintenance-records", <MaintenanceRecordsPage />)} />
          <Route path="/maintenance-records/:id" element={guarded("/maintenance-records/:id", <MaintenanceRecordDetailPage />)} />
          <Route path="/repair-execution" element={guarded("/repair-execution", <RepairExecutionPage />)} />
          <Route path="/system-management" element={guarded("/system-management", <SystemManagementPage />)} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>}
        {agentOpen && permissionCodes?.includes("intelligence:agent") && <GlobalAgentDrawer onClose={() => setAgentOpen(false)} />}
      </main>
    </div>
  );
}

function pagePermission(path: string, codes: string[]) {
  const required: Record<string, string[]> = {
    "/": ["workbench:view"],
    "/bi-dashboard": ["bi:view"],
    "/factory-modeling": ["organization:read", "organization:write"],
    "/equipment": ["equipment:read"],
    "/equipment/new": ["equipment:read", "equipment:write", "organization:read", "identity:read"],
    "/equipment/:id": ["equipment:read"],
    "/equipment/:id/edit": ["equipment:read", "equipment:write", "organization:read", "identity:read"],
    "/intelligent-config": ["intelligence:model", "intelligence:agent", "intelligence:knowledge"],
    "/intelligence-audit": ["intelligence:audit"],
    "/fault-report": ["fault:create", "intelligence:agent"],
    "/agent-report": ["intelligence:agent", "fault:create"],
    "/maintenance-records": ["maintenance:view"],
    "/maintenance-records/:id": ["maintenance:view", "maintenance:detail"],
    "/repair-execution": ["maintenance:view", "fault:repair", "fault:close", "intelligence:agent"],
    "/system-management": ["identity:read", "identity:write", "system:audit"],
  };
  return (required[path] ?? []).every((code) => codes.includes(code));
}

function GlobalAgentDrawer({ onClose }: { onClose: () => void }) {
  const [agentId, setAgentId] = useState("operation_guidance");
  const [text, setText] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [thread, setThread] = useState<AgentThread | null>(null);
  const [events, setEvents] = useState<RuntimeEvent[]>([]);
  const [tab, setTab] = useState<"compose" | "history">("compose");
  const [history, setHistory] = useState<AgentThreadSummary[] | null>(null);
  const [historyError, setHistoryError] = useState<string | null>(null);
  useEffect(() => {
    if (tab !== "history") return;
    getAgentThreads().then((value) => { setHistory(value.items); setHistoryError(null); }).catch((error) => setHistoryError(error instanceof ApiError ? error.code ?? "REQUEST_FAILED" : "REQUEST_FAILED"));
  }, [tab]);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!text.trim()) return;
    setMessage("正在创建正式 Agent 任务…");
    try {
      const run = await startAgentRun(agentId, {}, text.trim());
      setMessage(`已创建任务：${run.run_id}`);
      setEvents(await readRunEvents(run.run_id));
      setThread(await getAgentThread(run.thread_id));
    } catch (error) {
      setMessage(`请求失败：${error instanceof ApiError ? error.code : "REQUEST_FAILED"}`);
    }
  }
  async function resume() {
    if (!thread) return;
    try {
      const latest = thread.runs[thread.runs.length - 1];
      if (!latest) return;
      const resumed = await resumeAgentThread(thread.thread_id, { resume: true, confirmation: { source: "user" } });
      setMessage(`已恢复任务：${resumed.run_id}`);
    } catch (error) {
      setMessage(`恢复失败：${error instanceof ApiError ? error.code : "REQUEST_FAILED"}`);
    }
  }
  return <aside className="agent-drawer" aria-label="全局 Agent"><header><strong>全局 Agent</strong><button type="button" onClick={onClose}>关闭</button></header><div className="tab-list"><button type="button" aria-pressed={tab === "compose"} onClick={() => setTab("compose")}>新建任务</button><button type="button" aria-pressed={tab === "history"} onClick={() => setTab("history")}>线程历史</button></div>{tab === "compose" ? <><p>仅可创建故障上报、智能问数和操作指引任务。</p><form onSubmit={submit}><label>类型<select value={agentId} onChange={(event) => setAgentId(event.target.value)}><option value="fault_reporting">AI 故障上报</option><option value="metric_query">智能问数</option><option value="operation_guidance">操作指引</option></select></label><label>问题<textarea value={text} onChange={(event) => setText(event.target.value)} required /></label><button type="submit">发起任务</button></form></> : <section aria-label="Agent 历史">{historyError && <p role="alert">线程历史加载失败：{historyError}</p>}{history === null && !historyError ? <p role="status">正在加载线程历史…</p> : history?.length === 0 ? <p>暂无线程历史。</p> : <ul>{history?.map((item) => <li key={item.thread_id}><button type="button" onClick={() => void getAgentThread(item.thread_id).then(setThread).catch((error) => setHistoryError(error instanceof ApiError ? error.code ?? "REQUEST_FAILED" : "REQUEST_FAILED"))}>{item.agent_id} · {item.status}</button></li>)}</ul>}{thread && <div><p>线程：{thread.thread_id}</p><p>状态：{thread.status}</p>{thread.messages.map((item, index) => <p key={index}>消息已记录（内容受保护）</p>)}{thread.runs.length > 0 && <button type="button" onClick={() => void resume()}>恢复最近任务</button>}</div>}</section>}{events.length > 0 && <section aria-label="Agent 运行状态">{events.map((item, index) => <p key={`${item.event}-${index}`}>{item.event}：{String(item.data.status ?? "已收到")}</p>)}</section>}{message && <p role="status">{message}</p>}</aside>;
}

export function App() {
  return <Routes>
    <Route path="/login" element={hasActiveSession() ? <Navigate to="/" replace /> : <LoginPage />} />
    <Route path="*" element={<RequireAuthentication><ApplicationShell /></RequireAuthentication>} />
  </Routes>;
}
