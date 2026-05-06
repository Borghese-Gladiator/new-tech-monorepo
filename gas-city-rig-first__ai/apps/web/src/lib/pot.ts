import type { PlayerState, Pot } from "@gas-city/shared";

// buildPots creates a separate pot entry per contribution tier, so asymmetric
// blinds (heads-up SB+BB preflop, no all-in) produce 2 pot entries even though
// no real side pot exists. Players read "N side pots" as "someone went all-in",
// so only count side pots when an all-in is actually responsible for them.
export function meaningfulSidePotCount(
  pots: ReadonlyArray<Pot>,
  players: ReadonlyArray<PlayerState>,
): number {
  if (pots.length <= 1) return 0;
  const anyAllIn = players.some((p) => p.status === "all_in");
  if (!anyAllIn) return 0;
  return pots.length - 1;
}
