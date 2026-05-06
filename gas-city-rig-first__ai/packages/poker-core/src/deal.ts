import type { Card, Deck, GameState, PlayerState, Seat } from "./types.js";
import type { GameEvent } from "./types.js";

export type DrawResult = {
  drawn: ReadonlyArray<Card>;
  remaining: Deck;
};

export function drawCards(deck: Deck, count: number): DrawResult {
  if (count < 0 || count > deck.length) {
    throw new Error(`drawCards: invalid count ${count} (deck size ${deck.length})`);
  }
  const drawn = deck.slice(0, count);
  const remaining = deck.slice(count);
  return { drawn, remaining };
}

export type DealHoleResult = {
  players: ReadonlyArray<PlayerState>;
  deck: Deck;
  events: ReadonlyArray<GameEvent>;
};

export function dealHoleCards(
  players: ReadonlyArray<PlayerState>,
  deck: Deck,
  startSeat: Seat,
): DealHoleResult {
  const order = orderFromSeat(players, startSeat);
  let working: Deck = deck;
  const out: PlayerState[] = players.map((p) => ({
    ...p,
    holeCards: p.holeCards,
  }));
  const dealt = new Map<Seat, Card[]>();
  for (let round = 0; round < 2; round++) {
    for (const seat of order) {
      const idx = out.findIndex((p) => p.seat === seat);
      if (idx === -1) continue;
      const player = out[idx];
      if (!player) continue;
      if (player.status === "folded") continue;
      const draw = drawCards(working, 1);
      working = draw.remaining;
      const card = draw.drawn[0];
      if (!card) continue;
      const list = dealt.get(seat) ?? [];
      list.push(card);
      dealt.set(seat, list);
    }
  }
  const events: GameEvent[] = [];
  for (let i = 0; i < out.length; i++) {
    const p = out[i];
    if (!p) continue;
    const cards = dealt.get(p.seat);
    if (!cards) continue;
    out[i] = { ...p, holeCards: cards };
    events.push({ type: "hole-cards-dealt", seat: p.seat, cards });
  }
  return { players: out, deck: working, events };
}

export function orderFromSeat(
  players: ReadonlyArray<PlayerState>,
  startSeat: Seat,
): ReadonlyArray<Seat> {
  const seats = players.map((p) => p.seat).slice().sort((a, b) => a - b);
  const idx = seats.indexOf(startSeat);
  if (idx === -1) return seats;
  return [...seats.slice(idx), ...seats.slice(0, idx)];
}

export type DealCommunityResult = {
  community: ReadonlyArray<Card>;
  deck: Deck;
  events: ReadonlyArray<GameEvent>;
};

export function dealFlop(state: GameState): DealCommunityResult {
  const draw = drawCards(state.deck, 3);
  const community = [...state.community, ...draw.drawn];
  return {
    community,
    deck: draw.remaining,
    events: [{ type: "cards-dealt", street: "flop", community }],
  };
}

export function dealTurn(state: GameState): DealCommunityResult {
  const draw = drawCards(state.deck, 1);
  const community = [...state.community, ...draw.drawn];
  return {
    community,
    deck: draw.remaining,
    events: [{ type: "cards-dealt", street: "turn", community }],
  };
}

export function dealRiver(state: GameState): DealCommunityResult {
  const draw = drawCards(state.deck, 1);
  const community = [...state.community, ...draw.drawn];
  return {
    community,
    deck: draw.remaining,
    events: [{ type: "cards-dealt", street: "river", community }],
  };
}
