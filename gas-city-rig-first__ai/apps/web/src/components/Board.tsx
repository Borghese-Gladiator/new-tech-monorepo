import type { Card as PokerCard, Street } from "@gas-city/shared";
import { Card, CardBack } from "./Card";

const STREET_LABEL: Record<Street, string> = {
  preflop: "Preflop",
  flop: "Flop",
  turn: "Turn",
  river: "River",
  showdown: "Showdown",
};

const VISIBLE_BY_STREET: Record<Street, number> = {
  preflop: 0,
  flop: 3,
  turn: 4,
  river: 5,
  showdown: 5,
};

export function Board({
  community,
  street,
}: {
  community: ReadonlyArray<PokerCard>;
  street: Street;
}): JSX.Element {
  const visibleCount = VISIBLE_BY_STREET[street];
  return (
    <div className="flex flex-col items-center gap-2">
      <span className="text-xs uppercase tracking-wide text-zinc-400">
        {STREET_LABEL[street]}
      </span>
      <div className="flex gap-2">
        {Array.from({ length: 5 }).map((_, i) => {
          const card = i < visibleCount ? community[i] : undefined;
          return card ? (
            <Card key={i} card={card} />
          ) : (
            <CardBack key={i} />
          );
        })}
      </div>
    </div>
  );
}
