import { fetchEventSource, type EventSourceMessage } from "@microsoft/fetch-event-source";
import { API_BASE, API_KEY } from "../config";

export interface SseHandlers {
  onOpen?: (resp: Response) => void | Promise<void>;
  onMessage: (ev: EventSourceMessage) => void;
  onError?: (err: unknown) => void;
  onClose?: () => void;
  signal?: AbortSignal;
}

export function decodeSseMessage(
  ev: EventSourceMessage,
): { name: string; data: unknown } | null {
  if (!ev.event) return null;
  try {
    return { name: ev.event, data: JSON.parse(ev.data) };
  } catch {
    return null; // keepalive comment or unparseable
  }
}

export async function openSse(path: string, h: SseHandlers): Promise<void> {
  await fetchEventSource(`${API_BASE}${path}`, {
    method: "GET",
    headers: API_KEY ? { "X-API-Key": API_KEY } : {},
    signal: h.signal,
    onopen: async (resp) => {
      if (resp.ok) {
        await h.onOpen?.(resp);
        return;
      }
      throw new Error(`SSE open failed: ${resp.status}`);
    },
    onmessage: h.onMessage,
    onerror: (err) => {
      h.onError?.(err);
    },
    onclose: () => h.onClose?.(),
    openWhenHidden: true,
  });
}

export async function postSse(path: string, body: unknown, h: SseHandlers): Promise<void> {
  await fetchEventSource(`${API_BASE}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(API_KEY ? { "X-API-Key": API_KEY } : {}),
    },
    body: JSON.stringify(body),
    signal: h.signal,
    onopen: async (resp) => {
      if (resp.ok) {
        await h.onOpen?.(resp);
        return;
      }
      throw new Error(`SSE open failed: ${resp.status}`);
    },
    onmessage: h.onMessage,
    onerror: (err) => {
      h.onError?.(err);
      // Re-throw so fetch-event-source does not retry. Indefinite retry is
      // wrong for one-shot POST chat turns.
      throw err;
    },
    onclose: () => h.onClose?.(),
    openWhenHidden: true,
  });
}
