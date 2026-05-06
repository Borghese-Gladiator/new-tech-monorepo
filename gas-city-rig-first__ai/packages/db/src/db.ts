import { mkdirSync } from "node:fs";
import { dirname } from "node:path";
import Database, { type Database as SqliteDatabase } from "better-sqlite3";
import { drizzle, type BetterSQLite3Database } from "drizzle-orm/better-sqlite3";
import type { ExtractTablesWithRelations } from "drizzle-orm";
import type { SQLiteTransaction } from "drizzle-orm/sqlite-core";
import type { RunResult } from "better-sqlite3";
import * as schema from "./schema.js";

export type Db = BetterSQLite3Database<typeof schema>;

export type DbTx = SQLiteTransaction<
  "sync",
  RunResult,
  typeof schema,
  ExtractTablesWithRelations<typeof schema>
>;

/**
 * Accepted by repo helpers — either the top-level db handle or a
 * transaction-bound handle. Both share the same drizzle query API.
 */
export type DbOrTx = Db | DbTx;

export type DbHandle = {
  db: Db;
  sqlite: SqliteDatabase;
  close: () => void;
};

/**
 * Run `fn` inside a single sqlite transaction. Throws abort the transaction so
 * neither partial writes nor side-effects of dependent inserts persist.
 */
export function runInTransaction<T>(db: Db, fn: (tx: DbTx) => T): T {
  return db.transaction((tx) => fn(tx));
}

const DEFAULT_URL = "file:./.data/poker.db";

export function resolveDatabasePath(url: string | undefined): string {
  const raw = url ?? DEFAULT_URL;
  if (raw.startsWith("file:")) return raw.slice("file:".length);
  return raw;
}

export function createDb(url?: string): DbHandle {
  const resolved = url ?? process.env.DATABASE_URL ?? DEFAULT_URL;
  const path = resolveDatabasePath(resolved);
  if (path !== ":memory:") {
    mkdirSync(dirname(path), { recursive: true });
  }
  const sqlite = new Database(path);
  sqlite.pragma("journal_mode = WAL");
  sqlite.pragma("foreign_keys = ON");
  const db = drizzle(sqlite, { schema });
  return {
    db,
    sqlite,
    close: () => sqlite.close(),
  };
}
