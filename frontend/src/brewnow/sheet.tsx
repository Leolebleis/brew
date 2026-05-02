import { useState } from "react";
import { useDevice, useActiveBag } from "../status/hooks";
import { Sheet } from "../components/sheet";
import { Button } from "../components/button";
import { brewNow } from "./submit";

interface Props {
  open: boolean;
  onClose: () => void;
}

function Check({ label, ok }: { label: string; ok: boolean }) {
  return (
    <li className="flex items-center gap-2">
      <span style={{ color: ok ? "var(--color-success)" : "var(--color-destructive)" }}>{ok ? "✓" : "✗"}</span>
      {label}
    </li>
  );
}

export function BrewNowSheet({ open, onClose }: Props) {
  const device = useDevice();
  const activeBag = useActiveBag();
  const [waterMlOverride, setWaterMlOverride] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const targetVolume = activeBag.data?.profile_snapshot?.target_volume;
  const defaultWaterMl = typeof targetVolume === "number" ? targetVolume : 250;
  const waterMl = waterMlOverride ?? defaultWaterMl;

  const lid = device.data?.lid_closed === true;
  const basket = device.data?.basket_present === true;
  const carafe = device.data?.carafe_present === true;
  const allGreen = lid && basket && carafe;
  const canSubmit = !!activeBag.data && allGreen && !submitting && waterMl > 0;

  const submit = async () => {
    if (!activeBag.data?.profile_id) return;
    setSubmitting(true);
    setError(null);
    try {
      await brewNow(activeBag.data.profile_id, waterMl);
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Sheet open={open} onOpenChange={(v) => !v && onClose()} title="Brew now">
      <div className="space-y-3">
        <div>
          <div className="text-xs uppercase tracking-wide" style={{ color: "var(--color-fg-muted)" }}>Bag</div>
          <div>{activeBag.data?.name ?? "—"}</div>
        </div>
        <div>
          <label className="text-xs uppercase tracking-wide block mb-1" style={{ color: "var(--color-fg-muted)" }}>Water (mL)</label>
          <input
            type="number"
            value={waterMl}
            onChange={(e) => setWaterMlOverride(Number(e.target.value))}
            className="bg-[color:var(--color-bg)] border border-[color:var(--color-border)] rounded px-2 py-1 w-32"
          />
        </div>
        <ul className="text-sm space-y-1">
          <Check label="Lid closed" ok={lid} />
          <Check label="Basket in" ok={basket} />
          <Check label="Carafe in" ok={carafe} />
        </ul>
        {error && <div className="text-sm" style={{ color: "var(--color-destructive)" }}>{error}</div>}
        <div className="flex gap-2 justify-end pt-2">
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button onClick={submit} disabled={!canSubmit}>
            {submitting ? "Starting…" : "Brew now"}
          </Button>
        </div>
      </div>
    </Sheet>
  );
}
