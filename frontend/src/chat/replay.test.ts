import { describe, it, expect, vi, beforeEach } from "vitest";
import { loadInitialThread } from "./replay";
import { useChatStore } from "./store";

beforeEach(() => {
  useChatStore.setState({ messages: [] });
});

describe("loadInitialThread", () => {
  it("loads projected messages into the store, oldest first", async () => {
    const fetchMock = vi.fn(async () =>
      new Response(
        JSON.stringify({
          messages: [
            { id: "2", kind: "response", payload: {}, projected: { role: "assistant", content: [{ type: "text", text: "hi" }] }, created_at: "2026-05-02T10:00:01Z" },
            { id: "1", kind: "request", payload: {}, projected: { role: "user", content: [{ type: "text", text: "hello" }] }, created_at: "2026-05-02T10:00:00Z" },
          ],
          next_before_id: null,
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    await loadInitialThread();
    const msgs = useChatStore.getState().messages;
    expect(msgs).toHaveLength(2);
    expect(msgs[0].role).toBe("user");
    expect(msgs[1].role).toBe("assistant");
  });

  it("filters out null projections (system prompts etc.)", async () => {
    const fetchMock = vi.fn(async () =>
      new Response(
        JSON.stringify({
          messages: [
            { id: "1", kind: "request", payload: {}, projected: null, created_at: "2026-05-02T10:00:00Z" },
            { id: "2", kind: "request", payload: {}, projected: { role: "user", content: [{ type: "text", text: "hi" }] }, created_at: "2026-05-02T10:00:01Z" },
          ],
          next_before_id: null,
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    await loadInitialThread();
    expect(useChatStore.getState().messages).toHaveLength(1);
  });
});
