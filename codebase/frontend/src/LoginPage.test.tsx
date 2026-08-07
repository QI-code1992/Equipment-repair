import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { Location, MemoryRouter, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import * as api from "./api";
import { LoginPage } from "./LoginPage";

function LocationProbe() {
  const location = useLocation();
  return <output data-testid="location">{location.pathname}{location.search}{location.hash}</output>;
}

function renderLogin(initialEntry: string | Partial<Location> = "/login") {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <LoginPage />
      <LocationProbe />
    </MemoryRouter>,
  );
}

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
});

describe("LoginPage", () => {
  it("renders the approved platform identity and controlled-access context", () => {
    renderLogin();

    expect(screen.getByText("新能源装载机设备故障智能运维平台")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "设备AI智能运维平台" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "登录" })).toBeInTheDocument();
    for (const label of ["故障追踪", "诊断辅助", "知识检索", "知识图谱", "驾驶舱分析", "工单协同"]) expect(screen.getByText(label)).toBeInTheDocument();
  });

  it("identifies credentials for the browser password manager without platform-side storage", () => {
    renderLogin();

    expect(screen.getByLabelText("用户名")).toHaveAttribute("name", "username");
    expect(screen.getByLabelText("密码")).toHaveAttribute("name", "password");
    expect(screen.getByText("密码由浏览器的密码管理器保存，平台不会存储密码。")).toBeInTheDocument();
  });

  it("shows field-level errors and does not call the authentication API for blank credentials", () => {
    const login = vi.spyOn(api, "login");
    renderLogin();

    fireEvent.click(screen.getByRole("button", { name: "登录" }));

    expect(screen.getByText("请输入账号。")).toBeInTheDocument();
    expect(screen.getByText("请输入密码。")).toBeInTheDocument();
    expect(screen.getByLabelText("用户名")).toHaveAttribute("aria-invalid", "true");
    expect(screen.getByLabelText("密码")).toHaveAttribute("aria-invalid", "true");
    expect(login).not.toHaveBeenCalled();
  });

  it("shows loading feedback while authenticating and returns to the original path", async () => {
    let resolveLogin: (() => void) | undefined;
    const loginPromise = new Promise<void>((resolve) => { resolveLogin = resolve; });
    vi.spyOn(api, "login").mockReturnValue(loginPromise);
    renderLogin({ pathname: "/login", search: "", hash: "", state: { from: "/equipment?status=FAULT#eq-7" } });

    fireEvent.change(screen.getByLabelText("用户名"), { target: { value: "operator" } });
    fireEvent.change(screen.getByLabelText("密码"), { target: { value: "correct-password" } });
    fireEvent.click(screen.getByRole("button", { name: "登录" }));

    expect(screen.getByRole("button", { name: "登录中…" })).toBeDisabled();
    expect(screen.getByRole("status", { name: "登录状态" })).toHaveTextContent("正在验证账号");

    resolveLogin?.();
    await waitFor(() => expect(screen.getByTestId("location")).toHaveTextContent("/equipment?status=FAULT#eq-7"));
  });

  it("counts credential failures and locks the form for thirty seconds after three 401 responses", async () => {
    vi.useFakeTimers();
    vi.spyOn(api, "login").mockRejectedValue(new api.ApiError(401, "INVALID_CREDENTIALS"));
    renderLogin();
    fireEvent.change(screen.getByLabelText("用户名"), { target: { value: "operator" } });
    fireEvent.change(screen.getByLabelText("密码"), { target: { value: "wrong-password" } });

    for (const remaining of [2, 1]) {
      fireEvent.click(screen.getByRole("button", { name: "登录" }));
      await act(async () => { await Promise.resolve(); });
      expect(screen.getByRole("alert")).toHaveTextContent(`剩余 ${remaining} 次机会`);
    }

    fireEvent.click(screen.getByRole("button", { name: "登录" }));
    await act(async () => { await Promise.resolve(); });
    expect(screen.getByRole("alert")).toHaveTextContent("账号已临时锁定，请 30s 后再试");
    expect(screen.getByRole("button", { name: "登录" })).toBeDisabled();
    expect(api.login).toHaveBeenCalledTimes(3);

    await act(async () => { await vi.advanceTimersByTimeAsync(30_000); });
    expect(screen.getByRole("alert")).toHaveTextContent("账号锁定已解除，请重新登录");
    expect(screen.getByRole("button", { name: "登录" })).toBeEnabled();
  });

  it("opens and closes the forgot-password modal without leaving the page", () => {
    renderLogin();

    fireEvent.click(screen.getByRole("button", { name: "忘记密码" }));
    expect(screen.getByRole("dialog", { name: "忘记密码" })).toBeInTheDocument();
    expect(screen.getByText(/请联系系统管理员重置密码/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "知道了" }));
    expect(screen.queryByRole("dialog", { name: "忘记密码" })).not.toBeInTheDocument();
  });
});
