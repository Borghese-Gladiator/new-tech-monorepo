import type { IOSocket, ServerCtx } from "../engine.js";
import { registerJoinGame } from "./joinGame.js";
import { registerLeaveGame } from "./leaveGame.js";
import { registerPlayerAction } from "./playerAction.js";
import { registerReconnectSession } from "./reconnectSession.js";

export function registerHandlers(ctx: ServerCtx, socket: IOSocket): void {
  registerJoinGame(ctx, socket);
  registerLeaveGame(ctx, socket);
  registerPlayerAction(ctx, socket);
  registerReconnectSession(ctx, socket);

  socket.on("disconnect", () => {
    // PoC: keep the seat assigned (so re-join with sessionToken still works)
    // but unbind the live socket. TODO: schedule auto-fold timer when it's
    // the disconnected seat's turn.
    ctx.rooms.unbindSocket(socket.id);
  });
}
