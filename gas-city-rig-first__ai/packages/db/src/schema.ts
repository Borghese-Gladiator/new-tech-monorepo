import { sql } from "drizzle-orm";
import {
  check,
  integer,
  sqliteTable,
  text,
  uniqueIndex,
} from "drizzle-orm/sqlite-core";

const now = sql`(unixepoch() * 1000)`;

export const games = sqliteTable(
  "games",
  {
    id: integer("id").primaryKey({ autoIncrement: true }),
    status: text("status").notNull().default("open"),
    buttonSeat: integer("button_seat"),
    currentStreet: text("current_street"),
    createdAt: integer("created_at").notNull().default(now),
    updatedAt: integer("updated_at").notNull().default(now),
  },
  (t) => ({
    statusCheck: check(
      "games_status_check",
      sql`${t.status} in ('open','in_progress','finished')`,
    ),
  }),
);

export const players = sqliteTable("players", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  displayName: text("display_name").notNull(),
  createdAt: integer("created_at").notNull().default(now),
});

export const seats = sqliteTable(
  "seats",
  {
    id: integer("id").primaryKey({ autoIncrement: true }),
    gameId: integer("game_id")
      .notNull()
      .references(() => games.id),
    playerId: integer("player_id")
      .notNull()
      .references(() => players.id),
    seatIndex: integer("seat_index").notNull(),
    stack: integer("stack").notNull(),
    status: text("status").notNull().default("active"),
    sessionToken: text("session_token"),
  },
  (t) => ({
    statusCheck: check(
      "seats_status_check",
      sql`${t.status} in ('active','folded','all_in','sitting_out')`,
    ),
    seatPerGame: uniqueIndex("seats_game_seat_idx").on(t.gameId, t.seatIndex),
  }),
);

export const gameSnapshots = sqliteTable(
  "game_snapshots",
  {
    id: integer("id").primaryKey({ autoIncrement: true }),
    gameId: integer("game_id")
      .notNull()
      .references(() => games.id),
    snapshotIndex: integer("snapshot_index").notNull(),
    state: text("state").notNull(),
    createdAt: integer("created_at").notNull().default(now),
  },
  (t) => ({
    snapshotPerGame: uniqueIndex("game_snapshots_game_idx").on(
      t.gameId,
      t.snapshotIndex,
    ),
  }),
);

export const gameEvents = sqliteTable(
  "game_events",
  {
    id: integer("id").primaryKey({ autoIncrement: true }),
    gameId: integer("game_id")
      .notNull()
      .references(() => games.id),
    eventIndex: integer("event_index").notNull(),
    eventType: text("event_type").notNull(),
    payload: text("payload").notNull(),
    createdAt: integer("created_at").notNull().default(now),
  },
  (t) => ({
    eventPerGame: uniqueIndex("game_events_game_idx").on(
      t.gameId,
      t.eventIndex,
    ),
  }),
);

export type GameRow = typeof games.$inferSelect;
export type PlayerRow = typeof players.$inferSelect;
export type SeatRow = typeof seats.$inferSelect;
export type GameSnapshotRow = typeof gameSnapshots.$inferSelect;
export type GameEventRow = typeof gameEvents.$inferSelect;
