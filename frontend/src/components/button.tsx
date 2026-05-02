import { forwardRef, type ButtonHTMLAttributes } from "react";

type Variant = "primary" | "ghost" | "destructive";

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
}

const STYLES: Record<Variant, string> = {
  primary:
    "bg-[color:var(--color-primary)] text-[color:var(--color-on-primary)] hover:opacity-90",
  ghost:
    "bg-transparent text-[color:var(--color-fg)] border border-[color:var(--color-border)] hover:bg-[color:var(--color-surface)]",
  destructive:
    "bg-[color:var(--color-destructive)] text-white hover:opacity-90 destructive",
};

export const Button = forwardRef<HTMLButtonElement, Props>(function Button(
  { variant = "primary", className = "", ...rest },
  ref,
) {
  return (
    <button
      ref={ref}
      type="button"
      className={`px-4 py-2 rounded-md font-medium text-sm transition-opacity disabled:opacity-50 disabled:cursor-not-allowed ${STYLES[variant]} ${className}`}
      {...rest}
    />
  );
});
