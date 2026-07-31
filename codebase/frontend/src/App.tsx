import { FormEvent, useState } from "react";
import { Navigate, NavLink, Route, Routes, useLocation } from "react-router-dom";

import { IntelligentConfigPage } from "./IntelligentConfigPage";
import { FaultReportPage } from "./FaultReportPage";
import { RepairExecutionPage } from "./RepairExecutionPage";
import { WorkbenchPage } from "./WorkbenchPage";
import { ApiError, hasActiveSession, startAgentRun } from "./api";
import { LoginPage } from "./LoginPage";
import { AgentReportPage, BiDashboardPage, EquipmentAddPage, EquipmentDetailPage, EquipmentEditPage, EquipmentLedgerPage, FactoryModelingPage, IntelligentAuditPage, MaintenanceRecordsPage, SystemManagementPage } from "./PortalPages";

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
  const [agentOpen, setAgentOpen] = useState(false);
  const activePage = pages.find((page) => page.path === location.pathname) ?? pages[0];
  const groups = [...new Set(pages.map((page) => page.group))];

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
          {groups.map((group) => (
            <div className="nav-group" key={group}>
              <div className="nav-group__label">{group}</div>
              {pages.filter((page) => page.group === group).map((page) => (
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
          <div className="topbar__actions"><button type="button" className="agent-trigger" onClick={() => setAgentOpen(true)}>全局 Agent</button><div className="topbar__avatar" aria-label="当前用户">管</div></div>
        </header>
        <Routes>
          <Route path="/" element={<WorkbenchPage />} />
          <Route path="/bi-dashboard" element={<BiDashboardPage />} />
          <Route path="/factory-modeling" element={<FactoryModelingPage />} />
          <Route path="/equipment" element={<EquipmentLedgerPage />} />
          <Route path="/equipment/new" element={<EquipmentAddPage />} />
          <Route path="/equipment/:id" element={<EquipmentDetailPage />} />
          <Route path="/equipment/:id/edit" element={<EquipmentEditPage />} />
          <Route path="/intelligent-config" element={<IntelligentConfigPage />} />
          <Route path="/intelligence-audit" element={<IntelligentAuditPage />} />
          <Route path="/fault-report" element={<FaultReportPage />} />
          <Route path="/agent-report" element={<AgentReportPage />} />
          <Route path="/maintenance-records" element={<MaintenanceRecordsPage />} />
          <Route path="/repair-execution" element={<RepairExecutionPage />} />
          <Route path="/system-management" element={<SystemManagementPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        {agentOpen && <GlobalAgentDrawer onClose={() => setAgentOpen(false)} />}
      </main>
    </div>
  );
}

function GlobalAgentDrawer({ onClose }: { onClose: () => void }) {
  const [agentId, setAgentId] = useState("operation_guidance");
  const [text, setText] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!text.trim()) return;
    setMessage("正在创建正式 Agent 任务…");
    try {
      const run = await startAgentRun(agentId, {}, text.trim());
      setMessage(`已创建任务：${run.run_id}`);
    } catch (error) {
      setMessage(`请求失败：${error instanceof ApiError ? error.code : "REQUEST_FAILED"}`);
    }
  }
  return <aside className="agent-drawer" aria-label="全局 Agent"><header><strong>全局 Agent</strong><button type="button" onClick={onClose}>关闭</button></header><p>仅可创建故障上报、智能问数和操作指引任务。</p><form onSubmit={submit}><label>类型<select value={agentId} onChange={(event) => setAgentId(event.target.value)}><option value="fault_reporting">AI 故障上报</option><option value="metric_query">智能问数</option><option value="operation_guidance">操作指引</option></select></label><label>问题<textarea value={text} onChange={(event) => setText(event.target.value)} required /></label><button type="submit">发起任务</button></form>{message && <p role="status">{message}</p>}</aside>;
}

export function App() {
  return <Routes>
    <Route path="/login" element={hasActiveSession() ? <Navigate to="/" replace /> : <LoginPage />} />
    <Route path="*" element={<RequireAuthentication><ApplicationShell /></RequireAuthentication>} />
  </Routes>;
}
