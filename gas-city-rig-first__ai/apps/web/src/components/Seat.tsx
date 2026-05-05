import type { Card as PokerCard, PlayerState, Seat as SeatNum } from "@gas-city/shared";
import { Card, CardBack } from "./Card";

export type SeatViewProps = {
  player: PlayerState;
  isCurrent: boolean;
  isLocal: boolean;
  displayName?: string;
  holeCards?: [PokerCard, PokerCard];
  flash?: boolean;
};

const STATUS_LABEL: Record<PlayerState["status"], string> = {
  active: "active",
  folded: "folded",
  all_in: "all-in",
};

function isSeated(seat: SeatNum, player: PlayerState): boolean {
  return seat === player.seat;
}

export function SeatView({
  player,
  isCurrent,
  isLocal,
  displayName,
  holeCards,
  flash,
}: SeatViewProps): JSX.Element {
  void isSeated; // referenced indirectly by callers
  const ring = isCurrent
    ? "ring-2 ring-amber-400"
    : "ring-1 ring-zinc-700/60";
  const flashClass = flash ? "animate-pulse" : "";
  return (
    <div
      data-seat={player.seat}
      className={`flex min-w-[180px] flex-col gap-2 rounded-xl bg-zinc-950/70 p-3 ${ring} ${flashClass}`}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="truncate font-semibold">
          {displayName ?? `Seat ${player.seat}`}
          {isLocal ? " (you)" : ""}
        </span>
        <span className="text-xs text-zinc-400">{STATUS_LABEL[player.status]}</span>
      </div>
      <div className="flex items-center justify-between gap-2 text-sm">
        <span className="text-zinc-300">
          stack: <span className="font-mono">{player.stack}</span>
        </span>
        <span className="text-zinc-400">
          bet: <span className="font-mono">{player.committedThisStreet}</span>
        </span>
      </div>
      <div className="flex gap-1">
        {holeCards ? (
          <>
            <Card card={holeCards[0]} />
            <Card card={holeCards[1]} />
          </>
        ) : player.status === "folded" ? (
          <span className="text-xs italic text-zinc-500">— folded —</span>
        ) : (
          <>
            <CardBack />
            <CardBack />
          </>
        )}
      </div>
    </div>
  );
}
