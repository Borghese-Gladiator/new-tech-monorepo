import { io, type Socket } from "socket.io-client";
import type {
  ClientToServerEvents,
  ServerToClientEvents,
} from "@gas-city/shared";

export type GameSocket = Socket<ServerToClientEvents, ClientToServerEvents>;

const DEFAULT_SERVER_URL = "http://localhost:4000";

function serverUrl(): string {
  if (typeof process !== "undefined" && process.env.NEXT_PUBLIC_SERVER_URL) {
    return process.env.NEXT_PUBLIC_SERVER_URL;
  }
  return DEFAULT_SERVER_URL;
}

/**
 * Create a Socket.IO client for a specific gameId.
 *
 * Reconnect is handled by socket.io-client automatically; the caller is
 * responsible for emitting joinGame on first connect and reconnectSession
 * on subsequent reconnects with the cookie's sessionToken.
 */
export function createGameSocket(): GameSocket {
  return io(serverUrl(), {
    transports: ["websocket"],
    autoConnect: true,
    reconnection: true,
    reconnectionAttempts: Infinity,
    reconnectionDelay: 500,
    reconnectionDelayMax: 5000,
    forceNew: true,
  });
}
