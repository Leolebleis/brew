import { describe, it, expect, beforeEach } from "vitest";
import { handleSseEvent } from "./runtime";
import { useChatStore } from "./store";

beforeEach(() => {
  useChatStore.setState({ messages: [] });
});

describe("handleSseEvent", () => {
  it("text_delta appends to current assistant text", () => {
    useChatStore.getState().startAssistantTurn();
    handleSseEvent("text_delta", { text: "Hi " });
    handleSseEvent("text_delta", { text: "there" });
    expect(useChatStore.getState().messages.at(-1)!.content).toEqual([
      { type: "text", text: "Hi there" },
    ]);
  });

  it("tool_call_start appends a tool-call part", () => {
    useChatStore.getState().startAssistantTurn();
    handleSseEvent("tool_call_start", { tool_call_id: "c1", tool_name: "brew_now" });
    const part = useChatStore.getState().messages.at(-1)!.content[0];
    expect(part.type).toBe("tool-call");
  });

  it("tool_call_delta accumulates arg fragments", () => {
    useChatStore.getState().startAssistantTurn();
    handleSseEvent("tool_call_start", { tool_call_id: "c1", tool_name: "brew_now" });
    handleSseEvent("tool_call_delta", { tool_call_id: "c1", args_delta: '{"x":' });
    handleSseEvent("tool_call_delta", { tool_call_id: "c1", args_delta: "1}" });
    const part = useChatStore.getState().messages.at(-1)!.content[0];
    expect((part as { args_raw: string }).args_raw).toBe('{"x":1}');
  });

  it("tool_call_result appends a tool-result", () => {
    useChatStore.getState().startAssistantTurn();
    handleSseEvent("tool_call_start", { tool_call_id: "c1", tool_name: "brew_now" });
    handleSseEvent("tool_call_result", { tool_call_id: "c1", result: { status: "ok" } });
    const last = useChatStore.getState().messages.at(-1)!;
    expect(last.content.at(-1)!.type).toBe("tool-result");
  });

  it("thinking_delta appends to reasoning", () => {
    useChatStore.getState().startAssistantTurn();
    handleSseEvent("thinking_delta", { text: "checking…" });
    expect(useChatStore.getState().messages.at(-1)!.content[0]).toEqual({
      type: "reasoning",
      text: "checking…",
    });
  });

  it("done marks turn complete with messageId", () => {
    useChatStore.getState().startAssistantTurn();
    handleSseEvent("done", { message_id: "msg-1" });
    expect(useChatStore.getState().messages.at(-1)!.status).toBe("complete");
    expect(useChatStore.getState().messages.at(-1)!.id).toBe("msg-1");
  });

  it("error marks turn errored", () => {
    useChatStore.getState().startAssistantTurn();
    handleSseEvent("error", { code: "Boom", message: "oops" });
    expect(useChatStore.getState().messages.at(-1)!.status).toBe("error");
  });
});
