import type { QueryClient } from "@tanstack/react-query";
import { decodeSseMessage, openSse } from "../api/sse";
import { StatusEvent } from "./events";
import { handleStatusEvent } from "./hooks";

export function startStatusEventListener(
  qc: QueryClient,
  onJournalEntry: (entryId: string) => void,
  signal: AbortSignal,
): void {
  void openSse("/events", {
    signal,
    onMessage: (ev) => {
      const decoded = decodeSseMessage(ev);
      if (!decoded) return;
      handleStatusEvent(qc, decoded.name, decoded.data);
      if (decoded.name === StatusEvent.JournalEntryCreated) {
        const d = decoded.data as { entry_id?: string };
        if (d.entry_id) onJournalEntry(d.entry_id);
      }
    },
    onError: (err) => {
      console.warn("status events stream errored:", err);
    },
  });
}
