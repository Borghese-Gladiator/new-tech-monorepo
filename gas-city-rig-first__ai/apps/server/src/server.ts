import { createServer as createHttpServer, type Server as HttpServer } from "node:http";
import { Server as IOServer } from "socket.io";
import { migrate } from "drizzle-orm/better-sqlite3/migrator";
import { createDb, migrationsFolder, type DbHandle } from "@gas-city/db";
import type {
  ClientToServerEvents,
  ServerToClientEvents,
} from "@gas-city/shared";
import { Rooms } from "./rooms.js";
import { registerHandlers } from "./handlers/index.js";
import { handleHttpRequest } from "./http.js";
import type { ServerCtx } from "./engine.js";

export type ServerOptions = {
  databaseUrl?: string;
  /** Reuse an already-open DbHandle. Caller is responsible for closing it. */
  dbHandle?: DbHandle;
  /** When true (default), apply migrations on the connection the server uses. */
  runMigrationsOnStart?: boolean;
};

export type ServerHandle = {
  http: HttpServer;
  io: IOServer<ClientToServerEvents, ServerToClientEvents>;
  db: DbHandle;
  rooms: Rooms;
  ctx: ServerCtx;
  listen: (port: number) => Promise<number>;
  close: () => Promise<void>;
};

export function createServer(opts: ServerOptions = {}): ServerHandle {
  const ownsDb = !opts.dbHandle;
  const dbHandle = opts.dbHandle ?? createDb(opts.databaseUrl);
  if (opts.runMigrationsOnStart !== false) {
    migrate(dbHandle.db, { migrationsFolder: migrationsFolder() });
  }

  const http = createHttpServer((req, res) => {
    if (!handleHttpRequest(dbHandle.db, req, res)) {
      res.statusCode = 404;
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify({ error: { code: "NOT_FOUND", message: "not found" } }));
    }
  });
  const io = new IOServer<ClientToServerEvents, ServerToClientEvents>(http, {
    cors: { origin: "*" },
  });

  const rooms = new Rooms();
  const ctx: ServerCtx = { io, db: dbHandle.db, rooms };

  io.on("connection", (socket) => {
    registerHandlers(ctx, socket);
  });

  return {
    http,
    io,
    db: dbHandle,
    rooms,
    ctx,
    listen(port: number): Promise<number> {
      return new Promise((resolve) => {
        http.listen(port, () => {
          const address = http.address();
          if (address && typeof address === "object") {
            resolve(address.port);
          } else {
            resolve(port);
          }
        });
      });
    },
    async close(): Promise<void> {
      await new Promise<void>((resolve) => {
        io.close(() => resolve());
      });
      await new Promise<void>((resolve) => {
        http.close(() => resolve());
      });
      if (ownsDb) dbHandle.close();
    },
  };
}
