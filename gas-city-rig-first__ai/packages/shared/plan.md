# packages/shared — Socket.IO event DTOs

## Brief
Wire-contract package shared by the server and web client. Defines the typed
Socket.IO event payloads, the `ClientToServerEvents` / `ServerToClientEvents`
generic maps, and a small ad-hoc runtime guard so the package is not
type-only.

## Changes
- `packages/shared/package.json`: workspace package `@gas-city/shared`,
  scripts for `typecheck` and `lint` (both `tsc --noEmit`), no test script.
  `sideEffects: false`. Workspace dep on `@gas-city/poker-core` for type-only
  imports of `GameState` / `GameEvent` / `Card`.
- `packages/shared/tsconfig.json`: extends workspace base, mirrors `db` /
  `poker-core` setup (`noEmit: true`, includes `src/**`).
- `packages/shared/src/events.ts`: payload types for the four C→S events,
  the four S→C events, plus `AckResult`. Type-only `import type` from
  `@gas-city/poker-core` for `GameState`, `GameEvent`, `Card`.
- `packages/shared/src/guards.ts`: at minimum
  `isJoinGamePayload(value: unknown): value is JoinGamePayload`. Plain
  hand-rolled `typeof` checks — no zod.
- `packages/shared/src/index.ts`: barrel re-export of payload types,
  `AckResult`, the `ClientToServerEvents` / `ServerToClientEvents` map
  types, and the runtime guard(s).

## Tests
### Unit
None — package has no test script per the assignment.

### Manual
- `pnpm install` at the repo root so the new workspace package is linked.
- `pnpm --filter @gas-city/shared typecheck` passes.
