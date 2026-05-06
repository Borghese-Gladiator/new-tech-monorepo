# packages/db — plan

## Brief
Drizzle ORM persistence package for the multiplayer poker PoC. SQLite via `better-sqlite3` for the PoC. No runtime dependency on `@gas-city/poker-core` — only a `type`-only import for `GameState`. Strict TS, vitest tests.

## Changes

```
packages/db/
  package.json          # name @gas-city/db, scripts (typecheck, lint, test, db:generate, db:migrate); deps: drizzle-orm, better-sqlite3; devDeps: drizzle-kit, tsx, vitest, typescript, @types/better-sqlite3
  tsconfig.json         # extends ../../tsconfig.base.json
  vitest.config.ts      # node env
  drizzle.config.ts     # dialect sqlite, schema path, out ./drizzle
  src/
    index.ts            # barrel — exports schema, repos, createDb factory
    schema.ts           # games, players, seats, game_snapshots, game_events
    db.ts               # createDb(url): {db, sqlite} factory; resolves DATABASE_URL or default file:./.data/poker.db
    repos.ts            # saveSnapshot, appendGameEvent, loadGame, listOpenGames, restorePlayerSeat
    migrate.ts          # CLI entry: tsx src/migrate.ts — runs drizzle-kit migrations against DATABASE_URL
  test/
    repos.test.ts       # in-memory sqlite, runs migrations, exercises every repo function
  drizzle/              # generated migrations (committed)
```

## Schema details

- games: id (pk auto), status text check ('open','in_progress','finished'), button_seat int nullable, current_street text nullable, created_at, updated_at (epoch ms)
- players: id (pk auto), display_name text, created_at
- seats: id (pk auto), game_id fk, player_id fk, seat_index int, stack int, status text check ('active','folded','all_in','sitting_out'), session_token text nullable; unique(game_id, seat_index)
- game_snapshots: id (pk auto), game_id fk, snapshot_index int, state text json, created_at; unique(game_id, snapshot_index)
- game_events: id (pk auto), game_id fk, event_index int, event_type text, payload text json, created_at; unique(game_id, event_index)

## Repo functions

- `saveSnapshot(db, gameId, state: GameState)`: pulls max(snapshot_index) for the game, inserts new row at idx+1.
- `appendGameEvent(db, gameId, event: {type, payload})`: similar — bumps event_index.
- `loadGame(db, gameId, eventLimit = 50)`: latest snapshot by snapshot_index; open seats (seats with status != 'sitting_out'); last N events ordered by event_index desc.
- `listOpenGames(db)`: status in ('open','in_progress'), ordered by updated_at desc.
- `restorePlayerSeat(db, gameId, sessionToken)`: select seat row by (game_id, session_token), or null.

## Tests

### Unit/integration (vitest)
- One test file: opens in-memory sqlite (`:memory:`), runs a helper that applies migration SQL (drizzle-kit generated), then exercises:
  - insert game + players + seats
  - saveSnapshot twice → loadGame returns the latest
  - appendGameEvent twice → loadGame returns last events ordered correctly
  - listOpenGames returns only open/in_progress
  - restorePlayerSeat returns the seat for a known session_token, null for an unknown one

### Manual
N/A — backend-only, no UI.

## Acceptance
- `pnpm --filter @gas-city/db typecheck`
- `pnpm --filter @gas-city/db db:generate` (produces SQL in ./drizzle)
- `pnpm --filter @gas-city/db test`
