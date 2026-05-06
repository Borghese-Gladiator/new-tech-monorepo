import { eq } from "drizzle-orm";
import { games } from "@gas-city/db";
import { isLegalAction, type Action } from "@gas-city/poker-core";
import type { AckResult, PlayerActionPayload } from "@gas-city/shared";
import { ErrorCode, type ErrorCode as Code } from "../errors.js";
import {
  applyAction,
  broadcastEvents,
  broadcastSnapshot,
  persistStateAndEvents,
  settleAfterAction,
  type IOSocket,
  type ServerCtx,
} from "../engine.js";

function ack(
  cb: ((res: AckResult) => void) | undefined,
  res: AckResult,
): void {
  if (typeof cb === "function") cb(res);
}

function emitError(socket: IOSocket, code: Code, message: string): void {
  socket.emit("playerError", { code, message });
}

function isAction(value: unknown): value is Action {
  if (typeof value !== "object" || value === null) return false;
  const k = (value as { kind?: unknown }).kind;
  if (k === "fold" || k === "check" || k === "call") return true;
  if (k === "raise") {
    const amt = (value as { amount?: unknown }).amount;
    return typeof amt === "number" && Number.isFinite(amt);
  }
  return false;
}

function isPlayerActionPayload(value: unknown): value is PlayerActionPayload {
  if (typeof value !== "object" || value === null) return false;
  const v = value as { gameId?: unknown; action?: unknown };
  return typeof v.gameId === "string" && isAction(v.action);
}

export function registerPlayerAction(ctx: ServerCtx, socket: IOSocket): void {
  socket.on("playerAction", (payload, cb) => {
    if (!isPlayerActionPayload(payload)) {
      emitError(socket, ErrorCode.INVALID_PAYLOAD, "invalid payload");
      ack(cb, {
        ok: false,
        error: { code: ErrorCode.INVALID_PAYLOAD, message: "invalid payload" },
      });
      return;
    }
    const gameId = Number.parseInt(payload.gameId, 10);
    if (!Number.isFinite(gameId)) {
      emitError(socket, ErrorCode.INVALID_PAYLOAD, "invalid gameId");
      ack(cb, {
        ok: false,
        error: { code: ErrorCode.INVALID_PAYLOAD, message: "invalid gameId" },
      });
      return;
    }

    const room = ctx.rooms.get(gameId);
    if (!room || !room.state) {
      emitError(socket, ErrorCode.GAME_NOT_FOUND, "game not found");
      ack(cb, {
        ok: false,
        error: { code: ErrorCode.GAME_NOT_FOUND, message: "game not found" },
      });
      return;
    }

    const seat = room.seatBySocket.get(socket.id);
    if (seat === undefined) {
      emitError(socket, ErrorCode.NOT_SEATED, "socket has no seat in this game");
      ack(cb, {
        ok: false,
        error: {
          code: ErrorCode.NOT_SEATED,
          message: "socket has no seat in this game",
        },
      });
      return;
    }

    if (room.state.currentSeat !== seat) {
      emitError(socket, ErrorCode.NOT_YOUR_TURN, "not your turn");
      ack(cb, {
        ok: false,
        error: { code: ErrorCode.NOT_YOUR_TURN, message: "not your turn" },
      });
      return;
    }

    const legal = isLegalAction(room.state, seat, payload.action);
    if (!legal.ok) {
      emitError(
        socket,
        ErrorCode.ILLEGAL_ACTION,
        legal.reason ?? "illegal action",
      );
      ack(cb, {
        ok: false,
        error: {
          code: ErrorCode.ILLEGAL_ACTION,
          message: legal.reason ?? "illegal action",
        },
      });
      return;
    }

    const applied = applyAction(room.state, payload.action);
    if (!applied.ok) {
      emitError(socket, ErrorCode.ILLEGAL_ACTION, applied.reason);
      ack(cb, {
        ok: false,
        error: { code: ErrorCode.ILLEGAL_ACTION, message: applied.reason },
      });
      return;
    }

    const settled = settleAfterAction(applied.state);
    const allNewEvents = [...applied.events, ...settled.events];

    // Detect terminal hand to flip game status to finished.
    const handResolved = allNewEvents.some((e) => e.type === "hand-resolved");
    if (handResolved) {
      ctx.db
        .update(games)
        .set({ status: "finished", currentStreet: settled.state.street })
        .where(eq(games.id, gameId))
        .run();
    } else {
      ctx.db
        .update(games)
        .set({ currentStreet: settled.state.street })
        .where(eq(games.id, gameId))
        .run();
    }

    ctx.rooms.setState(gameId, settled.state);
    persistStateAndEvents(ctx.db, gameId, settled.state, allNewEvents);
    broadcastEvents(ctx, gameId, allNewEvents);
    broadcastSnapshot(ctx, gameId, settled.state);

    ack(cb, { ok: true });
  });
}
