import type { GameState, PlayerState, Seat } from "./types.js";

export function getPlayer(state: GameState, seat: Seat): PlayerState | undefined {
  return state.players.find((p) => p.seat === seat);
}

export function activePlayers(state: GameState): ReadonlyArray<PlayerState> {
  return state.players.filter((p) => p.status !== "folded");
}

export function inHandPlayers(state: GameState): ReadonlyArray<PlayerState> {
  return state.players.filter((p) => p.status === "active");
}

export function nextSeatIn(
  players: ReadonlyArray<PlayerState>,
  fromSeat: Seat,
  predicate: (p: PlayerState) => boolean,
): Seat | null {
  const ordered = players.slice().sort((a, b) => a.seat - b.seat);
  if (ordered.length === 0) return null;
  const idx = ordered.findIndex((p) => p.seat === fromSeat);
  const start = idx === -1 ? -1 : idx;
  for (let step = 1; step <= ordered.length; step++) {
    const next = ordered[(start + step) % ordered.length];
    if (next && predicate(next)) return next.seat;
  }
  return null;
}

export function seatAfterButton(
  players: ReadonlyArray<PlayerState>,
  buttonSeat: Seat,
  predicate: (p: PlayerState) => boolean = () => true,
): Seat | null {
  return nextSeatIn(players, buttonSeat, predicate);
}

export function smallBlindSeat(
  players: ReadonlyArray<PlayerState>,
  buttonSeat: Seat,
): Seat | null {
  const seated = players.filter((p) => p.status !== "folded");
  if (seated.length === 2) {
    return buttonSeat;
  }
  return seatAfterButton(seated, buttonSeat);
}

export function bigBlindSeat(
  players: ReadonlyArray<PlayerState>,
  buttonSeat: Seat,
): Seat | null {
  const sb = smallBlindSeat(players, buttonSeat);
  if (sb === null) return null;
  const seated = players.filter((p) => p.status !== "folded");
  return nextSeatIn(seated, sb, () => true);
}

export function firstToActPreflop(
  players: ReadonlyArray<PlayerState>,
  buttonSeat: Seat,
): Seat | null {
  const seated = players.filter((p) => p.status !== "folded");
  if (seated.length === 2) {
    return buttonSeat;
  }
  const bb = bigBlindSeat(seated, buttonSeat);
  if (bb === null) return null;
  return nextSeatIn(
    seated,
    bb,
    (p) => p.status === "active",
  );
}

export function firstToActPostflop(
  players: ReadonlyArray<PlayerState>,
  buttonSeat: Seat,
): Seat | null {
  const seated = players.filter((p) => p.status === "active");
  return nextSeatIn(seated, buttonSeat, () => true);
}
