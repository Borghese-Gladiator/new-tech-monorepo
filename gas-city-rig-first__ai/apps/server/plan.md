# apps/server — plan

## Brief

Server-authoritative multiplayer poker service. Socket.IO 4 over Node 20+,
TypeScript strict ESM. Validates every client action through
`@gas-city/poker-core`, persists snapshots and events through `@gas-city/db`,
and emits typed events from `@gas-city/shared`.

## Changes

```
apps/server/
  package.json          # @gas-city/server, ESM, scripts (dev/start/typecheck/test/build)
  tsconfig.json         # extends ../../tsconfig.base.json, NodeNext module
  vitest.config.ts      # node env, includes test/**/*.test.ts
  src/
    index.ts            # entry point: createServer() + listen on PORT (default 4000)
    server.ts           # createServer(opts) — exposes io, httpServer, db handle for tests
    rooms.ts            # in-memory map: gameId -> { state, seatBySocket }; bootRoomsFromDb
    errors.ts           # ErrorCode constants + makeError + emitPlayerError helper
    handlers/
      joinGame.ts       # join (with optional sessionToken) + auto startHand when 2 seats
      leaveGame.ts      # mark seat folded if in-hand, otherwise remove from room
      playerAction.ts   # validate, apply, advance street, resolve hand, persist + emit
      reconnectSession.ts # rebind socket → seat, send fresh snapshot to that socket
      index.ts          # registerHandlers(io, socket, ctx)
  test/
    integration.test.ts # 2 clients, fold, hand resolves, both receive event + snapshot
```

## Key behaviors

- **Persistence cadence**: every state-mutating handler persists `saveSnapshot` +
  `appendGameEvent` (one call per new event from poker-core). Wrapped in
  `db.transaction` if available; the package today does not expose a tx helper —
  flagged as TODO.
- **Reconnect**: `joinGame` with `sessionToken` triggers `restorePlayerSeat`
  → if found, rebind socket; if not found, fall through to new-seat creation.
- **Auto-start**: For PoC, when a 2-seat game has both seats filled, server
  immediately calls `startHand` and broadcasts the initial snapshot.
- **Hand advancement**: After every legal `playerAction`, the server loops
  through `isBettingRoundClosed` → `advanceStreet` and `isHandOver` →
  `resolveHand` until the hand is settled or another player must act.
- **Hole cards**: `gameSnapshot` is broadcast to the room without hole cards;
  each client also receives a per-socket snapshot with their own `you.holeCards`.

## Tests

### Unit / integration (vitest)
- `test/integration.test.ts`:
  - boot server on a random port with in-memory sqlite
  - connect 2 socket.io-client instances, both joinGame
  - server starts hand → both receive `gameSnapshot` (with their own `you.holeCards`)
  - client at currentSeat sends `playerAction { kind: 'fold' }`
  - both clients receive a `gameEvent` (action-taken) AND a `gameSnapshot` showing
    pots empty and hand resolved
  - assert both ack results are `{ ok: true }`

### Manual
N/A — backend, exercised by the integration test.

## Acceptance

- `pnpm install`
- `pnpm --filter @gas-city/server typecheck`
- `pnpm --filter @gas-city/server test`
