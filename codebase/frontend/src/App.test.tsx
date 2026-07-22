import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { App } from "./App";

describe("App", () => {
  it("renders the prototype-inspired shared shell without business content", () => {
    render(
      <MemoryRouter initialEntries={["/intelligent-config"]}>
        <App />
      </MemoryRouter>,
    );

    expect(screen.getByRole("navigation", { name: "主导航" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "智能配置" })).toBeInTheDocument();
    expect(screen.getByText("业务内容将在对应任务中接入")).toBeInTheDocument();
    expect(screen.queryByLabelText("保存配置")).not.toBeInTheDocument();
  });
});
