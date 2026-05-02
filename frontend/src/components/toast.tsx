import * as Toast from "@radix-ui/react-toast";
import { type ReactNode } from "react";

export function ToastProvider({ children }: { children: ReactNode }) {
  return (
    <Toast.Provider swipeDirection="right">
      {children}
      <Toast.Viewport className="fixed bottom-4 right-4 flex flex-col gap-2 w-[320px] max-w-[100vw] z-50" />
    </Toast.Provider>
  );
}

interface ToastItemProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  duration?: number;
  children?: ReactNode;
}

export function ToastItem({
  open,
  onOpenChange,
  title,
  duration = 60000,
  children,
}: ToastItemProps) {
  return (
    <Toast.Root
      open={open}
      onOpenChange={onOpenChange}
      duration={duration}
      className="bg-[color:var(--color-surface)] border border-[color:var(--color-border)] rounded-lg p-3 shadow-lg"
    >
      <Toast.Title className="font-semibold text-sm mb-1">{title}</Toast.Title>
      {children && <Toast.Description asChild>{children}</Toast.Description>}
      <Toast.Close
        className="absolute top-2 right-2 text-xs opacity-60 hover:opacity-100"
        aria-label="Dismiss"
      >
        ×
      </Toast.Close>
    </Toast.Root>
  );
}
