import type { IncomingMessage, ServerResponse } from "node:http";
import { eq } from "drizzle-orm";
import { games, listOpenGames, seats } from "@gas-city/db";
import type { Db } from "@gas-city/db";

type OpenGameDto = {
  id: string;
  status: string;
  seatsTaken: number;
  numSeats: number;
  createdAt: number;
  updatedAt: number;
};

const NUM_SEATS = 2;

function setCors(res: ServerResponse): void {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
}

function sendJson(res: ServerResponse, status: number, body: unknown): void {
  setCors(res);
  res.statusCode = status;
  res.setHeader("Content-Type", "application/json");
  res.end(JSON.stringify(body));
}

function listOpenGamesDto(db: Db): ReadonlyArray<OpenGameDto> {
  const rows = listOpenGames(db);
  return rows.map((row) => {
    const seatRows = db
      .select({ id: seats.id })
      .from(seats)
      .where(eq(seats.gameId, row.id))
      .all();
    return {
      id: String(row.id),
      status: row.status,
      seatsTaken: seatRows.length,
      numSeats: NUM_SEATS,
      createdAt: row.createdAt,
      updatedAt: row.updatedAt,
    };
  });
}

function createGame(db: Db): { id: string } {
  const inserted = db
    .insert(games)
    .values({ status: "open" })
    .returning()
    .get();
  if (!inserted) throw new Error("failed to create game");
  return { id: String(inserted.id) };
}

export function handleHttpRequest(
  db: Db,
  req: IncomingMessage,
  res: ServerResponse,
): boolean {
  const url = req.url ?? "";
  // socket.io owns /socket.io/*; let it handle that path.
  if (url.startsWith("/socket.io")) return false;

  // CORS preflight
  if (req.method === "OPTIONS") {
    setCors(res);
    res.statusCode = 204;
    res.end();
    return true;
  }

  if (req.method === "GET" && (url === "/games" || url.startsWith("/games?"))) {
    sendJson(res, 200, { games: listOpenGamesDto(db) });
    return true;
  }

  if (req.method === "POST" && url === "/games") {
    try {
      const created = createGame(db);
      sendJson(res, 201, created);
    } catch (err) {
      sendJson(res, 500, {
        error: { code: "INTERNAL", message: (err as Error).message },
      });
    }
    return true;
  }

  if (req.method === "GET" && url === "/health") {
    sendJson(res, 200, { ok: true });
    return true;
  }

  return false;
}
