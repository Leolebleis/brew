import { useEffect, useReducer } from "react";
import { useDevice, useActiveBag, useWater } from "./hooks";
import { Button } from "../components/button";
import { ThemeToggle } from "../components/theme-toggle";
import { apiJson } from "../api/client";
import { BREW_POLL_UNTIL_KEY } from "../brewnow/submit";

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
  const until = Number(sessionStorage.getItem(BREW_POLL_UNTIL_KEY) ?? "0");
  return Date.now() < until;
}

function useDeviceShouldPoll(): boolean {
  // Re-read on every render so writes from other components in the same tab
  // are picked up immediately (e.g. brewNow() flipping the flag right before
  // this header re-renders for an unrelated reason).
  const flag = readPollFlag();
  const [, force] = useReducer((n: number) => n + 1, 0);
  useEffect(() => {
    if (!flag) return;
    const until = Number(sessionStorage.getItem(BREW_POLL_UNTIL_KEY) ?? "0");
    const remaining = until - Date.now();
    if (remaining <= 0) return;
    // One-shot timer: when the poll window expires, force a re-render so the
    // next readPollFlag() returns false.
    const t = setTimeout(force, remaining);
    return () => clearTimeout(t);
  }, [flag]);
  return flag;
}

function Elapsed({ startedAt }: { startedAt: string }) {
  const [, force] = useReducer((n: number) => n + 1, 0);
  useEffect(() => {
    const i = setInterval(force, 1000);
    return () => clearInterval(i);
  }, []);
  return <>{fmtElapsed(startedAt)}</>;
}

export function StatusHeader({ onBrew }: Props) {
  const shouldPoll = useDeviceShouldPoll();
  const device = useDevice({
    refetchIntervalMs: shouldPoll ? 5000 : false,
  });
  const activeBag = useActiveBag();
  const water = useWater();

  const refillWater = async () => {
    await apiJson<unknown>("/water/refill", { method: "POST" });
  };

  const renderBrewState = () => {
    if (!device.data?.brewing) return "Idle";
    if (!device.data.brew_started_at) return "Brewing…";
    return (
      <>
        Brewing <Elapsed startedAt={device.data.brew_started_at} />
      </>
    );
  };

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
        <span>{renderBrewState()}</span>
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
