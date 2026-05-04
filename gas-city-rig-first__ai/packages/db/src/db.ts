import { mkdirSync } from "node:fs";
import { dirname } from "node:path";
import Database, { type Database as SqliteDatabase } from "better-sqlite3";
import { drizzle, type BetterSQLite3Database } from "drizzle-orm/better-sqlite3";
import * as schema from "./schema.js";

export type Db = BetterSQLite3Database<typeof schema>;

export type DbHandle = {
  db: Db;
  sqlite: SqliteDatabase;
  close: () => void;
};

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
