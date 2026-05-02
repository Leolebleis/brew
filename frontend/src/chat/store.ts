import { create } from "zustand";

export type ThreadPart =
  | { type: "text"; text: string }
  | { type: "tool-call"; tool_call_id: string; tool_name: string; args_raw: string }
  | { type: "tool-result"; tool_call_id: string; tool_name: string; result: unknown }
  | { type: "reasoning"; text: string };

export interface ThreadMessage {
  id?: string;
  role: "user" | "assistant";
  content: ThreadPart[];
  status: "streaming" | "complete" | "error";
  error?: { code: string; message: string };
}

interface ChatState {
  messages: ThreadMessage[];
  appendUserMessage: (text: string) => void;
  startAssistantTurn: () => void;
  appendAssistantText: (text: string) => void;
  appendThinking: (text: string) => void;
  appendToolCall: (toolCallId: string, toolName: string) => void;
  appendToolCallArgsDelta: (toolCallId: string, delta: string) => void;
  appendToolResult: (toolCallId: string, toolName: string, result: unknown) => void;
  completeAssistantTurn: (messageId: string) => void;
  errorAssistantTurn: (code: string, message: string) => void;
  loadThread: (messages: ThreadMessage[]) => void;
}

function patchLast(state: ChatState, fn: (msg: ThreadMessage) => ThreadMessage): ThreadMessage[] {
  const last = state.messages.at(-1);
  if (!last) return state.messages;
  return [...state.messages.slice(0, -1), fn(last)];
}

function appendOrExtendStreamPart(
  state: ChatState,
  partType: "text" | "reasoning",
  text: string,
): ThreadMessage[] {
  return patchLast(state, (m) => {
    const last = m.content.at(-1);
    if (last?.type === partType) {
      return { ...m, content: [...m.content.slice(0, -1), { ...last, text: last.text + text }] };
    }
    return { ...m, content: [...m.content, { type: partType, text }] };
  });
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  appendUserMessage: (text) =>
    set((s) => ({
      messages: [
        ...s.messages,
        { role: "user", content: [{ type: "text", text }], status: "complete" },
      ],
    })),
  startAssistantTurn: () =>
    set((s) => ({
      messages: [...s.messages, { role: "assistant", content: [], status: "streaming" }],
    })),
  appendAssistantText: (text) =>
    set((s) => ({ messages: appendOrExtendStreamPart(s, "text", text) })),
  appendThinking: (text) =>
    set((s) => ({ messages: appendOrExtendStreamPart(s, "reasoning", text) })),
  appendToolCall: (tool_call_id, tool_name) =>
    set((s) => ({
      messages: patchLast(s, (m) => ({
        ...m,
        content: [...m.content, { type: "tool-call", tool_call_id, tool_name, args_raw: "" }],
      })),
    })),
  appendToolCallArgsDelta: (tool_call_id, delta) =>
    set((s) => ({
      messages: patchLast(s, (m) => ({
        ...m,
        content: m.content.map((p) =>
          p.type === "tool-call" && p.tool_call_id === tool_call_id
            ? { ...p, args_raw: p.args_raw + delta }
            : p,
        ),
      })),
    })),
  appendToolResult: (tool_call_id, tool_name, result) =>
    set((s) => ({
      messages: patchLast(s, (m) => ({
        ...m,
        content: [...m.content, { type: "tool-result", tool_call_id, tool_name, result }],
      })),
    })),
  completeAssistantTurn: (messageId) =>
    set((s) => ({
      messages: patchLast(s, (m) => ({ ...m, id: messageId, status: "complete" })),
    })),
  errorAssistantTurn: (code, message) =>
    set((s) => ({
      messages: patchLast(s, (m) => ({ ...m, status: "error", error: { code, message } })),
    })),
  loadThread: (messages) => set(() => ({ messages })),
}));
