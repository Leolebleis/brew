import { useState } from "react";
import { ToastItem } from "../components/toast";
import { apiJson } from "../api/client";

interface Props {
  entryId: string;
  open: boolean;
  onClose: () => void;
}

export function RatingToast({ entryId, open, onClose }: Props) {
  const [submitting, setSubmitting] = useState(false);

  const rate = async (n: number) => {
    setSubmitting(true);
    try {
      await apiJson<unknown>(`/journal/${entryId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rating: n }),
      });
      onClose();
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <ToastItem open={open} onOpenChange={(v) => !v && onClose()} title="How was it?">
      <div className="flex gap-1 mt-1">
        {[1, 2, 3, 4, 5].map((n) => (
          <button
            key={n}
            type="button"
            disabled={submitting}
            onClick={() => rate(n)}
            aria-label={`Rate ${n} star${n === 1 ? "" : "s"}`}
            className="text-2xl leading-none disabled:opacity-50"
            style={{ color: "var(--color-accent)" }}
          >
            ☆
          </button>
        ))}
      </div>
    </ToastItem>
  );
}
