import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { LoginPage } from "./LoginPage";

describe("LoginPage", () => {
  it("renders the approved platform identity and controlled-access context", () => {
    render(<MemoryRouter><LoginPage /></MemoryRouter>);

    expect(screen.getByText("新能源装载机智能运维平台")).toBeInTheDocument();
    expect(screen.getByText("现场运维 · 受控访问")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "欢迎回来" })).toBeInTheDocument();
  });
});
