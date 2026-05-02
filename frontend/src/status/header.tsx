import { useEffect, useState } from "react";
import { useDevice, useActiveBag, useWater } from "./hooks";
import { Button } from "../components/button";
import { ThemeToggle } from "../components/theme-toggle";
import { apiFetch } from "../api/client";

interface Props {
  onBrew: () => void;
}

function fmtElapsed(startedAt: string): string {
  const start = new Date(startedAt).getTime();
  const elapsedSec = Math.max(0, Math.floor((Date.now() - start) / 1000));
  const m = Math.floor(elapsedSec / 60);
  const s = elapsedSec % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

function readPollFlag(): boolean {
  const until = Number(sessionStorage.getItem("brew.pollUntil") ?? "0");
  return Date.now() < until;
}

function useDeviceShouldPoll(): boolean {
  const [poll, setPoll] = useState<boolean>(() => readPollFlag());
  useEffect(() => {
    const tick = setInterval(() => setPoll(readPollFlag()), 1000);
    return () => clearInterval(tick);
  }, []);
  return poll;
}

export function StatusHeader({ onBrew }: Props) {
  const shouldPoll = useDeviceShouldPoll();
  const device = useDevice({
    refetchIntervalMs: shouldPoll ? 5000 : false,
  });
  const activeBag = useActiveBag();
  const water = useWater();

  const [, tick] = useState(0);
  useEffect(() => {
    if (!device.data?.brewing) return;
    const i = setInterval(() => tick((n) => n + 1), 1000);
    return () => clearInterval(i);
  }, [device.data?.brewing]);

  const refillWater = async () => {
    await apiFetch("/water/refill", { method: "POST" });
  };

  const brewState = device.data?.brewing
    ? device.data.brew_started_at
      ? `Brewing ${fmtElapsed(device.data.brew_started_at)}`
      : "Brewing…"
    : "Idle";

  const bagText = activeBag.data
    ? `${activeBag.data.name} · ${activeBag.data.remaining_grams} g`
    : "No active bag";
  const waterText = water.data ? `${water.data.remaining_ml} mL` : "—";

  const brewDisabled =
    !!device.data?.brewing || !activeBag.data || (water.data?.remaining_ml ?? 0) <= 0;

  return (
    <header className="sticky top-0 z-10 bg-[color:var(--color-surface)] border-b border-[color:var(--color-border)] p-3 flex flex-wrap gap-3 items-center justify-between">
      <div className="flex flex-wrap gap-3 items-center text-sm">
        <span
          className="font-semibold uppercase text-xs tracking-wide"
          style={{ color: "var(--color-primary)" }}
        >
          Brew
        </span>
        <span>{brewState}</span>
        <span style={{ color: "var(--color-fg-muted)" }}>·</span>
        <span>{bagText}</span>
        <span style={{ color: "var(--color-fg-muted)" }}>·</span>
        <span>{waterText}</span>
        <Button variant="ghost" onClick={refillWater} className="text-xs px-2 py-1">
          Refill
        </Button>
      </div>
      <div className="flex gap-2 items-center">
        <Button onClick={onBrew} disabled={brewDisabled}>
          Brew now
        </Button>
        <ThemeToggle />
      </div>
    </header>
  );
}
