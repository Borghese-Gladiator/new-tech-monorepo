import { randomUUID } from "node:crypto";
import { eq } from "drizzle-orm";
import { games, players, seats, restorePlayerSeat } from "@gas-city/db";
import { isJoinGamePayload, type AckResult } from "@gas-city/shared";
import { ErrorCode } from "../errors.js";
import {
  broadcastEvents,
  broadcastSnapshot,
  defaultGameConfig,
  persistStateAndEvents,
  snapshotForSeat,
  startHand,
  type IOSocket,
  type ServerCtx,
} from "../engine.js";
import { gameRoomName } from "../rooms.js";

const REQUIRED_TO_START = 2;

function ack(
  cb: ((res: AckResult) => void) | undefined,
  res: AckResult,
): void {
  if (typeof cb === "function") cb(res);
}

function ensureGame(ctx: ServerCtx, gameId: number): boolean {
  const row = ctx.db.select().from(games).where(eq(games.id, gameId)).get();
  return row !== undefined;
}

function createGame(ctx: ServerCtx): number {
  const inserted = ctx.db
    .insert(games)
    .values({ status: "open" })
    .returning()
    .get();
  if (!inserted) throw new Error("failed to create game");
  return inserted.id;
}

function nextOpenSeat(ctx: ServerCtx, gameId: number): number | null {
  const taken = new Set(
    ctx.db
      .select({ seatIndex: seats.seatIndex })
      .from(seats)
      .where(eq(seats.gameId, gameId))
      .all()
      .map((r) => r.seatIndex),
  );
  for (let i = 0; i < 2; i++) {
    if (!taken.has(i)) return i;
  }
  return null;
}

export function registerJoinGame(ctx: ServerCtx, socket: IOSocket): void {
  socket.on("joinGame", (payload, cb) => {
    if (!isJoinGamePayload(payload)) {
      ack(cb, {
        ok: false,
        error: { code: ErrorCode.INVALID_PAYLOAD, message: "invalid payload" },
      });
      return;
    }

    const gameIdNum = Number.parseInt(payload.gameId, 10);
    let gameId = Number.isFinite(gameIdNum) ? gameIdNum : NaN;

    // Auto-create game if id is "new" sentinel or if id doesn't exist.
    if (!Number.isFinite(gameId) || gameId <= 0) {
      gameId = createGame(ctx);
    } else if (!ensureGame(ctx, gameId)) {
      gameId = createGame(ctx);
    }

    // Reconnect path
    if (payload.sessionToken) {
      const existing = restorePlayerSeat(ctx.db, gameId, payload.sessionToken);
      if (existing) {
        ctx.rooms.bindSocket(gameId, socket.id, existing.seatIndex);
        socket.join(gameRoomName(gameId));
        const room = ctx.rooms.get(gameId);
        if (room?.state) {
          socket.emit(
            "gameSnapshot",
            snapshotForSeat(room.state, gameId, existing.seatIndex),
          );
        }
        ack(cb, { ok: true });
        return;
      }
    }

    // New seat path — must have an open slot
    const gameRow = ctx.db.select().from(games).where(eq(games.id, gameId)).get();
    if (!gameRow) {
      ack(cb, {
        ok: false,
        error: { code: ErrorCode.GAME_NOT_FOUND, message: "game not found" },
      });
      return;
    }
    if (gameRow.status !== "open") {
      ack(cb, {
        ok: false,
        error: { code: ErrorCode.GAME_NOT_OPEN, message: "game not accepting joins" },
      });
      return;
    }
    const seatIndex = nextOpenSeat(ctx, gameId);
    if (seatIndex === null) {
      ack(cb, {
        ok: false,
        error: { code: ErrorCode.NO_OPEN_SEATS, message: "no open seats" },
      });
      return;
    }

    const player = ctx.db
      .insert(players)
      .values({ displayName: payload.displayName })
      .returning()
      .get();
    if (!player) {
      ack(cb, {
        ok: false,
        error: { code: ErrorCode.INTERNAL, message: "player insert failed" },
      });
      return;
    }

    const sessionToken = randomUUID();
    const seatRow = ctx.db
      .insert(seats)
      .values({
        gameId,
        playerId: player.id,
        seatIndex,
        stack: 200,
        status: "active",
        sessionToken,
      })
      .returning()
      .get();
    if (!seatRow) {
      ack(cb, {
        ok: false,
        error: { code: ErrorCode.INTERNAL, message: "seat insert failed" },
      });
      return;
    }

    ctx.rooms.bindSocket(gameId, socket.id, seatIndex);
    socket.join(gameRoomName(gameId));
    ack(cb, { ok: true });
    socket.emit("connectionStatus", { state: "connected", sessionToken });

    // Auto-start when room is full
    const seatCount = ctx.db
      .select()
      .from(seats)
      .where(eq(seats.gameId, gameId))
      .all().length;
    if (seatCount >= REQUIRED_TO_START) {
      const seatRows = ctx.db
        .select()
        .from(seats)
        .where(eq(seats.gameId, gameId))
        .all();
      const config = defaultGameConfig(gameId * 1000 + Date.now() % 1000);
      const { state, events } = startHand({
        config,
        players: seatRows.map((s) => ({ seat: s.seatIndex, stack: s.stack })),
      });
      ctx.db
        .update(games)
        .set({ status: "in_progress", currentStreet: state.street })
        .where(eq(games.id, gameId))
        .run();
      ctx.rooms.setState(gameId, state);
      persistStateAndEvents(ctx.db, gameId, state, events);
      broadcastSnapshot(ctx, gameId, state);
      broadcastEvents(ctx, gameId, events);
    }
  });
}
