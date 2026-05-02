import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { StatusHeader } from "./status/header";
import { startStatusEventListener } from "./status/event-listener";
import { BrewNowSheet } from "./brewnow/sheet";
import { RatingToast } from "./rating/toast";
import { ToastProvider } from "./components/toast";
import { TerminalTab } from "./terminal/terminal-tab";

export default function App() {
  const qc = useQueryClient();
  const [brewOpen, setBrewOpen] = useState(false);
  const [pendingRating, setPendingRating] = useState<string | null>(null);

  useEffect(() => {
    const ac = new AbortController();
    startStatusEventListener(qc, (entryId) => setPendingRating(entryId), ac.signal);
    return () => ac.abort();
  }, [qc]);

  return (
    <ToastProvider>
      <div className="min-h-dvh flex flex-col">
        <StatusHeader onBrew={() => setBrewOpen(true)} />
        <main className="flex-1 overflow-hidden">
          <TerminalTab />
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
  );
}
