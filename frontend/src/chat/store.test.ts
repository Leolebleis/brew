import { describe, it, expect, beforeEach } from "vitest";
import { useChatStore, type ThreadMessage } from "./store";

beforeEach(() => {
  useChatStore.setState({ messages: [] });
});

describe("chat store", () => {
  it("appends a user message", () => {
    useChatStore.getState().appendUserMessage("hi");
    const msgs = useChatStore.getState().messages;
    expect(msgs).toHaveLength(1);
    expect(msgs[0].role).toBe("user");
    expect(msgs[0].content[0]).toEqual({ type: "text", text: "hi" });
  });

  it("startAssistantTurn creates an empty assistant draft", () => {
    useChatStore.getState().startAssistantTurn();
    const last = useChatStore.getState().messages.at(-1)!;
    expect(last.role).toBe("assistant");
    expect(last.content).toEqual([]);
    expect(last.status).toBe("streaming");
  });

  it("appendAssistantText accumulates into the latest text part", () => {
    const s = useChatStore.getState();
    s.startAssistantTurn();
    s.appendAssistantText("Hel");
    s.appendAssistantText("lo");
    const last = useChatStore.getState().messages.at(-1)!;
    expect(last.content).toEqual([{ type: "text", text: "Hello" }]);
  });

  it("appendToolCall starts a new tool-call part with empty args", () => {
    const s = useChatStore.getState();
    s.startAssistantTurn();
    s.appendToolCall("call_1", "brew_now");
    const last = useChatStore.getState().messages.at(-1)!;
    expect(last.content).toEqual([
      { type: "tool-call", tool_call_id: "call_1", tool_name: "brew_now", args_raw: "" },
    ]);
  });

  it("appendToolCallArgsDelta accumulates JSON fragment text", () => {
    const s = useChatStore.getState();
    s.startAssistantTurn();
    s.appendToolCall("call_1", "brew_now");
    s.appendToolCallArgsDelta("call_1", '{"profile_id":');
    s.appendToolCallArgsDelta("call_1", '"p1"}');
    const last = useChatStore.getState().messages.at(-1)!;
    const part = last.content.find((p) => p.type === "tool-call" && p.tool_call_id === "call_1")!;
    expect((part as { args_raw: string }).args_raw).toBe('{"profile_id":"p1"}');
  });

  it("appendToolResult appends a tool-result part", () => {
    const s = useChatStore.getState();
    s.startAssistantTurn();
    s.appendToolResult("call_1", "brew_now", { status: "ok" });
    const last = useChatStore.getState().messages.at(-1)!;
    expect(last.content.at(-1)).toEqual({
      type: "tool-result",
      tool_call_id: "call_1",
      tool_name: "brew_now",
      result: { status: "ok" },
    });
  });

  it("completeAssistantTurn marks status complete", () => {
    const s = useChatStore.getState();
    s.startAssistantTurn();
    s.completeAssistantTurn("msg-id-123");
    const last = useChatStore.getState().messages.at(-1)!;
    expect(last.status).toBe("complete");
    expect(last.id).toBe("msg-id-123");
  });

  it("errorAssistantTurn marks status errored", () => {
    const s = useChatStore.getState();
    s.startAssistantTurn();
    s.errorAssistantTurn("UnknownError", "boom");
    const last = useChatStore.getState().messages.at(-1)!;
    expect(last.status).toBe("error");
    expect(last.error).toEqual({ code: "UnknownError", message: "boom" });
  });

  it("loadThread replaces messages from server projection", () => {
    const projected: ThreadMessage[] = [
      { id: "1", role: "user", content: [{ type: "text", text: "hi" }], status: "complete" },
      { id: "2", role: "assistant", content: [{ type: "text", text: "hello" }], status: "complete" },
    ];
    useChatStore.getState().loadThread(projected);
    expect(useChatStore.getState().messages).toEqual(projected);
  });
});
