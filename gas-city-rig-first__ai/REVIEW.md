# Pre-merge code review — Gas City Poker PoC

Reviewer: code steward (gcrfa-qrw, molecule gcrfa-i6t)
Scope: packages/poker-core, packages/db, packages/shared, apps/server, apps/web, tests/journeys
Verdict: **Ship after fixing 1 BLOCKER + 2 MAJOR.**

## Findings

### BLOCKER

#### B1. Sub-minimum all-in raise lets the prior raiser re-raise illegally
`packages/poker-core/src/legal.ts:14-53`, `packages/poker-core/src/betting.ts:62-89`

Standard NL rule: when an all-in raise increments below the previous full raise size, action is NOT reopened for any player who already acted. They may only call or fold.

The engine half-implements this. In `betting.ts:63`:
```ts
raiseReopens = raiseIncrement >= state.lastRaiseSize;
```
…and `nextLastRaiseSize` is only updated when `raiseReopens` is true (line 65-67). So `lastRaiseSize` correctly stays at the prior full-raise increment after a sub-min all-in, and the `hasActedThisStreet` flag for already-acted players is correctly NOT cleared (line 82-88).

But `legalActions` (`legal.ts:14-53`) gates `canRaise` only on chip availability:
```ts
const canRaise = maxRaiseTo > state.currentBet && player.stack > toCall;
```
There is no check for "did the most recent raise reopen action for *this* seat." So a player who already acted and is being asked to act again only because of a partial-call shortfall (the fallback in `betting.ts:108-122` picks them up since `committedThisStreet < nextCurrentBet`) is told `canRaise=true`.

Concrete repro (3-handed, blinds 1/2, BTN=seat 0 with 200, SB=seat 1 with 200, BB=seat 2 with 9 starting stack):
1. Blinds posted. BB has stack 7 left after posting. `currentBet=2`, `lastRaiseSize=2`. UTG-equivalent here is BTN (seat 0) — it acts first preflop with 3 players, since UTG = next after BB which wraps to seat 0.
2. BTN raises to 6 → `currentBet=6`, `lastRaiseSize=4`, hasActedThisStreet for SB/BB cleared.
3. SB calls 6 → `hasActedThisStreet=true`, committedThisStreet=6.
4. BB shoves all-in to 9 (their full 9 chips on the street: 2 blind + 7 stack). raiseIncrement = 9 − 6 = 3 < 4. `raiseReopens=false`, `lastRaiseSize` stays at 4. SB's `hasActedThisStreet` stays true.
5. Engine looks for next actor. BTN: `hasActedThisStreet=true` and `committedThisStreet=6 < currentBet=9` — picked up by the fallback at `betting.ts:108-122`.
6. `legalActions(BTN)` returns `canRaise=true` because BTN has stack > toCall (3). **BTN can re-raise to 13 (= 6+7) or higher, even though under NL rules they may only call or fold.**

This corrupts the betting sequence: BTN's illegal re-raise becomes a new full raise, reopens action for SB and BB, and the engine accepts it as valid. The "server is authoritative on legal actions" property fails.

There is no test for the all-in-doesn't-reopen rule (`legal.test.ts` covers only basic min-raise rejection at line 29-33 and the postflop check/bet at 51-70).

Fix sketch: track per-seat per-street whether action has been re-opened. After applying a raise, set `actionReopenedFor: ReadonlyArray<Seat>` containing only seats that haven't acted yet OR all opponents if the raise was full. `legalActions` returns `canRaise=false` when the seat is being pulled back to act only via partial-call shortfall and the most recent raise was sub-minimum. Add a unit test mirroring the repro above.

---

### MAJOR

#### M1. `apps/web` depends on `@gas-city/poker-core` directly
`apps/web/package.json:13`, `apps/web/src/lib/tableState.ts:1-6`, `apps/web/src/components/Seat.tsx:1`, `apps/web/src/components/ActionBar.tsx:4`, `apps/web/src/components/Board.tsx:1`, `apps/web/src/components/Pot.tsx:1`, `apps/web/src/components/Card.tsx:1`

The bead explicitly asks: "Does apps/web only depend on packages/shared (not directly on poker-core or db)?" The answer is **no**. Six client files reach across the boundary to import `Card`, `PlayerState`, `Seat`, `Street`, `GameState`, `GameEvent`, `Pot` from `@gas-city/poker-core`. All usages are `import type`, so this is not a runtime-bundling problem — but the dependency declaration in `package.json` *is* a runtime dep, and the boundary contract the bead asks us to verify is broken at the package-graph level.

Fix: re-export the needed types from `@gas-city/shared/index.ts` (it already type-imports them in `events.ts`), drop `@gas-city/poker-core` from `apps/web/package.json`, and rewrite the six client imports to point at `@gas-city/shared`. `next.config.mjs:5` then no longer needs to transpile `@gas-city/poker-core`.

#### M2. `GameState.events` is unbounded and is embedded in every persisted snapshot
`packages/poker-core/src/betting.ts:135`, `packages/poker-core/src/street.ts:76`, `packages/poker-core/src/showdown.ts:80`, `apps/server/src/engine.ts:104`

Every state mutation appends to `state.events`. `saveSnapshot` then JSON-serializes the full `GameState` (`packages/db/src/repos.ts:58`), so each snapshot embeds the entire hand-history-to-date. With one snapshot per action in `playerAction.ts:143` and the events array growing on each action+street advance+showdown, storage is O(actions²) per hand. A 30-action hand stores ~30+ snapshots each ~30 events long.

This is also a *correctness* trap because the events stream is double-stored: once in `gameSnapshots.state` (embedded), once as rows in `gameEvents`. If a future loader trusts the snapshot's embedded events, replay can desync from the row-level event log.

Fix: drop `events` from the snapshot before persisting (`engine.ts:persistStateAndEvents` should serialize a copy with `events: []`). Even better, drop `events` from `GameState` entirely and make `events` a return value of action/street/showdown calls — `betting.ts`, `street.ts`, `showdown.ts` already return `events` in their result tuples; the field on `GameState` is redundant.

---

### MINOR

#### m1. Server handlers exceed the 100-LOC budget the bead asked us to verify
`apps/server/src/handlers/joinGame.ts` (187 lines), `apps/server/src/handlers/playerAction.ts` (149 lines)

`joinGame.ts` mixes five responsibilities: payload validation, game lookup-or-create, reconnect path, new-seat path, and the auto-start-on-full path. Auto-start (`joinGame.ts:159-185`) is a separate concern and could move to a tiny `maybeStartHand(ctx, gameId)` helper. `playerAction.ts:44-148` has a long happy-path; the validation/auth checks (`44-95`) are easy to extract.

#### m2. Persist + broadcast not wrapped in a transaction
`apps/server/src/engine.ts:96-108`

The TODO at `engine.ts:93` already calls this out. Right now `persistStateAndEvents` does N+1 inserts (one snapshot, then one row per event). If any insert fails mid-loop, you have a snapshot that disagrees with a partial event log. better-sqlite3 exposes `.transaction(fn)` via `dbHandle.sqlite`; wrap the whole thing in one. Acceptable for a PoC but trivial to fix.

#### m3. `handId` is hardcoded to 1
`packages/poker-core/src/start-hand.ts:38, 82`

Both `events: [{ handId: 1, ... }]` and `state.handId = 1`. A single hand at a time is the PoC scope, but flagging — the field exists in the type, it's just never advanced.

#### m4. Game stalls forever on disconnect during own turn
`apps/server/src/handlers/index.ts:13-18`

The TODO is honest: no auto-fold timer. With a single Socket.IO connection this is observable: if you disconnect on your own turn, the opponent has no way to progress the hand. PoC scope, but worth noting in the README.

#### m5. `seats.sessionToken` has no UNIQUE constraint
`packages/db/src/schema.ts:36-58`

The schema permits two seats to share a `sessionToken` (the constraint is `(gameId, seatIndex)` only). `randomUUID()` makes collision negligible, but `restorePlayerSeat` will silently return the wrong row if it ever did happen. Add `uniqueIndex` on `sessionToken` (or `(gameId, sessionToken)`).

#### m6. `firstToActPreflop` quietly returns `null` if no `active` player exists after BB
`packages/poker-core/src/seating.ts:60-75`

Edge case: 3-handed hand, BB shoves all-in via posting (BB > stack), then `bigBlindSeat` returns BB but `nextSeatIn(seated, bb, p => p.status === "active")` may return null if everyone else also went all-in via blinds. `start-hand.ts:76` then sets `currentSeat = null`, which silently leaves the hand stuck. Currently unreachable with default 200-stack/2-bb config but a real concern as soon as min-buy-ins drop. No test covers it.

#### m7. `evaluateBest5` runs C(7,5)=21 combinations with full sort each
`packages/poker-core/src/hand-eval.ts:51-70`

Acceptable for a PoC. Listed only because if the table moves to 9-handed showdowns the cost compounds. Standard Hold'em evaluators precompute lookup tables.

#### m8. `defaultGameConfig` re-uses `Date.now() % 1000` as a seed mixer
`apps/server/src/handlers/joinGame.ts:171`

`gameId * 1000 + Date.now() % 1000` produces a non-deterministic seed, defeating the purpose of having a seeded RNG. For a PoC this is fine, but it makes test reproduction harder and exposes the choice in a way that suggests cryptographic intent. Use a clearly random-ish seed (e.g. `randomBytes`) or, better, a deterministic one tied to gameId+handId for reproducible debugging.

#### m9. `restorePlayerSeat` doesn't filter by `seats.status != 'sitting_out'`
`packages/db/src/repos.ts:152-163`

Once a `leaveGame` flow flips a seat status (it currently only unbinds the socket — `leaveGame.ts:31`), reconnect by sessionToken will still resurrect the row. PoC scope, but the comment in `handlers/index.ts:14-15` ("keep the seat assigned") implies the intent. The status column accepts `sitting_out` per the schema check (`schema.ts:54`) but nothing writes it.

---

### Test gap audit (specific gaps, per the bead)

#### poker-core

- **No test for the all-in-below-min-raise rule** (the BLOCKER above). `legal.test.ts:29-33` rejects a generic short raise but never exercises the all-in exemption.
- **No test for chips conservation across a full hand**, only for individual mechanics. A property test that totals stacks pre-hand vs. post-hand and asserts `total_in == total_out + sum(pots_paid)` would have caught arithmetic drift.
- **No test for postflop turn order with a folded SB** (heads-up): `firstToActPostflop` filters to `active` only, but no test exercises the case where SB has folded preflop.
- **No test for `street.ts:advanceStreet` when `isHandOver(state)` is true mid-stream.** The current code skips dealing community cards (line 35) but still emits `street-advanced`. A unit test would clarify the intended behavior.

#### db

All five exported repo functions (`appendGameEvent`, `listOpenGames`, `loadGame`, `restorePlayerSeat`, `saveSnapshot`) ARE exercised in `repos.test.ts:62`. ✅

But: **no migration test** — the suite uses `migrate(... migrationsFolder())` and assumes drizzle's migrator. A trivial smoke test that opens a fresh `:memory:` DB, runs migrations, and does an `INSERT/SELECT` round-trip on every table would lock the schema's ergonomic shape against future drift.

#### server

- **No test for illegal-action rejection** at the socket layer. The integration test (`integration.test.ts`) covers a happy fold; nothing exercises `playerError` emission for `NOT_YOUR_TURN`, `ILLEGAL_ACTION`, `NOT_SEATED`.
- **No test for disconnect mid-hand**. The TODO at `handlers/index.ts:14` is unverified; a regression test would assert "if A disconnects, the room state stays intact and B receives no error".
- **No test for reconnect** at the integration layer — the journeys spec covers reconnect via browser refresh, but the socket-level `reconnectSession` event has no unit test asserting the per-seat snapshot replay.
- **No test for the join → auto-start trigger** with mismatched `seatRows` count (e.g., one seat reserved with stale state from a previous game).

#### journeys

All three specs exercise the real path through Next.js + the Socket.IO server (`playwright.config.ts:32-56` boots both). None mock. ✅

The `helpers.ts:findActionSeat` matches against `ring-2` Tailwind class string — this is fragile to JIT class minification (which Next disables in dev but enables in production builds). The journeys run against `pnpm run dev`, so it's safe in CI; flag as flaky if production builds are ever tested.

---

## Recommendations

Top 3 to fix before merge:

1. **Fix B1**: track per-street whether the most recent raise was a full raise; gate `canRaise` and `lastRaiseSize` updates on it. Add the missing `legal.test.ts` case.
2. **Fix M2**: stop persisting `state.events` inside snapshots. Either zero it out at `engine.ts:persistStateAndEvents` or remove the field from `GameState` entirely (it's already returned alongside actions/street/showdown results).
3. **Fix M1**: re-export the needed `poker-core` types from `@gas-city/shared`, drop `@gas-city/poker-core` from `apps/web/package.json`, and rewrite the six client imports. This is a 30-minute change with high-payoff boundary clarity.

The MINORs can ship as-is for a PoC, but m2 (transaction wrapping) and m4 (auto-fold-on-disconnect) are the two that affect any post-PoC playtest and should be on the immediate follow-up list.

---

## Out of scope (correctly avoided)

Confirmed *none* of these slipped in:

- **Real money / payments / wallets**: no Stripe, no payment routes, stacks are integers tied to in-memory game state.
- **Authentication / login**: `sessionToken` cookie is a per-game seat-resume token, not auth. No password, no JWT, no user table beyond the `players` row created on join.
- **Tournaments / rankings / leaderboards**: no tournament structures, no cross-game persistence of player results, no leaderboard query.

Boundary integrity:

- `packages/poker-core` has zero non-relative imports — pure logic. ✅ (verified by `grep -E "import .* from \"[^.]" packages/poker-core/src/*.ts` returning empty.)
- `packages/shared` only `import type`s from poker-core. ✅
- `packages/db` cleanly depends on `@gas-city/poker-core` for `GameState` only at the type level (used in `repos.ts:2` and the JSON serialization roundtrip). ✅
