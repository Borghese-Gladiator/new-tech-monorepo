import type {
  Action,
  ActionResult,
  GameEvent,
  GameState,
  PlayerState,
  Seat,
} from "./types.js";
import { isLegalAction } from "./legal.js";
import { buildPots } from "./pot.js";
import { getPlayer, nextSeatIn } from "./seating.js";

function replacePlayer(
  players: ReadonlyArray<PlayerState>,
  next: PlayerState,
): ReadonlyArray<PlayerState> {
  return players.map((p) => (p.seat === next.seat ? next : p));
}

export function applyAction(state: GameState, action: Action): ActionResult {
  const seat = state.currentSeat;
  if (seat === null) return { ok: false, reason: "no current actor" };
  const legal = isLegalAction(state, seat, action);
  if (!legal.ok) return { ok: false, reason: legal.reason ?? "illegal action" };
  const player = getPlayer(state, seat);
  if (!player) return { ok: false, reason: "no player at seat" };

  // The acting player consumes their reopen privilege: until someone raises again,
  // they may only call/check/fold on any subsequent re-prompt for the same street.
  let nextPlayer: PlayerState = {
    ...player,
    hasActedThisStreet: true,
    actionReopened: false,
  };
  let nextCurrentBet = state.currentBet;
  let nextLastRaiseSize = state.lastRaiseSize;
  let chipsCommittedNow = 0;
  let raiseReopens = false;

  switch (action.kind) {
    case "fold": {
      nextPlayer = { ...nextPlayer, status: "folded" };
      break;
    }
    case "check": {
      // no chip movement
      break;
    }
    case "call": {
      const toCall = Math.min(
        state.currentBet - player.committedThisStreet,
        player.stack,
      );
      chipsCommittedNow = toCall;
      nextPlayer = {
        ...nextPlayer,
        stack: player.stack - toCall,
        committedThisStreet: player.committedThisStreet + toCall,
        committedTotal: player.committedTotal + toCall,
        status: player.stack - toCall === 0 ? "all_in" : "active",
      };
      break;
    }
    case "raise": {
      const raiseTo = action.amount;
      const additional = raiseTo - player.committedThisStreet;
      chipsCommittedNow = additional;
      const raiseIncrement = raiseTo - state.currentBet;
      raiseReopens = raiseIncrement >= state.lastRaiseSize;
      nextCurrentBet = raiseTo;
      if (raiseReopens) {
        nextLastRaiseSize = raiseIncrement;
      }
      nextPlayer = {
        ...nextPlayer,
        stack: player.stack - additional,
        committedThisStreet: player.committedThisStreet + additional,
        committedTotal: player.committedTotal + additional,
        status: player.stack - additional === 0 ? "all_in" : "active",
      };
      break;
    }
  }

  let nextPlayers = replacePlayer(state.players, nextPlayer);

  // If raise reopened action (full raise), every other still-active player must act again
  // and regains the right to raise. A sub-minimum all-in does NOT reopen action for
  // seats that already acted — they keep actionReopened=false (set by their prior action).
  if (action.kind === "raise" && raiseReopens) {
    nextPlayers = nextPlayers.map((p) => {
      if (p.seat === nextPlayer.seat) return p;
      if (p.status !== "active") return p;
      return { ...p, hasActedThisStreet: false, actionReopened: true };
    });
  }

  const events: GameEvent[] = [
    { type: "action-taken", seat, action, amount: chipsCommittedNow },
  ];

  // Determine next actor
  const stillContending = nextPlayers.filter((p) => p.status !== "folded");
  const onePlayerLeft = stillContending.length === 1;

  let nextCurrentSeat: Seat | null = state.currentSeat;
  if (onePlayerLeft) {
    nextCurrentSeat = null;
  } else {
    nextCurrentSeat = nextSeatIn(
      nextPlayers,
      seat,
      (p) => p.status === "active" && !p.hasActedThisStreet,
    );
    // If everyone matched / acted, also see if anyone with mismatched committedThisStreet is still active.
    if (nextCurrentSeat === null) {
      const needsToAct = nextPlayers.some(
        (p) =>
          p.status === "active" &&
          (!p.hasActedThisStreet || p.committedThisStreet < nextCurrentBet),
      );
      if (needsToAct) {
        nextCurrentSeat = nextSeatIn(
          nextPlayers,
          seat,
          (p) =>
            p.status === "active" &&
            (!p.hasActedThisStreet || p.committedThisStreet < nextCurrentBet),
        );
      }
    }
  }

  const nextPots = buildPots(nextPlayers);

  const nextState: GameState = {
    ...state,
    players: nextPlayers,
    currentSeat: nextCurrentSeat,
    currentBet: nextCurrentBet,
    lastRaiseSize: nextLastRaiseSize,
    pots: nextPots,
  };

  return {
    ok: true,
    state: nextState,
    events: [...events, { type: "pot-updated", pots: nextPots }],
  };
}

export function isBettingRoundClosed(state: GameState): boolean {
  const contenders = state.players.filter((p) => p.status !== "folded");
  if (contenders.length <= 1) return true;
  const actives = state.players.filter((p) => p.status === "active");
  if (actives.length === 0) return true;
  const allMatched = actives.every(
    (p) => p.hasActedThisStreet && p.committedThisStreet === state.currentBet,
  );
  return allMatched;
}

export function isHandOver(state: GameState): boolean {
  const contenders = state.players.filter((p) => p.status !== "folded");
  return contenders.length <= 1;
}
