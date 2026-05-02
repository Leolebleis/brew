import { useEffect, useRef } from "react";
import { Terminal } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import { AttachAddon } from "@xterm/addon-attach";
import { WebglAddon } from "@xterm/addon-webgl";
import "@xterm/xterm/css/xterm.css";
import { API_BASE, API_KEY } from "../config";

function buildWsUrl(): string {
  // API_BASE is "/coffee/api" in production; the WS path is "/terminal/ws".
  const proto = location.protocol === "https:" ? "wss:" : "ws:";
  const path = `${API_BASE}/terminal/ws`;
  const qs = API_KEY ? `?api_key=${encodeURIComponent(API_KEY)}` : "";
  return `${proto}//${location.host}${path}${qs}`;
}

export function TerminalTab() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const term = new Terminal({
      fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
      fontSize: 13,
      theme: {
        background: "var(--color-bg)" as unknown as string,
        foreground: "var(--color-fg)" as unknown as string,
      },
    });

    const fit = new FitAddon();
    term.loadAddon(fit);

    // Probe for WebGL2 before loading the addon — JSDOM and very old
    // browsers don't support it, and the addon's activate path emits an
    // async error that the synchronous try/catch can't catch.
    const probe = document.createElement("canvas");
    if (probe.getContext && probe.getContext("webgl2")) {
      try {
        term.loadAddon(new WebglAddon());
      } catch {
        // WebGL2 reported but addon refused it — fall back to canvas.
      }
    }

    term.open(containerRef.current);
    fit.fit();

    const ws = new WebSocket(buildWsUrl());
    ws.binaryType = "arraybuffer";
    term.loadAddon(new AttachAddon(ws));

    const onResize = () => {
      fit.fit();
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(
          JSON.stringify({ type: "resize", rows: term.rows, cols: term.cols }),
        );
      }
    };
    window.addEventListener("resize", onResize);

    return () => {
      window.removeEventListener("resize", onResize);
      try {
        ws.close();
      } catch {
        // ignore
      }
      term.dispose();
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className="h-full w-full p-2"
      style={{ background: "var(--color-bg)" }}
    />
  );
}
