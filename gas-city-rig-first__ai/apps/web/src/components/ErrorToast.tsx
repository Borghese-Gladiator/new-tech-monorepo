"use client";

import { useEffect } from "react";

export type ErrorToastProps = {
  message: string;
  onDismiss: () => void;
  ttlMs?: number;
};

export function ErrorToast({
  message,
  onDismiss,
  ttlMs = 4000,
}: ErrorToastProps): JSX.Element {
  useEffect(() => {
    const timer = setTimeout(onDismiss, ttlMs);
    return () => clearTimeout(timer);
  }, [onDismiss, ttlMs]);

  return (
    <div
      role="alert"
      className="fixed bottom-6 right-6 z-50 max-w-sm rounded-lg bg-rose-700 px-4 py-3 text-white shadow-lg"
    >
      <div className="flex items-start gap-3">
        <span className="font-semibold">Error</span>
        <span className="flex-1 text-sm">{message}</span>
        <button
          type="button"
          onClick={onDismiss}
          aria-label="dismiss"
          className="text-white/80 hover:text-white"
        >
          ✕
        </button>
      </div>
    </div>
  );
}
