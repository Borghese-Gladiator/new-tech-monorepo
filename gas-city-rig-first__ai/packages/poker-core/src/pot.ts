import type { PlayerState, Pot, Seat } from "./types.js";

/**
 * Build pots (main + side pots) from each player's total committed chips.
 * Folded players contribute their chips but are not eligible to win.
 *
 * Algorithm: at each contribution tier, every player who reached it
 * contributes (tier - prev) chips; eligible winners are non-folded players
 * who contributed at least that much.
 */
export function buildPots(players: ReadonlyArray<PlayerState>): ReadonlyArray<Pot> {
  const contributions = players
    .map((p) => ({ seat: p.seat, total: p.committedTotal, folded: p.status === "folded" }))
    .filter((p) => p.total > 0);
  if (contributions.length === 0) return [];

  const tiers = Array.from(new Set(contributions.map((p) => p.total))).sort((a, b) => a - b);

  const pots: Pot[] = [];
  let prev = 0;
  for (const tier of tiers) {
    const slice = tier - prev;
    if (slice <= 0) {
      prev = tier;
      continue;
    }
    const contributors = contributions.filter((p) => p.total >= tier);
    const amount = slice * contributors.length;
    const eligibleSeats: Seat[] = contributors
      .filter((p) => !p.folded)
      .map((p) => p.seat);
    pots.push({ amount, eligibleSeats });
    prev = tier;
  }
  return pots;
}
