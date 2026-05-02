import { useEffect, useState } from "react";
import {
  AssistantRuntimeProvider,
  ComposerPrimitive,
  MessagePartPrimitive,
  MessagePrimitive,
  ThreadPrimitive,
} from "@assistant-ui/react";
import { useQueryClient } from "@tanstack/react-query";
import { useChatRuntime } from "./chat/runtime";
import { loadInitialThread } from "./chat/replay";
import { StatusHeader } from "./status/header";
import { startStatusEventListener } from "./status/event-listener";
import { BrewNowSheet } from "./brewnow/sheet";
import { RatingToast } from "./rating/toast";
import { ToastProvider } from "./components/toast";

// MessagePartPrimitive.Text is a span ref-forwarder; the components.Text slot
// expects a TextMessagePartComponent (a function component). This shim bridges
// the two — don't inline.
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
  const qc = useQueryClient();
  const [brewOpen, setBrewOpen] = useState(false);
  const [pendingRating, setPendingRating] = useState<string | null>(null);

  useEffect(() => {
    loadInitialThread().catch((err) => console.error("Initial thread load failed:", err));
  }, []);

  useEffect(() => {
    const ac = new AbortController();
    startStatusEventListener(qc, (entryId) => setPendingRating(entryId), ac.signal);
    return () => ac.abort();
  }, [qc]);

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <ToastProvider>
        <div className="min-h-dvh flex flex-col">
          <StatusHeader onBrew={() => setBrewOpen(true)} />
          <main className="flex-1 overflow-hidden">
            <Thread />
          </main>
          <BrewNowSheet open={brewOpen} onClose={() => setBrewOpen(false)} />
          {pendingRating && (
            <RatingToast
              entryId={pendingRating}
              open={true}
              onClose={() => setPendingRating(null)}
            />
          )}
        </div>
      </ToastProvider>
    </AssistantRuntimeProvider>
  );
}
