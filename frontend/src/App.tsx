import { ThemeToggle } from "./components/theme-toggle";

export default function App() {
  return (
    <div className="min-h-dvh flex flex-col">
      <header className="flex justify-between items-center p-4 border-b border-[color:var(--color-border)]">
        <span className="font-semibold uppercase text-xs tracking-wide" style={{ color: "var(--color-primary)" }}>Brew</span>
        <ThemeToggle />
      </header>
      <main className="flex-1 p-4">
        <p style={{ color: "var(--color-fg-muted)" }}>Frontend shell — chat surface lands in Task 16.</p>
      </main>
    </div>
  );
}
