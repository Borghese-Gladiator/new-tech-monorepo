export type ConnectionState = "connected" | "reconnecting" | "disconnected";

const LABEL: Record<ConnectionState, string> = {
  connected: "Connected",
  reconnecting: "Reconnecting…",
  disconnected: "Disconnected",
};

const COLOR: Record<ConnectionState, string> = {
  connected: "bg-emerald-600",
  reconnecting: "bg-amber-500",
  disconnected: "bg-rose-600",
};

export function ConnectionPill({
  state,
}: {
  state: ConnectionState;
}): JSX.Element {
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold text-white ${COLOR[state]}`}
      role="status"
      aria-live="polite"
    >
      <span className="h-2 w-2 rounded-full bg-white/80" />
      {LABEL[state]}
    </span>
  );
}
