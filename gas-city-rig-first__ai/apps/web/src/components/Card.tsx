import type { Card as PokerCard } from "@gas-city/poker-core";

const SUIT_GLYPH: Record<PokerCard["suit"], string> = {
  c: "♣",
  d: "♦",
  h: "♥",
  s: "♠",
};

function suitColor(suit: PokerCard["suit"]): string {
  return suit === "h" || suit === "d" ? "text-red-400" : "text-zinc-100";
}

export function Card({ card }: { card: PokerCard }): JSX.Element {
  return (
    <span
      className={`inline-flex h-12 w-9 items-center justify-center rounded border border-zinc-700 bg-zinc-900 font-mono text-lg ${suitColor(card.suit)}`}
      aria-label={`${card.rank} of ${card.suit}`}
    >
      {card.rank}
      {SUIT_GLYPH[card.suit]}
    </span>
  );
}

export function CardBack(): JSX.Element {
  return (
    <span
      className="inline-flex h-12 w-9 items-center justify-center rounded border border-zinc-700 bg-emerald-900/80 font-mono text-lg text-emerald-300"
      aria-label="hidden card"
    >
      ?
    </span>
  );
}
