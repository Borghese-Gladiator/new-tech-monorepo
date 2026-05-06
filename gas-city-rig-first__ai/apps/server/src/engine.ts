import type { Server, Socket } from "socket.io";
import {
  advanceStreet,
  applyAction,
  isBettingRoundClosed,
  isHandOver,
  resolveHand,
  startHand,
  type Action,
  type Card,
  type GameConfig,
  type GameEvent,
  type GameState,
  type PlayerState,
  type Seat,
} from "@gas-city/poker-core";
import {
  appendGameEvent,
  runInTransaction,
  saveSnapshot,
  type Db,
} from "@gas-city/db";
import type {
  ClientToServerEvents,
  GameSnapshotPayload,
  ServerToClientEvents,
} from "@gas-city/shared";
import { gameRoomName, Rooms } from "./rooms.js";

export type IOServer = Server<ClientToServerEvents, ServerToClientEvents>;
export type IOSocket = Socket<ClientToServerEvents, ServerToClientEvents>;

export type ServerCtx = {
  io: IOServer;
  db: Db;
  rooms: Rooms;
};

const DEFAULT_CONFIG: GameConfig = {
  blinds: { sb: 1, bb: 2 },
  startingStacks: 200,
  numSeats: 2,
  buttonSeat: 0,
  seed: 1,
};

export function defaultGameConfig(seed: number): GameConfig {
  return { ...DEFAULT_CONFIG, seed };
}

/**
 * Strip private fields (hole cards) from a state before broadcasting.
 * Each player keeps their seat/stack/status but holeCards becomes empty.
 */
function publicState(state: GameState): GameState {
  const players: PlayerState[] = state.players.map((p) => ({
    ...p,
    holeCards: [],
  }));
  return { ...state, players };
}

function holeCardsFor(state: GameState, seat: Seat): [Card, Card] | null {
  const player = state.players.find((p) => p.seat === seat);
  if (!player) return null;
  if (player.holeCards.length < 2) return null;
  const a = player.holeCards[0];
  const b = player.holeCards[1];
  if (!a || !b) return null;
  return [a, b];
}

export function snapshotForRoom(state: GameState, gameId: number): GameSnapshotPayload {
  return { gameId: String(gameId), state: publicState(state) };
}

export function snapshotForSeat(
  state: GameState,
  gameId: number,
  seat: Seat,
): GameSnapshotPayload {
  const hole = holeCardsFor(state, seat);
  const base: GameSnapshotPayload = {
    gameId: String(gameId),
    state: publicState(state),
  };
  if (hole) {
    return { ...base, you: { seatIndex: seat, holeCards: hole } };
  }
  return base;
}

/**
 * Persist state + new events atomically. The snapshot and all event rows are
 * written inside one sqlite transaction so a mid-loop failure cannot leave a
 * snapshot disagreeing with a partial event log.
 */
export function persistStateAndEvents(
  db: Db,
  gameId: number,
  state: GameState,
  newEvents: ReadonlyArray<GameEvent>,
): void {
  runInTransaction(db, (tx) => {
    saveSnapshot(tx, gameId, state);
    for (const event of newEvents) {
      appendGameEvent(tx, gameId, { type: event.type, payload: event });
    }
  });
}

/**
 * After a player action: drain closed betting rounds (advance streets) and
 * resolve the hand if it's over. Returns the final state plus all events
 * generated since the action. The caller is responsible for persisting and
 * broadcasting.
 */
export function settleAfterAction(state: GameState): {
  state: GameState;
  events: ReadonlyArray<GameEvent>;
} {
  const events: GameEvent[] = [];
  let current = state;

  // Hand may already be over (everyone folded) — resolve immediately.
  while (true) {
    if (isHandOver(current)) {
      const r = resolveHand(current);
      events.push(...r.events);
      current = r.state;
      break;
    }
    if (current.street === "showdown") {
      const r = resolveHand(current);
      events.push(...r.events);
      current = r.state;
      break;
    }
    if (!isBettingRoundClosed(current)) {
      break;
    }
    const adv = advanceStreet(current);
    if (!adv.ok) break;
    events.push(...adv.events);
    current = adv.state;
    // After advancing to showdown, resolve next loop iteration.
    if (current.street === "showdown") {
      const r = resolveHand(current);
      events.push(...r.events);
      current = r.state;
      break;
    }
  }

  return { state: current, events };
}

/** Broadcast a public snapshot to the room, then per-socket snapshots with hole cards. */
export function broadcastSnapshot(ctx: ServerCtx, gameId: number, state: GameState): void {
  ctx.io.to(gameRoomName(gameId)).emit("gameSnapshot", snapshotForRoom(state, gameId));
  const room = ctx.rooms.get(gameId);
  if (!room) return;
  for (const [socketId, seat] of room.seatBySocket) {
    const sock = ctx.io.sockets.sockets.get(socketId);
    if (!sock) continue;
    sock.emit("gameSnapshot", snapshotForSeat(state, gameId, seat));
  }
}

export function broadcastEvents(
  ctx: ServerCtx,
  gameId: number,
  events: ReadonlyArray<GameEvent>,
): void {
  for (const event of events) {
    ctx.io
      .to(gameRoomName(gameId))
      .emit("gameEvent", { gameId: String(gameId), event });
  }
}

export { applyAction, startHand };
export type { Action };
