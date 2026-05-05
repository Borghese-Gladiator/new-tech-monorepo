import type { GameEvent, GameState, PlayerState, Street } from "./types.js";
import { dealFlop, dealRiver, dealTurn } from "./deal.js";
import { isBettingRoundClosed, isHandOver } from "./betting.js";
import { firstToActPostflop } from "./seating.js";

const NEXT_STREET: Record<Street, Street> = {
  preflop: "flop",
  flop: "turn",
  turn: "river",
  river: "showdown",
  showdown: "showdown",
};

export type AdvanceResult = {
  ok: true;
  state: GameState;
  events: ReadonlyArray<GameEvent>;
} | {
  ok: false;
  reason: string;
};

export function advanceStreet(state: GameState): AdvanceResult {
  if (state.street === "showdown") {
    return { ok: false, reason: "already at showdown" };
  }
  if (!isBettingRoundClosed(state)) {
    return { ok: false, reason: "betting round not closed" };
  }
  const nextStreet = NEXT_STREET[state.street];
  let nextDeck = state.deck;
  let nextCommunity = state.community;
  const events: GameEvent[] = [];

  if (!isHandOver(state)) {
    if (nextStreet === "flop") {
      const r = dealFlop(state);
      nextDeck = r.deck;
      nextCommunity = r.community;
      events.push(...r.events);
    } else if (nextStreet === "turn") {
      const r = dealTurn(state);
      nextDeck = r.deck;
      nextCommunity = r.community;
      events.push(...r.events);
    } else if (nextStreet === "river") {
      const r = dealRiver(state);
      nextDeck = r.deck;
      nextCommunity = r.community;
      events.push(...r.events);
    }
  }

  const resetPlayers: ReadonlyArray<PlayerState> = state.players.map((p) => ({
    ...p,
    committedThisStreet: 0,
    hasActedThisStreet: false,
    actionReopened: true,
  }));

  const nextCurrentSeat =
    isHandOver(state) || nextStreet === "showdown"
      ? null
      : firstToActPostflop(resetPlayers, state.buttonSeat);

  events.push({ type: "street-advanced", from: state.street, to: nextStreet });

  const nextState: GameState = {
    ...state,
    deck: nextDeck,
    community: nextCommunity,
    players: resetPlayers,
    street: nextStreet,
    currentSeat: nextCurrentSeat,
    currentBet: 0,
    lastRaiseSize: 0,
  };
  return { ok: true, state: nextState, events };
}
