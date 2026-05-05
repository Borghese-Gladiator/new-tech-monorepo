import type { Pot as PotType } from "@gas-city/shared";

export function Pot({ pots }: { pots: ReadonlyArray<PotType> }): JSX.Element {
  const total = pots.reduce((acc, p) => acc + p.amount, 0);
  return (
    <div className="flex flex-col items-center gap-1 text-sm text-zinc-300">
      <span className="text-xs uppercase tracking-wide text-zinc-400">Pot</span>
      <span className="font-mono text-2xl text-zinc-100">{total}</span>
      {pots.length > 1 ? (
        <span className="text-xs text-zinc-400">
          {pots.length} side pots
        </span>
      ) : null}
    </div>
  );
}
