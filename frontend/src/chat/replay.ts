import { apiJson } from "../api/client";
import { useChatStore, type ThreadMessage, type ThreadPart } from "./store";

interface ReplayMessage {
  id: string;
  kind: "request" | "response";
  payload: unknown;
  projected: { role: "user" | "assistant"; content: unknown[] } | null;
  created_at: string;
}

interface ReplayResponse {
  messages: ReplayMessage[];
  next_before_id: string | null;
}

export async function loadInitialThread(): Promise<void> {
  const resp = await apiJson<ReplayResponse>("/chat/messages?limit=50");
  // Server returns newest-first; we want oldest-first in the store.
  const ordered = [...resp.messages].reverse();
  const projected: ThreadMessage[] = ordered
    .filter((m): m is ReplayMessage & { projected: NonNullable<ReplayMessage["projected"]> } => m.projected !== null)
    .map((m) => ({
      id: m.id,
      role: m.projected.role,
      content: m.projected.content as ThreadPart[],
      status: "complete",
    }));
  useChatStore.getState().loadThread(projected);
}
