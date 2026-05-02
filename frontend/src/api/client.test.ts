import { describe, it, expect, vi, beforeEach } from "vitest";
import { apiFetch } from "./client";

describe("apiFetch", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response("{}", { status: 200, headers: { "content-type": "application/json" } })));
  });

  it("prepends API_BASE to relative paths", async () => {
    await apiFetch("/device");
    const fetch = (globalThis.fetch as ReturnType<typeof vi.fn>);
    expect(fetch.mock.calls[0][0]).toBe("/api/device");
  });

  it("sets X-API-Key header from config", async () => {
    await apiFetch("/device");
    const fetch = (globalThis.fetch as ReturnType<typeof vi.fn>);
    const init = fetch.mock.calls[0][1] as RequestInit;
    expect((init.headers as Headers).get?.("X-API-Key") ?? (init.headers as Record<string, string>)["X-API-Key"]).toBeDefined();
  });

  it("merges custom headers without dropping API key", async () => {
    await apiFetch("/device", { headers: { "X-Trace": "abc" } });
    const fetch = (globalThis.fetch as ReturnType<typeof vi.fn>);
    const init = fetch.mock.calls[0][1] as RequestInit;
    const headers = init.headers as Headers;
    expect(headers.get("X-Trace")).toBe("abc");
    expect(headers.get("X-API-Key")).toBeDefined();
  });
});
