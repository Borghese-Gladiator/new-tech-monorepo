import type { Card, Deck, Rank, Suit } from "./types.js";
import type { Rng } from "./rng.js";
import { randInt } from "./rng.js";

const SUITS: ReadonlyArray<Suit> = ["c", "d", "h", "s"];
const RANKS: ReadonlyArray<Rank> = [
  "2",
  "3",
  "4",
  "5",
  "6",
  "7",
  "8",
  "9",
  "T",
  "J",
  "Q",
  "K",
  "A",
];

export function buildDeck(): Deck {
  const cards: Card[] = [];
  for (const suit of SUITS) {
    for (const rank of RANKS) {
      cards.push({ rank, suit });
    }
  }
  return cards;
}

export function shuffle(deck: Deck, rng: Rng): Deck {
  const out = deck.slice();
  for (let i = out.length - 1; i > 0; i--) {
    const j = randInt(rng, i + 1);
    const a = out[i];
    const b = out[j];
    if (a === undefined || b === undefined) continue;
    out[i] = b;
    out[j] = a;
  }
  return out;
}

export function cardId(card: Card): string {
  return `${card.rank}${card.suit}`;
}

export const RANK_VALUE: Readonly<Record<Rank, number>> = {
  "2": 2,
  "3": 3,
  "4": 4,
  "5": 5,
  "6": 6,
  "7": 7,
  "8": 8,
  "9": 9,
  T: 10,
  J: 11,
  Q: 12,
  K: 13,
  A: 14,
};
