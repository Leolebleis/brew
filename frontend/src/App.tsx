import { useEffect } from "react";
import {
  AssistantRuntimeProvider,
  ComposerPrimitive,
  MessagePartPrimitive,
  MessagePrimitive,
  ThreadPrimitive,
} from "@assistant-ui/react";
import { ThemeToggle } from "./components/theme-toggle";
import { useChatRuntime } from "./chat/runtime";
import { loadInitialThread } from "./chat/replay";

function TextPart() {
  return <MessagePartPrimitive.Text />;
}

function ThreadMessage() {
  return (
    <MessagePrimitive.Root className="flex flex-col gap-1 px-4 py-2 text-sm">
      <MessagePrimitive.If user>
        <span className="self-end opacity-60 text-xs">You</span>
      </MessagePrimitive.If>
      <MessagePrimitive.If assistant>
        <span className="opacity-60 text-xs">Brew</span>
      </MessagePrimitive.If>
      <div className="whitespace-pre-wrap leading-relaxed">
        <MessagePrimitive.Parts components={{ Text: TextPart }} />
      </div>
    </MessagePrimitive.Root>
  );
}

function Thread() {
  return (
    <ThreadPrimitive.Root className="flex flex-col h-full">
      <ThreadPrimitive.Viewport className="flex-1 overflow-y-auto">
        <ThreadPrimitive.Empty>
          <div className="p-6 text-sm opacity-60">Start a conversation about your next brew.</div>
        </ThreadPrimitive.Empty>
        <ThreadPrimitive.Messages
          components={{
            UserMessage: ThreadMessage,
            AssistantMessage: ThreadMessage,
          }}
        />
      </ThreadPrimitive.Viewport>
      <ComposerPrimitive.Root className="flex gap-2 p-4 border-t border-[color:var(--color-border)]">
        <ComposerPrimitive.Input
          autoFocus
          placeholder="Message Brew..."
          className="flex-1 bg-transparent outline-none text-sm placeholder:opacity-50"
        />
        <ComposerPrimitive.Send className="px-3 py-1 text-sm rounded border border-[color:var(--color-border)] disabled:opacity-40">
          Send
        </ComposerPrimitive.Send>
      </ComposerPrimitive.Root>
    </ThreadPrimitive.Root>
  );
}

export default function App() {
  const runtime = useChatRuntime();

  useEffect(() => {
    loadInitialThread().catch((err) => console.error("Initial thread load failed:", err));
  }, []);

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <div className="min-h-dvh flex flex-col">
        <header className="flex justify-between items-center p-4 border-b border-[color:var(--color-border)]">
          <span className="font-semibold uppercase text-xs tracking-wide" style={{ color: "var(--color-primary)" }}>Brew</span>
          <div className="flex gap-2 items-center">
            <span className="text-xs opacity-60">Status header — Phase 3</span>
            <ThemeToggle />
          </div>
        </header>
        <main className="flex-1 overflow-hidden">
          <Thread />
        </main>
      </div>
    </AssistantRuntimeProvider>
  );
}
