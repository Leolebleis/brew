import type { QueryClient } from "@tanstack/react-query";
import { openSse } from "../api/sse";
import { handleStatusEvent } from "./hooks";

export function startStatusEventListener(
  qc: QueryClient,
  onJournalEntry: (entryId: string) => void,
  signal: AbortSignal,
): void {
  void openSse("/events", {
    signal,
    onMessage: (ev) => {
      if (!ev.event) return;
      let data: unknown;
      try {
        data = JSON.parse(ev.data);
      } catch {
        return;
      }
      handleStatusEvent(qc, ev.event, data);
      if (ev.event === "JournalEntryCreated") {
        const d = data as { entry_id?: string };
        if (d.entry_id) onJournalEntry(d.entry_id);
      }
    },
    onError: (err) => {
      console.warn("status events stream errored:", err);
    },
  });
}
