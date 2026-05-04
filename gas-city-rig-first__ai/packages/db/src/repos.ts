import { and, desc, eq, inArray, sql } from "drizzle-orm";
import type { GameState } from "@gas-city/poker-core";
import type { Db } from "./db.js";
import {
  gameEvents,
  gameSnapshots,
  games,
  seats,
  type GameEventRow,
  type GameRow,
  type GameSnapshotRow,
  type SeatRow,
} from "./schema.js";

export type AppendableEvent = {
  type: string;
  payload: unknown;
};

export type LoadedGame = {
  game: GameRow;
  snapshot: { row: GameSnapshotRow; state: GameState } | null;
  seats: ReadonlyArray<SeatRow>;
  events: ReadonlyArray<{ row: GameEventRow; payload: unknown }>;
};

function nextIndexFor(
  db: Db,
  table: typeof gameSnapshots | typeof gameEvents,
  indexCol: typeof gameSnapshots.snapshotIndex | typeof gameEvents.eventIndex,
  gameId: number,
): number {
  const row = db
    .select({ max: sql<number | null>`max(${indexCol})` })
    .from(table)
    .where(eq(table.gameId, gameId))
    .get();
  const current = row?.max ?? null;
  return current === null ? 0 : current + 1;
}

export function saveSnapshot(
  db: Db,
  gameId: number,
  state: GameState,
): GameSnapshotRow {
  const snapshotIndex = nextIndexFor(
    db,
    gameSnapshots,
    gameSnapshots.snapshotIndex,
    gameId,
  );
  const inserted = db
    .insert(gameSnapshots)
    .values({
      gameId,
      snapshotIndex,
      state: JSON.stringify(state),
    })
    .returning()
    .get();
  if (!inserted) {
    throw new Error(`failed to insert snapshot for game ${gameId}`);
  }
  return inserted;
}

export function appendGameEvent(
  db: Db,
  gameId: number,
  event: AppendableEvent,
): GameEventRow {
  const eventIndex = nextIndexFor(
    db,
    gameEvents,
    gameEvents.eventIndex,
    gameId,
  );
  const inserted = db
    .insert(gameEvents)
    .values({
      gameId,
      eventIndex,
      eventType: event.type,
      payload: JSON.stringify(event.payload),
    })
    .returning()
    .get();
  if (!inserted) {
    throw new Error(`failed to insert event for game ${gameId}`);
  }
  return inserted;
}

export function loadGame(
  db: Db,
  gameId: number,
  eventLimit = 50,
): LoadedGame | null {
  const game = db.select().from(games).where(eq(games.id, gameId)).get();
  if (!game) return null;

  const snapshotRow = db
    .select()
    .from(gameSnapshots)
    .where(eq(gameSnapshots.gameId, gameId))
    .orderBy(desc(gameSnapshots.snapshotIndex))
    .limit(1)
    .get();

  const seatRows = db
    .select()
    .from(seats)
    .where(
      and(
        eq(seats.gameId, gameId),
        inArray(seats.status, ["active", "folded", "all_in"]),
      ),
    )
    .all();

  const eventRows = db
    .select()
    .from(gameEvents)
    .where(eq(gameEvents.gameId, gameId))
    .orderBy(desc(gameEvents.eventIndex))
    .limit(eventLimit)
    .all();

  return {
    game,
    snapshot: snapshotRow
      ? { row: snapshotRow, state: JSON.parse(snapshotRow.state) as GameState }
      : null,
    seats: seatRows,
    events: eventRows.map((row) => ({
      row,
      payload: JSON.parse(row.payload),
    })),
  };
}

export function listOpenGames(db: Db): ReadonlyArray<GameRow> {
  return db
    .select()
    .from(games)
    .where(inArray(games.status, ["open", "in_progress"]))
    .orderBy(desc(games.updatedAt))
    .all();
}

export function restorePlayerSeat(
  db: Db,
  gameId: number,
  sessionToken: string,
): SeatRow | null {
  const row = db
    .select()
    .from(seats)
    .where(and(eq(seats.gameId, gameId), eq(seats.sessionToken, sessionToken)))
    .get();
  return row ?? null;
}
