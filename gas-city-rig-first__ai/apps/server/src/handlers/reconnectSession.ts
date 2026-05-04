import { restorePlayerSeat } from "@gas-city/db";
import type { AckResult } from "@gas-city/shared";
import { ErrorCode } from "../errors.js";
import {
  snapshotForSeat,
  type IOSocket,
  type ServerCtx,
} from "../engine.js";
import { gameRoomName } from "../rooms.js";

function ack(
  cb: ((res: AckResult) => void) | undefined,
  res: AckResult,
): void {
  if (typeof cb === "function") cb(res);
}

export function registerReconnectSession(ctx: ServerCtx, socket: IOSocket): void {
  socket.on("reconnectSession", (payload, cb) => {
    const gameId = Number.parseInt(payload.gameId, 10);
    if (
      !Number.isFinite(gameId) ||
      typeof payload.sessionToken !== "string" ||
      !payload.sessionToken
    ) {
      ack(cb, {
        ok: false,
        error: { code: ErrorCode.INVALID_PAYLOAD, message: "invalid payload" },
      });
      return;
    }

    const seatRow = restorePlayerSeat(ctx.db, gameId, payload.sessionToken);
    if (!seatRow) {
      ack(cb, {
        ok: false,
        error: {
          code: ErrorCode.SESSION_NOT_FOUND,
          message: "session not found",
        },
      });
      return;
    }

    ctx.rooms.bindSocket(gameId, socket.id, seatRow.seatIndex);
    socket.join(gameRoomName(gameId));
    ack(cb, { ok: true });

    const room = ctx.rooms.get(gameId);
    if (room?.state) {
      socket.emit(
        "gameSnapshot",
        snapshotForSeat(room.state, gameId, seatRow.seatIndex),
      );
    }
  });
}
