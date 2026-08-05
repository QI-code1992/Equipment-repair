import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { LoginPage } from "./LoginPage";

describe("LoginPage", () => {
  it("renders the approved platform identity and controlled-access context", () => {
    render(<MemoryRouter><LoginPage /></MemoryRouter>);

    expect(screen.getByText("新能源装载机智能运维平台")).toBeInTheDocument();
    expect(screen.getByText("现场运维 · 受控访问")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "欢迎回来" })).toBeInTheDocument();
    expect(screen.getByText("故障追踪")).toBeInTheDocument();
    expect(screen.getByText(/连续失败 3 次后临时锁定/)).toBeInTheDocument();
  });
  it("provides remember-password and forgot-password controls without bypassing login", () => {
    render(<MemoryRouter><LoginPage /></MemoryRouter>);

    expect(screen.getByRole("checkbox", { name: "记住密码" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "忘记密码" }));
    expect(screen.getByRole("dialog", { name: "忘记密码" })).toBeInTheDocument();
  });
  it("locks the login action after three failed attempts", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: { code: "UNAUTHENTICATED" } }), { status: 401 })));
    render(<MemoryRouter><LoginPage /></MemoryRouter>);
    fireEvent.change(screen.getByLabelText("用户名"), { target: { value: "operator" } });
    fireEvent.change(screen.getByLabelText("密码"), { target: { value: "wrong" } });
    const submit = screen.getByRole("button", { name: "登录系统" });
    fireEvent.click(submit); await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());
    fireEvent.click(submit); await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());
    fireEvent.click(submit); await waitFor(() => expect(screen.getByText(/账号已临时锁定/)).toBeInTheDocument());
    expect(submit).toBeDisabled();
  });
});
