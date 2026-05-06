import type { GameEvent, GameState, PlayerState, Pot, Seat } from "./types.js";
import { compareHandValues, evaluateBest5 } from "./hand-eval.js";
import type { HandValue } from "./hand-eval.js";

export type ShowdownResult = {
  state: GameState;
  events: ReadonlyArray<GameEvent>;
};

/**
 * Resolve a hand (showdown OR everyone-folded). Distributes each pot to its
 * eligible best hand(s). Splits chip remainders favoring the earliest seat
 * (lowest seat number) so the result is fully deterministic.
 */
export function resolveHand(state: GameState): ShowdownResult {
  const events: GameEvent[] = [];
  const winners: { seat: Seat; amount: number; potIndex: number }[] = [];
  const stackUpdates = new Map<Seat, number>();
  for (const p of state.players) stackUpdates.set(p.seat, p.stack);

  const evaluated = new Map<Seat, HandValue>();
  for (const p of state.players) {
    if (p.status === "folded") continue;
    const seven = [...p.holeCards, ...state.community];
    if (seven.length >= 5) {
      evaluated.set(p.seat, evaluateBest5(seven));
    }
  }

  state.pots.forEach((pot: Pot, idx: number) => {
    const candidates = pot.eligibleSeats
      .map((s) => ({ seat: s, value: evaluated.get(s) }))
      .filter((c): c is { seat: Seat; value: HandValue } => c.value !== undefined);
    if (candidates.length === 0) {
      // Everyone folded out of this pot — pay it to whichever non-folded seat is eligible.
      // (This case mostly arises when the pot is entirely from folded players' contributions
      // and the only contender wasn't on this pot's eligible list — should not happen with
      // correct buildPots, but degrade gracefully.)
      const fallback = state.players.find((p) => p.status !== "folded");
      if (fallback) {
        stackUpdates.set(fallback.seat, (stackUpdates.get(fallback.seat) ?? 0) + pot.amount);
        winners.push({ seat: fallback.seat, amount: pot.amount, potIndex: idx });
      }
      return;
    }
    candidates.sort((a, b) => compareHandValues(b.value, a.value));
    const top = candidates[0];
    if (!top) return;
    const tied = candidates.filter((c) => compareHandValues(c.value, top.value) === 0);
    const each = Math.floor(pot.amount / tied.length);
    let remainder = pot.amount - each * tied.length;
    const sortedTied = tied.slice().sort((a, b) => a.seat - b.seat);
    for (const t of sortedTied) {
      let prize = each;
      if (remainder > 0) {
        prize += 1;
        remainder -= 1;
      }
      stackUpdates.set(t.seat, (stackUpdates.get(t.seat) ?? 0) + prize);
      winners.push({ seat: t.seat, amount: prize, potIndex: idx });
    }
  });

  const nextPlayers: ReadonlyArray<PlayerState> = state.players.map((p) => ({
    ...p,
    stack: stackUpdates.get(p.seat) ?? p.stack,
    committedThisStreet: 0,
    committedTotal: 0,
    hasActedThisStreet: false,
    actionReopened: true,
  }));

  events.push({ type: "hand-resolved", winners });

  const nextState: GameState = {
    ...state,
    players: nextPlayers,
    pots: [],
    currentSeat: null,
    street: "showdown",
  };
  return { state: nextState, events };
}
