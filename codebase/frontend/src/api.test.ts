import { describe, expect, it, vi } from "vitest";

import { requestJson } from "./api";

describe("requestJson", () => {
  it("uses the browser fetch boundary and returns JSON", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ status: "ok" }), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(requestJson<{ status: string }>("/healthz")).resolves.toEqual({ status: "ok" });
    expect(fetchMock).toHaveBeenCalledWith("/healthz", undefined);
  });
});
