import { afterEach, beforeEach, describe, expect, it } from "vitest";
import Database, { type Database as SqliteDatabase } from "better-sqlite3";
import { drizzle } from "drizzle-orm/better-sqlite3";
import { eq } from "drizzle-orm";
import { migrate } from "drizzle-orm/better-sqlite3/migrator";
import {
  advanceStreet,
  applyAction,
  startHand,
  type GameState,
} from "@gas-city/poker-core";
import {
  appendGameEvent,
  gameEvents,
  gameSnapshots,
  games,
  listOpenGames,
  loadGame,
  players,
  restorePlayerSeat,
  runInTransaction,
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

  it("rejects two seats sharing the same sessionToken (UNIQUE constraint)", () => {
    const { db } = fx;

    const game = db
      .insert(games)
      .values({ status: "open" })
      .returning()
      .get();
    if (!game) throw new Error("game insert failed");

    const alice = db
      .insert(players)
      .values({ displayName: "alice" })
      .returning()
      .get();
    const bob = db
      .insert(players)
      .values({ displayName: "bob" })
      .returning()
      .get();
    if (!alice || !bob) throw new Error("player inserts failed");

    db.insert(seats)
      .values({
        gameId: game.id,
        playerId: alice.id,
        seatIndex: 0,
        stack: 200,
        sessionToken: "shared-token",
      })
      .run();

    expect(() =>
      db
        .insert(seats)
        .values({
          gameId: game.id,
          playerId: bob.id,
          seatIndex: 1,
          stack: 200,
          sessionToken: "shared-token",
        })
        .run(),
    ).toThrow(/UNIQUE constraint failed: seats\.session_token/);
  });

  it("snapshot row stays small after many actions (no embedded events array)", () => {
    const { db } = fx;

    const game = db
      .insert(games)
      .values({ status: "open" })
      .returning()
      .get();
    if (!game) throw new Error("game insert failed");

    const cfg = {
      blinds: { sb: 1, bb: 2 },
      startingStacks: 200,
      numSeats: 3,
      buttonSeat: 0,
      seed: 42,
    };
    let { state } = startHand({ config: cfg });
    saveSnapshot(db, game.id, state);

    // Drive a long sequence across all four streets: each player raises and
    // gets called, advancing one snapshot per action plus one per street.
    // This produces ~30 snapshots — enough to expose quadratic growth if the
    // events array were embedded.
    let actionCount = 0;
    while (actionCount < 30) {
      if (state.currentSeat === null) {
        const adv = advanceStreet(state);
        if (!adv.ok) break;
        state = adv.state;
        saveSnapshot(db, game.id, state);
        if (state.street === "showdown") break;
        continue;
      }
      const player = state.players.find((p) => p.seat === state.currentSeat);
      if (!player) break;
      const toCall = state.currentBet - player.committedThisStreet;
      const action =
        toCall > 0 ? { kind: "call" as const } : { kind: "check" as const };
      const r = applyAction(state, action);
      if (!r.ok) break;
      state = r.state;
      saveSnapshot(db, game.id, state);
      actionCount += 1;
    }

    const snapshotRows = db
      .select()
      .from(gameSnapshots)
      .where(eq(gameSnapshots.gameId, game.id))
      .all();
    expect(snapshotRows.length).toBeGreaterThan(0);

    for (const row of snapshotRows) {
      // Each snapshot must not embed an events array.
      const parsed = JSON.parse(row.state) as Partial<GameState> & {
        events?: unknown;
      };
      expect(parsed.events).toBeUndefined();
      // 8KB ceiling per snapshot — guards against quadratic regrowth.
      expect(row.state.length).toBeLessThan(8 * 1024);
    }
  });

  it("runInTransaction rolls back snapshot and events when the callback throws", () => {
    const { db } = fx;

    const game = db
      .insert(games)
      .values({ status: "open" })
      .returning()
      .get();
    if (!game) throw new Error("game insert failed");

    expect(() =>
      runInTransaction(db, (tx) => {
        saveSnapshot(tx, game.id, fakeState(1));
        appendGameEvent(tx, game.id, {
          type: "hand-started",
          payload: { handId: 1 },
        });
        throw new Error("boom — simulate mid-write failure");
      }),
    ).toThrow(/boom/);

    const snapRows = db
      .select()
      .from(gameSnapshots)
      .where(eq(gameSnapshots.gameId, game.id))
      .all();
    const evRows = db
      .select()
      .from(gameEvents)
      .where(eq(gameEvents.gameId, game.id))
      .all();
    expect(snapRows).toEqual([]);
    expect(evRows).toEqual([]);
  });
});
