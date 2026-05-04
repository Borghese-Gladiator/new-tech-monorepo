export * as schema from "./schema.js";
export {
  games,
  players,
  seats,
  gameSnapshots,
  gameEvents,
} from "./schema.js";
export type {
  GameRow,
  PlayerRow,
  SeatRow,
  GameSnapshotRow,
  GameEventRow,
} from "./schema.js";

export { createDb, resolveDatabasePath } from "./db.js";
export type { Db, DbHandle } from "./db.js";

export {
  appendGameEvent,
  listOpenGames,
  loadGame,
  restorePlayerSeat,
  saveSnapshot,
} from "./repos.js";
export type { AppendableEvent, LoadedGame } from "./repos.js";

export { migrationsFolder, runMigrations } from "./migrate.js";
