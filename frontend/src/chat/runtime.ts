import { useExternalStoreRuntime, type ThreadMessageLike } from "@assistant-ui/react";
import { postSse } from "../api/sse";
import { useChatStore, type ThreadMessage, type ThreadPart } from "./store";

export function handleSseEvent(name: string, data: unknown): void {
  const s = useChatStore.getState();
  const d = data as Record<string, unknown>;
  switch (name) {
    case "text_delta":
      s.appendAssistantText(String(d.text ?? ""));
      return;
    case "tool_call_start":
      s.appendToolCall(String(d.tool_call_id), String(d.tool_name));
      return;
    case "tool_call_delta":
      s.appendToolCallArgsDelta(String(d.tool_call_id), String(d.args_delta ?? ""));
      return;
    case "tool_call_result":
      s.appendToolResult(String(d.tool_call_id), String(d.tool_name ?? ""), d.result);
      return;
    case "thinking_delta":
      s.appendThinking(String(d.text ?? ""));
      return;
    case "done":
      s.completeAssistantTurn(String(d.message_id));
      return;
    case "error":
      s.errorAssistantTurn(String(d.code ?? "UnknownError"), String(d.message ?? ""));
      return;
    default:
      return;
  }
}

export async function runChat(text: string): Promise<void> {
  const s = useChatStore.getState();
  s.appendUserMessage(text);
  s.startAssistantTurn();
  try {
    await postSse(
      "/chat/messages",
      { text },
      {
        onMessage: (ev) => {
          if (!ev.event) return;
          let data: unknown = {};
          try {
            data = JSON.parse(ev.data);
          } catch {
            // tolerate non-JSON / keepalive
          }
          handleSseEvent(ev.event, data);
        },
        onError: (err) => {
          s.errorAssistantTurn("NetworkError", err instanceof Error ? err.message : String(err));
        },
      },
    );
  } catch (err) {
    if (useChatStore.getState().messages.at(-1)?.status === "streaming") {
      s.errorAssistantTurn("NetworkError", err instanceof Error ? err.message : String(err));
    }
  }
}

function tryParseArgs(raw: string): Record<string, unknown> {
  if (!raw) return {};
  try {
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
      return parsed as Record<string, unknown>;
    }
    return { _raw: raw };
  } catch {
    return { _raw: raw };
  }
}

function partToAssistantUi(p: ThreadPart): unknown {
  switch (p.type) {
    case "text":
      return { type: "text", text: p.text };
    case "tool-call":
      return {
        type: "tool-call",
        toolCallId: p.tool_call_id,
        toolName: p.tool_name,
        args: tryParseArgs(p.args_raw),
      };
    case "tool-result":
      return {
        type: "tool-call",
        toolCallId: p.tool_call_id,
        toolName: p.tool_name,
        args: {},
        result: p.result,
      };
    case "reasoning":
      return { type: "reasoning", text: p.text };
  }
}

function toAssistantUi(m: ThreadMessage): ThreadMessageLike {
  return {
    role: m.role,
    content: m.content.map(partToAssistantUi),
  } as ThreadMessageLike;
}

export function useChatRuntime() {
  const messages = useChatStore((s) => s.messages);
  return useExternalStoreRuntime({
    isRunning: messages.at(-1)?.status === "streaming",
    messages,
    convertMessage: toAssistantUi,
    onNew: async ({ content }) => {
      const text =
        content.find((c): c is { type: "text"; text: string } => c.type === "text")?.text ?? "";
      if (text) await runChat(text);
    },
  });
}
