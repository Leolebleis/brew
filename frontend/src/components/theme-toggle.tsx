import { useEffect, useState } from "react";

type Mode = "light" | "dark" | "system";

const ORDER: Mode[] = ["light", "dark", "system"];
const STORAGE_KEY = "brew.theme";

function readStored(): Mode {
  const v = localStorage.getItem(STORAGE_KEY);
  return v === "light" || v === "dark" || v === "system" ? v : "system";
}

function applyMode(mode: Mode): void {
  const root = document.documentElement;
  if (mode === "system") {
    root.removeAttribute("data-theme");
  } else {
    root.setAttribute("data-theme", mode);
  }
}

export function ThemeToggle() {
  const [mode, setMode] = useState<Mode>(() => readStored());

  useEffect(() => {
    applyMode(mode);
    localStorage.setItem(STORAGE_KEY, mode);
  }, [mode]);

  const next = () => {
    const idx = ORDER.indexOf(mode);
    setMode(ORDER[(idx + 1) % ORDER.length]);
  };

  const label = mode === "light" ? "☀" : mode === "dark" ? "☾" : "◐";

  return (
    <button
      type="button"
      onClick={next}
      aria-label={`Theme: ${mode}`}
      className="px-2 py-1 text-sm rounded border border-[color:var(--color-border)]"
    >
      {label}
    </button>
  );
}
