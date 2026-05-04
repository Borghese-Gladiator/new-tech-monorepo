import type { AckResult } from "@gas-city/shared";
import { ErrorCode } from "../errors.js";
import { gameRoomName } from "../rooms.js";
import type { IOSocket, ServerCtx } from "../engine.js";

function ack(
  cb: ((res: AckResult) => void) | undefined,
  res: AckResult,
): void {
  if (typeof cb === "function") cb(res);
}

export function registerLeaveGame(ctx: ServerCtx, socket: IOSocket): void {
  socket.on("leaveGame", (payload, cb) => {
    const gameId = Number.parseInt(payload.gameId, 10);
    if (!Number.isFinite(gameId)) {
      ack(cb, {
        ok: false,
        error: { code: ErrorCode.INVALID_PAYLOAD, message: "invalid gameId" },
      });
      return;
    }
    const room = ctx.rooms.get(gameId);
    if (!room) {
      ack(cb, {
        ok: false,
        error: { code: ErrorCode.GAME_NOT_FOUND, message: "game not found" },
      });
      return;
    }
    room.seatBySocket.delete(socket.id);
    socket.leave(gameRoomName(gameId));
    ack(cb, { ok: true });
  });
}
