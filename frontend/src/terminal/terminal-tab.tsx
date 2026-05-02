import { useEffect, useRef } from "react";
import { Terminal } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import { AttachAddon } from "@xterm/addon-attach";
import { WebglAddon } from "@xterm/addon-webgl";
import "@xterm/xterm/css/xterm.css";
import { API_BASE, API_KEY } from "../config";

function buildWsUrl(): string {
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
    });

    const fit = new FitAddon();
    term.loadAddon(fit);

    // WebglAddon's activate path raises asynchronously when WebGL2 is
    // unavailable (JSDOM, old browsers), so a sync try/catch around loadAddon
    // can't catch it — probe first.
    const probe = document.createElement("canvas");
    if (probe.getContext && probe.getContext("webgl2")) {
      term.loadAddon(new WebglAddon());
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
      ws.close();
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
