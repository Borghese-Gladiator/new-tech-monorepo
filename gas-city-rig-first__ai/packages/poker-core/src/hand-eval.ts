import type { Card, Suit } from "./types.js";
import { RANK_VALUE } from "./deck.js";

/**
 * Hand category, higher is better.
 */
export type HandCategory =
  | "high_card"
  | "pair"
  | "two_pair"
  | "trips"
  | "straight"
  | "flush"
  | "full_house"
  | "quads"
  | "straight_flush";

const CATEGORY_RANK: Record<HandCategory, number> = {
  high_card: 1,
  pair: 2,
  two_pair: 3,
  trips: 4,
  straight: 5,
  flush: 6,
  full_house: 7,
  quads: 8,
  straight_flush: 9,
};

export type HandValue = {
  category: HandCategory;
  /**
   * Tiebreaker tuple. Compared lexicographically. Always 5 numbers (rank values 2..14).
   * E.g. straight_flush [14] would be padded with kickers; we always pad to 5 for trivial comparison.
   */
  ranks: ReadonlyArray<number>;
};

export function compareHandValues(a: HandValue, b: HandValue): number {
  const da = CATEGORY_RANK[a.category];
  const db = CATEGORY_RANK[b.category];
  if (da !== db) return da - db;
  for (let i = 0; i < Math.min(a.ranks.length, b.ranks.length); i++) {
    const av = a.ranks[i] ?? 0;
    const bv = b.ranks[i] ?? 0;
    if (av !== bv) return av - bv;
  }
  return 0;
}

export function evaluateBest5(cards: ReadonlyArray<Card>): HandValue {
  if (cards.length < 5) {
    throw new Error("evaluateBest5: need at least 5 cards");
  }
  let best: HandValue | null = null;
  const idxs = combinations(cards.length, 5);
  for (const combo of idxs) {
    const five: Card[] = [];
    for (const i of combo) {
      const c = cards[i];
      if (c) five.push(c);
    }
    const v = evaluate5(five);
    if (best === null || compareHandValues(v, best) > 0) {
      best = v;
    }
  }
  if (!best) throw new Error("evaluateBest5: no hand found");
  return best;
}

function combinations(n: number, k: number): ReadonlyArray<ReadonlyArray<number>> {
  const out: number[][] = [];
  const idx: number[] = [];
  function rec(start: number, depth: number): void {
    if (depth === k) {
      out.push(idx.slice());
      return;
    }
    for (let i = start; i < n; i++) {
      idx.push(i);
      rec(i + 1, depth + 1);
      idx.pop();
    }
  }
  rec(0, 0);
  return out;
}

function evaluate5(cards: ReadonlyArray<Card>): HandValue {
  const ranks: number[] = cards
    .map((c) => RANK_VALUE[c.rank])
    .slice()
    .sort((a, b) => b - a);
  const suits: Suit[] = cards.map((c) => c.suit);

  const flush = suits.every((s) => s === suits[0]);
  const straightHigh = checkStraight(ranks);
  const isStraight = straightHigh !== null;

  if (flush && isStraight) {
    return { category: "straight_flush", ranks: [straightHigh, 0, 0, 0, 0] };
  }

  const counts = countByRank(ranks);

  // quads
  const quad = counts.find((g) => g.count === 4);
  if (quad) {
    const kicker = ranks.find((r) => r !== quad.rank) ?? 0;
    return { category: "quads", ranks: [quad.rank, kicker, 0, 0, 0] };
  }
  // full house
  const trips = counts.find((g) => g.count === 3);
  const pairs = counts.filter((g) => g.count === 2).map((g) => g.rank).sort((a, b) => b - a);
  if (trips && pairs.length >= 1) {
    const pair0 = pairs[0] ?? 0;
    return { category: "full_house", ranks: [trips.rank, pair0, 0, 0, 0] };
  }
  if (flush) {
    return { category: "flush", ranks: ranks.slice(0, 5) };
  }
  if (isStraight) {
    return { category: "straight", ranks: [straightHigh, 0, 0, 0, 0] };
  }
  if (trips) {
    const kickers = ranks.filter((r) => r !== trips.rank).slice(0, 2);
    return { category: "trips", ranks: [trips.rank, ...kickers, 0, 0].slice(0, 5) };
  }
  if (pairs.length >= 2) {
    const high = pairs[0] ?? 0;
    const low = pairs[1] ?? 0;
    const kicker = ranks.find((r) => r !== high && r !== low) ?? 0;
    return { category: "two_pair", ranks: [high, low, kicker, 0, 0] };
  }
  if (pairs.length === 1) {
    const pair0 = pairs[0] ?? 0;
    const kickers = ranks.filter((r) => r !== pair0).slice(0, 3);
    return { category: "pair", ranks: [pair0, ...kickers, 0].slice(0, 5) };
  }
  return { category: "high_card", ranks: ranks.slice(0, 5) };
}

function countByRank(ranksDesc: ReadonlyArray<number>): ReadonlyArray<{
  rank: number;
  count: number;
}> {
  const map = new Map<number, number>();
  for (const r of ranksDesc) {
    map.set(r, (map.get(r) ?? 0) + 1);
  }
  return Array.from(map.entries())
    .map(([rank, count]) => ({ rank, count }))
    .sort((a, b) => {
      if (a.count !== b.count) return b.count - a.count;
      return b.rank - a.rank;
    });
}

function checkStraight(ranksDesc: ReadonlyArray<number>): number | null {
  // Unique sorted descending
  const unique = Array.from(new Set(ranksDesc)).sort((a, b) => b - a);
  if (unique.length < 5) return null;
  // Wheel: A-2-3-4-5
  if (
    unique.includes(14) &&
    unique.includes(2) &&
    unique.includes(3) &&
    unique.includes(4) &&
    unique.includes(5)
  ) {
    // wheel high is 5
    // but a higher straight may also exist — keep checking
    let highest: number | null = 5;
    for (let i = 0; i <= unique.length - 5; i++) {
      const a = unique[i];
      const b = unique[i + 1];
      const c = unique[i + 2];
      const d = unique[i + 3];
      const e = unique[i + 4];
      if (
        a !== undefined &&
        b !== undefined &&
        c !== undefined &&
        d !== undefined &&
        e !== undefined &&
        a - 1 === b &&
        b - 1 === c &&
        c - 1 === d &&
        d - 1 === e
      ) {
        if (highest === null || a > highest) highest = a;
      }
    }
    return highest;
  }
  for (let i = 0; i <= unique.length - 5; i++) {
    const a = unique[i];
    const b = unique[i + 1];
    const c = unique[i + 2];
    const d = unique[i + 3];
    const e = unique[i + 4];
    if (
      a !== undefined &&
      b !== undefined &&
      c !== undefined &&
      d !== undefined &&
      e !== undefined &&
      a - 1 === b &&
      b - 1 === c &&
      c - 1 === d &&
      d - 1 === e
    ) {
      return a;
    }
  }
  return null;
}

