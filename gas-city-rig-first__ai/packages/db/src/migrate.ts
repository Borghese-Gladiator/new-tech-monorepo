import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { migrate } from "drizzle-orm/better-sqlite3/migrator";
import { createDb } from "./db.js";

export function migrationsFolder(): string {
  const here = dirname(fileURLToPath(import.meta.url));
  return resolve(here, "..", "drizzle");
}

export function runMigrations(url?: string): void {
  const handle = createDb(url);
  try {
    migrate(handle.db, { migrationsFolder: migrationsFolder() });
  } finally {
    handle.close();
  }
}

const isMain =
  import.meta.url === `file://${process.argv[1]}` ||
  import.meta.url.endsWith(process.argv[1] ?? "");

if (isMain) {
  runMigrations();
  // eslint-disable-next-line no-console
  console.log("migrations applied");
}
