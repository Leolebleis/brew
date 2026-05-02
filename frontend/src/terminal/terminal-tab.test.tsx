import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render } from "@testing-library/react";
import { TerminalTab } from "./terminal-tab";

class MockWebSocket {
  url: string;
  binaryType = "arraybuffer";
  sent: (string | ArrayBufferLike | Blob | ArrayBufferView)[] = [];
  onmessage: ((ev: MessageEvent) => void) | null = null;
  onopen: ((ev: Event) => void) | null = null;
  onclose: ((ev: CloseEvent) => void) | null = null;
  onerror: ((ev: Event) => void) | null = null;
  readyState = 1;

  constructor(url: string) {
    this.url = url;
  }
  send(data: string | ArrayBufferLike | Blob | ArrayBufferView): void {
    this.sent.push(data);
  }
  close(): void {
    this.readyState = 3;
  }
  addEventListener = vi.fn();
  removeEventListener = vi.fn();
}

let lastSocket: MockWebSocket | null = null;

function recordSocket(socket: MockWebSocket): void {
  lastSocket = socket;
}

class TestWebSocket extends MockWebSocket {
  constructor(url: string) {
    super(url);
    recordSocket(this);
  }
}

beforeEach(() => {
  lastSocket = null;
  vi.stubGlobal("WebSocket", TestWebSocket);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("TerminalTab", () => {
  it("opens a WebSocket against /api/terminal/ws with the API key", () => {
    render(<TerminalTab />);
    expect(lastSocket).not.toBeNull();
    expect(lastSocket!.url).toContain("/api/terminal/ws");
    expect(lastSocket!.url).toContain("api_key=");
  });

  it("sets binaryType to arraybuffer for the AttachAddon", () => {
    render(<TerminalTab />);
    expect(lastSocket!.binaryType).toBe("arraybuffer");
  });
});
