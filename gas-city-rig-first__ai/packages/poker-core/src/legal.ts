import type { Action, GameState, Seat } from "./types.js";
import { getPlayer } from "./seating.js";

export type LegalActionsResult = {
  canFold: boolean;
  canCheck: boolean;
  canCall: boolean;
  callAmount: number;
  canRaise: boolean;
  minRaiseTo: number;
  maxRaiseTo: number;
};

export function legalActions(state: GameState, seat: Seat): LegalActionsResult {
  const player = getPlayer(state, seat);
  const empty: LegalActionsResult = {
    canFold: false,
    canCheck: false,
    canCall: false,
    callAmount: 0,
    canRaise: false,
    minRaiseTo: 0,
    maxRaiseTo: 0,
  };
  if (!player) return empty;
  if (player.status !== "active") return empty;
  if (state.currentSeat !== seat) return empty;

  const toCall = Math.max(0, state.currentBet - player.committedThisStreet);
  const facingBet = toCall > 0;
  const canFold = facingBet;
  const canCheck = !facingBet;
  const canCall = facingBet && player.stack > 0;
  const callAmount = Math.min(toCall, player.stack);

  // raise sizing — "raise" amount is total chips committed this street after the raise (raise-to)
  const stackTotalCommittable = player.committedThisStreet + player.stack;
  const minRaiseIncrement = state.lastRaiseSize > 0 ? state.lastRaiseSize : state.config.blinds.bb;
  const minRaiseToRaw = state.currentBet + minRaiseIncrement;
  const maxRaiseTo = stackTotalCommittable;
  const minRaiseTo = Math.min(minRaiseToRaw, maxRaiseTo);
  const canRaise = maxRaiseTo > state.currentBet && player.stack > toCall;

  return {
    canFold,
    canCheck,
    canCall,
    callAmount,
    canRaise,
    minRaiseTo,
    maxRaiseTo,
  };
}

export function isLegalAction(state: GameState, seat: Seat, action: Action): {
  ok: boolean;
  reason?: string;
} {
  const opts = legalActions(state, seat);
  switch (action.kind) {
    case "fold":
      if (!opts.canFold) return { ok: false, reason: "cannot fold (no bet to face)" };
      return { ok: true };
    case "check":
      if (!opts.canCheck) return { ok: false, reason: "cannot check facing a bet" };
      return { ok: true };
    case "call":
      if (!opts.canCall) return { ok: false, reason: "cannot call (no bet or no chips)" };
      return { ok: true };
    case "raise": {
      if (!opts.canRaise) return { ok: false, reason: "cannot raise" };
      if (action.amount < opts.minRaiseTo && action.amount !== opts.maxRaiseTo) {
        return {
          ok: false,
          reason: `raise amount ${action.amount} below min ${opts.minRaiseTo}`,
        };
      }
      if (action.amount > opts.maxRaiseTo) {
        return {
          ok: false,
          reason: `raise amount ${action.amount} exceeds stack`,
        };
      }
      return { ok: true };
    }
  }
}
