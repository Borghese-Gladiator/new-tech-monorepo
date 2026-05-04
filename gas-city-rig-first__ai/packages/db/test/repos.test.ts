import { afterEach, beforeEach, describe, expect, it } from "vitest";
import Database, { type Database as SqliteDatabase } from "better-sqlite3";
import { drizzle } from "drizzle-orm/better-sqlite3";
import { migrate } from "drizzle-orm/better-sqlite3/migrator";
import type { GameState } from "@gas-city/poker-core";
import {
  appendGameEvent,
  games,
  listOpenGames,
  loadGame,
  players,
  restorePlayerSeat,
  saveSnapshot,
  seats,
  type Db,
} from "../src/index.js";
import { migrationsFolder } from "../src/migrate.js";

type Fixture = {
  db: Db;
  sqlite: SqliteDatabase;
};

function fakeState(handId: number): GameState {
  return {
    config: {
      blinds: { sb: 1, bb: 2 },
      startingStacks: 200,
      numSeats: 2,
      buttonSeat: 0,
      seed: 42,
    },
    handId,
    street: "preflop",
    deck: [],
    community: [],
    players: [],
    pots: [],
    currentSeat: 0,
    currentBet: 0,
    lastRaiseSize: 0,
    buttonSeat: 0,
    events: [],
  };
}

describe("@gas-city/db repos", () => {
  let fx: Fixture;

  beforeEach(() => {
    const sqlite = new Database(":memory:");
    sqlite.pragma("foreign_keys = ON");
    const db = drizzle(sqlite);
    migrate(db, { migrationsFolder: migrationsFolder() });
    fx = { db: db as unknown as Db, sqlite };
  });

  afterEach(() => {
    fx.sqlite.close();
  });

  it("round-trips snapshots, events, seats, and queries", () => {
    const { db } = fx;

    const gameOpen = db
      .insert(games)
      .values({ status: "open" })
      .returning()
      .get();
    const gameClosed = db
      .insert(games)
      .values({ status: "finished" })
      .returning()
      .get();
    const gameInProgress = db
      .insert(games)
      .values({ status: "in_progress" })
      .returning()
      .get();
    if (!gameOpen || !gameClosed || !gameInProgress) {
      throw new Error("game inserts failed");
    }

    const player = db
      .insert(players)
      .values({ displayName: "alice" })
      .returning()
      .get();
    if (!player) throw new Error("player insert failed");

    const seat = db
      .insert(seats)
      .values({
        gameId: gameOpen.id,
        playerId: player.id,
        seatIndex: 0,
        stack: 200,
        sessionToken: "tok-alice",
      })
      .returning()
      .get();
    if (!seat) throw new Error("seat insert failed");

    const snap1 = saveSnapshot(db, gameOpen.id, fakeState(1));
    const snap2 = saveSnapshot(db, gameOpen.id, fakeState(2));
    expect(snap1.snapshotIndex).toBe(0);
    expect(snap2.snapshotIndex).toBe(1);

    const ev1 = appendGameEvent(db, gameOpen.id, {
      type: "hand-started",
      payload: { handId: 1 },
    });
    const ev2 = appendGameEvent(db, gameOpen.id, {
      type: "blinds-posted",
      payload: { sb: 1, bb: 2 },
    });
    expect(ev1.eventIndex).toBe(0);
    expect(ev2.eventIndex).toBe(1);

    const loaded = loadGame(db, gameOpen.id);
    expect(loaded).not.toBeNull();
    expect(loaded?.snapshot?.row.snapshotIndex).toBe(1);
    expect(loaded?.snapshot?.state.handId).toBe(2);
    expect(loaded?.seats.map((s) => s.id)).toEqual([seat.id]);
    expect(loaded?.events.map((e) => e.row.eventIndex)).toEqual([1, 0]);
    expect(loaded?.events[0]?.payload).toEqual({ sb: 1, bb: 2 });

    const open = listOpenGames(db);
    expect(open.map((g) => g.id).sort()).toEqual(
      [gameOpen.id, gameInProgress.id].sort(),
    );

    expect(restorePlayerSeat(db, gameOpen.id, "tok-alice")?.id).toBe(seat.id);
    expect(restorePlayerSeat(db, gameOpen.id, "missing")).toBeNull();
  });
});
