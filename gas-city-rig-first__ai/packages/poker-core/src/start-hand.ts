import type { GameConfig, GameEvent, GameState, PlayerState, Seat } from "./types.js";
import { buildDeck, shuffle } from "./deck.js";
import { mulberry32 } from "./rng.js";
import { dealHoleCards } from "./deal.js";
import { bigBlindSeat, firstToActPreflop, smallBlindSeat } from "./seating.js";
import { buildPots } from "./pot.js";

export type StartHandOptions = {
  config: GameConfig;
  /** Optional override for the player base — if provided, must have length === config.numSeats. */
  players?: ReadonlyArray<{ seat: Seat; stack: number }>;
};

export type StartHandResult = {
  state: GameState;
  events: ReadonlyArray<GameEvent>;
};

export function startHand(opts: StartHandOptions): StartHandResult {
  const { config } = opts;
  const seedRng = mulberry32(config.seed);
  const shuffledDeck = shuffle(buildDeck(), seedRng);
  const seats = Array.from({ length: config.numSeats }, (_, i) => i as Seat);
  const base = opts.players ?? seats.map((s) => ({ seat: s, stack: config.startingStacks }));

  let players: PlayerState[] = base.map((p) => ({
    seat: p.seat,
    stack: p.stack,
    holeCards: [],
    status: "active",
    committedThisStreet: 0,
    committedTotal: 0,
    hasActedThisStreet: false,
    actionReopened: true,
  }));

  const sb = smallBlindSeat(players, config.buttonSeat);
  const bb = bigBlindSeat(players, config.buttonSeat);
  if (sb === null || bb === null) {
    throw new Error("startHand: cannot determine blinds");
  }

  const events: GameEvent[] = [
    { type: "hand-started", handId: 1, buttonSeat: config.buttonSeat },
  ];

  // Post blinds
  players = players.map((p) => {
    if (p.seat === sb) {
      const post = Math.min(config.blinds.sb, p.stack);
      return {
        ...p,
        stack: p.stack - post,
        committedThisStreet: post,
        committedTotal: post,
        status: p.stack - post === 0 ? "all_in" : "active",
      };
    }
    if (p.seat === bb) {
      const post = Math.min(config.blinds.bb, p.stack);
      return {
        ...p,
        stack: p.stack - post,
        committedThisStreet: post,
        committedTotal: post,
        status: p.stack - post === 0 ? "all_in" : "active",
      };
    }
    return p;
  });
  events.push({
    type: "blinds-posted",
    sb: { seat: sb, amount: Math.min(config.blinds.sb, players.find((p) => p.seat === sb)?.committedThisStreet ?? config.blinds.sb) },
    bb: { seat: bb, amount: Math.min(config.blinds.bb, players.find((p) => p.seat === bb)?.committedThisStreet ?? config.blinds.bb) },
  });

  const dealStart = sb;
  const deal = dealHoleCards(players, shuffledDeck, dealStart);
  players = deal.players.slice();
  events.push(...deal.events);

  const currentSeat = firstToActPreflop(players, config.buttonSeat);

  const pots = buildPots(players);

  const state: GameState = {
    config,
    handId: 1,
    street: "preflop",
    deck: deal.deck,
    community: [],
    players,
    pots,
    currentSeat,
    currentBet: config.blinds.bb,
    lastRaiseSize: config.blinds.bb,
    buttonSeat: config.buttonSeat,
  };
  return { state, events };
}
