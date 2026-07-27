import { NavLink, Route, Routes, useLocation } from "react-router-dom";

import { IntelligentConfigPage } from "./IntelligentConfigPage";
import { FaultReportPage } from "./FaultReportPage";

type Page = {
  path: string;
  label: string;
  group: string;
  mark: string;
};

const pages: Page[] = [
  { path: "/", label: "运维工作台", group: "工作台", mark: "台" },
  { path: "/intelligent-config", label: "智能配置", group: "智能运维", mark: "智" },
  { path: "/fault-report", label: "故障上报", group: "现场作业", mark: "报" },
  { path: "/repair-execution", label: "维修执行", group: "现场作业", mark: "修" },
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

export function App() {
  const location = useLocation();
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
          <div className="topbar__avatar" aria-label="当前用户">管</div>
        </header>
        <Routes>
          {pages.map((page) => <Route key={page.path} path={page.path} element={page.path === "/intelligent-config" ? <IntelligentConfigPage /> : page.path === "/fault-report" ? <FaultReportPage /> : <PageShell label={page.label} />} />)}
          <Route path="*" element={<PageShell label={activePage.label} />} />
        </Routes>
      </main>
    </div>
  );
}
