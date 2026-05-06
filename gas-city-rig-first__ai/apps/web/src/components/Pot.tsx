import type { PlayerState, Pot as PotType } from "@gas-city/shared";
import { meaningfulSidePotCount } from "@/lib/pot";

export function Pot({
  pots,
  players,
}: {
  pots: ReadonlyArray<PotType>;
  players: ReadonlyArray<PlayerState>;
}): JSX.Element {
  const total = pots.reduce((acc, p) => acc + p.amount, 0);
  const sidePots = meaningfulSidePotCount(pots, players);
  return (
    <div className="flex flex-col items-center gap-1 text-sm text-zinc-300">
      <span className="text-xs uppercase tracking-wide text-zinc-400">Pot</span>
      <span className="font-mono text-2xl text-zinc-100">{total}</span>
      {sidePots > 0 ? (
        <span className="text-xs text-zinc-400">
          {sidePots === 1 ? "1 side pot" : `${sidePots} side pots`}
        </span>
      ) : null}
    </div>
  );
}
