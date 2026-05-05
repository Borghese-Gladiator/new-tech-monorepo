# Gas Town First
Gas City is the next-generation successor to Gas Town.

Instead of being a monolithic system, it’s a general-purpose SDK for building agent orchestration systems. Gas City ≈ “Terraform + Kubernetes primitives for agent systems” => Instead of using a prebuilt “town,” you design your own city.

## Features
- declarative city config `city.toml`
- runtime providers - tmux, subprocesses, Kubernetes, etc.
- work routing system
- formulas + orders (task orchestration)
- supervisor loop (desired state -> actual state)
- health patrol (monitoring & recovery)


## Setup
read: https://github.com/gastownhall/gascity/blob/main/docs/getting-started/quickstart.md
- install
  ```
  brew install gastownhall/gascity/gascity
  ```
- fix alias so you can run it
  - open `~/.zshrc`
  - delete usages of `alias gc`
  - if not enough, add `unalias gc unalias gc 2>/dev/null`
    - This fixes `gc` from the default git plugin in Oh My Zsh with iterm2
- run bootstrap script from ChatGPT (note that it'll delete this README)
  ```
  chmod+ bootstrap.sh
  ./bootstrap poker-city
  ```
- create City Controller
  ```
  gc init gas-city-controller-first__ai
  cd gas-city-controller-first__ai
  ```
  - NOTE: City Controller does NOT need an explicit Beads database. Do not run `bd init` inside the city controller
- create City Rig
  ```
  mkdir ~/GitHub/LOCAL_worktrees/202604_gas_city_first__ai/gas-city-rig-first__ai
  gc rig add ~/GitHub/LOCAL_worktrees/202604_gas_city_first__ai/gas-city-rig-first__ai
  ```
  - `gc rig list`
  - `gc rig remove gas-city-rig-first__ai`
- create Beads Database inside Controller
  ```
  gc rig add ~/GitHub/LOCAL_worktrees/202604_gas_city_first__ai/gas-city-controller-first__ai
  bd init --prefix gccfa  # NOTE: use prefix based on the `gc rig` results
  ```
- Sling Work at the rig from inside the controller
  ```
  gc sling claude "Create a script that prints gas city works"
  ```


#### Troubleshooting
<details>
<summary>Wiping and getting a clean slate</summary>


How to build a clean slate
- delete repo
  ```
  rm -rf
  ```
- check for hidden files (eg: `beads`)
  - `ls -la`
  - `rm -rf .beads`
- unregister the cities from gc
  ```
  gc cities
  gc unregister <city_name>
  ```
</details>

<details>
<summary>bd autocommit</summary>

- initialize beads
  ```
  bd init
  ```
  - ensure you click `No` on this option, otherwise, you will get a random WIP commit every 10 minutes
    ```
      Auto-export keeps .beads/issues.jsonl up to date after every write command.
      This is useful for viewers (bv) and git-based sync workflows.

    Enable auto-export? [Y/n]: n
    ```
</details>


# Multiplayer Poker PoC

Stack:
- Next.js web app
- Node.js Socket.IO server
- Drizzle persistence
- TypeScript monorepo
- Playwright-ready browser journeys

Start by implementing:
1. packages/poker-core
2. packages/db
3. apps/server
4. apps/web
5. Playwright journeys


---

# Addendum — End-to-end sling verification (2026-05-04)

This addendum records the working end-to-end sling pipeline and the orphan-bead diagnosis that preceded it. Refer back here whenever `gc sling` fails with `database not initialized` or beads appear to vanish.

## Verified pipeline

A hello-world bead was slung from the controller, picked up by an auto-spawned rig session, implemented, committed, and closed.

```bash
gc --city gas-city-controller-first__ai sling \
  gas-city-rig-first__ai/claude \
  "Create a hello.txt file in the rig root with the contents: hello from gas city"
```

Result:
- Bead `gcrfa-cx5` created in the rig's Dolt DB (`gcrfa`).
- Auto-convoy `gcrfa-7r9` and wisp `gcrfa-z3o` (formula `mol-do-work`) attached.
- Session `hq-bho` (template `gas-city-rig-first__ai/claude`) auto-spawned by the controller. After the first session went idle without closing the bead, the reconciler spawned `hq-4jv` which finished the work.
- `hello.txt` written to the rig root and committed: `d0903a3 feat: add hello.txt to rig root`.
- Bead closed with note: `"Done: Created hello.txt in rig root with 'hello from gas city' content and committed."`

## Beads topology

There is **one** Dolt SQL server (`dolt sql-server`, port 40036) hosting multiple databases. Each `.beads/dolt-server.port` file in both controller and rig points at the same port.

| Location | Database | Prefix | Purpose |
|----------|----------|--------|---------|
| `gas-city-controller-first__ai/.beads/` | `hq` | `hq` | Controller-side beads (orders, runtime, supervisor work) |
| `gas-city-rig-first__ai/.beads/` | `gcrfa` | `gcrfa` | Rig-side application work |

Use `gc bd context` to confirm which database `bd` is talking to from any cwd. The `--rig <name>` flag selects the rig DB; without it, you talk to the controller DB.

## The orphan-bead bug

**Symptom:** `gc sling` failed with `bd create: database not initialized: issue_prefix config is missing (run 'bd init --prefix <prefix>' for a new project, or 'bd bootstrap' to clone an existing remote)`. Beads from earlier slings appeared to be missing.

**Root cause:** the `gcrfa` and `hq` Dolt databases were missing the `issue_prefix` row in the `config` table. `bd bootstrap --yes` printed `Created fresh database with prefix "gcrfa"` but did not actually persist that row to the running Dolt server. Every subsequent `bd create` failed before reaching the bead-creation path.

**Secondary symptom:** the controller has a stale `.gc/beads.json` containing 76 orphaned beads (`gc-1` through `gc-76`) from a previous run that used the JSON backend. The active backend is now Dolt, so those beads are unreachable. They are not loaded by the supervisor, do not appear in `bd list`, and never execute. Safe to delete or archive.

**Fix (idempotent, safe to re-run):**

```bash
# Rig DB
gc --city gas-city-controller-first__ai --rig gas-city-rig-first__ai \
  bd sql "INSERT INTO config (\`key\`, value) VALUES ('issue_prefix', 'gcrfa')"

# Controller DB
gc --city gas-city-controller-first__ai \
  bd sql "INSERT INTO config (\`key\`, value) VALUES ('issue_prefix', 'hq')"
```

Verify:

```bash
gc --city gas-city-controller-first__ai --rig gas-city-rig-first__ai bd config get issue_prefix
# → gcrfa
gc --city gas-city-controller-first__ai bd config get issue_prefix
# → hq
```

After this, `gc sling` works.

## How to verify a sling end-to-end

1. Sling: `gc --city <controller> sling <rig>/claude "<task text>"`. Note the bead id returned (e.g. `gcrfa-cx5`).
2. Confirm bead is in the live Dolt DB (not orphaned in `.gc/beads.json`):

   ```bash
   gc --city <controller> --rig <rig> bd show <bead-id>
   ```

3. Confirm a session was auto-spawned: `gc --city <controller> session list`. Expect a row with template `<rig>/claude` and state `creating` → `active`.
4. Watch for closure: poll `bd show <bead-id> --json` until `status` is `closed`. The reconciler may spawn a follow-up session if the first one goes idle without finishing — this is expected.
5. Verify side effects: the file/commit the bead asked for is in the rig.

## Next steps for the poker PoC

The 8 implementation beads (monorepo skeleton, poker-core, db, shared, server, server verification, web, web verification, Playwright journeys, review) can now be slung the same way. Stale `.gc/beads.json` should be deleted before the run so it doesn't get confused with live beads.


---

# Addendum 2 — Full PoC build-out via Gas City sling loop (2026-05-04 → 2026-05-05)

After the end-to-end pipeline was verified (Addendum 1), the entire 2-handed multiplayer Texas Hold'em PoC was built and hardened by slinging discrete beads to the rig. Each bead implemented one slice, ran its own typecheck/test gate, committed, and closed. No manual interventions during the loop other than a one-time gitignore patch (described below).

## Sling cadence

| # | Bead | Outcome | Commit |
|---|---|---|---|
| 1 | Monorepo skeleton (pnpm + TS) | `package.json`, `tsconfig.base.json`, `pnpm-workspace.yaml`, `.nvmrc` | `6c01f87` |
| 2 | `packages/poker-core` (rules engine) | 40 vitest tests covering deck/RNG/turn-order/legal/betting/pot/street/showdown | `839f919` |
| 3 | `packages/db` (Drizzle persistence) | 5 tables, 5 repo fns, drizzle migrations, in-memory sqlite integration test | `0075782` |
| 4 | `packages/shared` (Socket.IO event DTOs) | 4 client→server + 4 server→client events, `AckResult`, runtime guard | `c70b2a0` |
| 5 | `apps/server` (authoritative service) | Socket.IO 4 gateway, room lifecycle, server-side validation, reconnect, persistence | `8062ead` |
| 5b | `GET/POST /games` HTTP routes (added during web bead) | Lobby data API exposed to web | `6b96c9b` |
| 6 | `apps/web` (Next.js 14 App Router) | Lobby, table, components (Seat, Pot, Board, ActionBar, ConnectionPill), socket wiring, sessionToken cookie reconnect | `d37b49a` |
| 7 | Playwright journeys (`tests/journeys`) | 3 specs: create-and-join, fold-resolves-hand, reconnect-survives-refresh — all green on first run | `fdb2d59` |
| 8 | Code-steward review (REVIEW.md) | 1 BLOCKER + 2 MAJOR + 9 MINOR surfaced; ranked, with file:line repros | `4185ada` |

## Review-driven hardening (REVIEW.md follow-ups)

Each REVIEW.md finding the team prioritized was slung as a separate bead. All passed their own gates and the prior journey suite.

| Finding | Outcome | Commit |
|---|---|---|
| **B1 (BLOCKER)** — sub-min all-in raise let prior raiser re-raise illegally | Added `PlayerState.actionReopened` flag tracked per-street; gated `legalActions.canRaise` on it. 2 new tests (the REVIEW.md repro + a positive control). poker-core: 40 → 42 tests | `5bb5b0a` |
| **M1 (MAJOR)** — `apps/web` imported `@gas-city/poker-core` directly | Re-exported needed types from `@gas-city/shared`; rewrote 6 web files; dropped `@gas-city/poker-core` from `apps/web/package.json` and `next.config.mjs` `transpilePackages` | `7b56f75` |
| **M2 (MAJOR)** — `GameState.events` unbounded and embedded in every snapshot | Option B: dropped `events` from `GameState` entirely; `startHand` now returns `{state, events}`; persistence size measured ≈2KB/snapshot (previously O(actions²)) | `4342b31` |
| **m2 (MINOR)** — persist + broadcast not wrapped in a transaction | Added `runInTransaction` helper to `@gas-city/db`; engine wraps snapshot+event inserts atomically; new atomicity test asserts neither row commits on mid-callback throw | `4d7285c` |
| **m5 (MINOR)** — `seats.sessionToken` lacked UNIQUE constraint | Partial unique index `WHERE session_token IS NOT NULL`; migration `0001_productive_photon.sql`; new uniqueness test | `8085394`, `aa83164` |

## Validation-driven follow-ups (VALIDATION.md follow-ups)

After live Playwright MCP validation surfaced two additional bugs beyond the REVIEW.md set:

| Finding | Outcome | Commit |
|---|---|---|
| **BUG-V1 (MAJOR, live-only)** — joining a full game silently strands the client at "Waiting for opponent…" | Added `ErrorCode.GAME_FULL`. Server rejects `joinGame` when no `sessionToken` AND (game.status != open OR no open seat). Web client clears session cookie and `router.replace('/')` on receipt. 2 new server integration tests | `fabacdf` |
| **BUG-V2 (cosmetic, live-only)** — pot panel showed "2 side pots" on heads-up SB+BB hand with no all-in | Option A (web-only): `meaningfulSidePotCount` helper in `apps/web/src/lib/pot.ts`; subtext now hidden for non-all-in hands and renders "1 side pot" / "N side pots" for real all-ins. poker-core untouched | `9150422` |

## The lib/ gitignore trap (worth knowing)

The monorepo-wide `.gitignore` (one directory above the rig) has a Python-era `lib/` rule that silently swallowed `gas-city-rig-first__ai/apps/web/src/lib/{cookies,socket,tableState}.ts`. Three files compiled fine on disk and the journeys passed against them, but **none were tracked in git** until commit `aee1378 fix(web): track apps/web/src/lib/ that parent .gitignore was hiding`. The fix was to add a negation in the rig-local `.gitignore`:

```
!apps/*/src/lib/
!apps/*/src/lib/**
```

Worth verifying after any large web bead: run `git status` and look for "untracked files" in `apps/web/src/lib/`. The agent reviewing M1 caught this in its closing notes — don't ignore agent close-notes when they flag this kind of footgun.

## Live Playwright MCP validation

Beyond the headless Playwright suite in `tests/journeys/`, the apps were driven end-to-end through the live MCP browser tool against running services:

- ✅ Lobby render, create+join, auto-start-on-2nd-seat
- ✅ Server-authoritative state synced across two browser contexts
- ✅ Hole cards visible only to the owning seat
- ✅ Fold-resolves-hand journey (Alice folds → Bob wins pot)
- ✅ Chip conservation (199 + 201 = 400 = 200 + 200)
- ✅ F5 refresh reconnect — sessionToken cookie restores seat
- ✅ **Server-restart reconnect** — killed server PID, restarted, both clients rehydrated with intact stacks/cards/event-log. This is the live-validation proof that `m2`'s transaction wrap holds across cold start.

The two new bugs found during this validation (BUG-V1, BUG-V2) are recorded in `gas-city-rig-first__ai/VALIDATION.md` along with screenshots; both are now fixed (commits `fabacdf`, `9150422`).

## Outstanding (non-blocking)

REVIEW.md MINORs not yet slung: m1 (handler refactor — cosmetic), m3 (`handId` hardcoded), m4 (no auto-fold-on-disconnect timer), m6 (`firstToActPreflop` null edge), m7 (showdown evaluator complexity), m8 (deterministic seed mixer), m9 (`restorePlayerSeat` filters). Plus the lobby observation that resolved-hand games disappear from `Open games` (may be intentional).

## Final commit graph (most recent at top)

```
9150422 fix(web): hide misleading 'side pots' subtext when no all-in
fabacdf fix(server,web): reject join on full game with GAME_FULL playerError
38897d3 docs(validation): live Playwright MCP run + 2 new bugs found
aa83164 test(db): assert UNIQUE constraint on seats.sessionToken
8085394 fix(db): add UNIQUE index on seats.sessionToken
4d7285c fix(server): wrap persistStateAndEvents in a sqlite transaction
aee1378 fix(web): track apps/web/src/lib/ that parent .gitignore was hiding
4342b31 fix(poker-core): drop GameState.events to bound snapshot size
7b56f75 fix(web): import poker-core types from @gas-city/shared
5bb5b0a fix(poker-core): sub-min all-in must not reopen action
4185ada docs(review): pre-merge code review of poker PoC
fdb2d59 test(journeys): Playwright smoke browser journeys for poker PoC
d37b49a feat(web): Next.js client for poker PoC (lobby + table)
6b96c9b feat(server): expose GET/POST /games HTTP routes
8062ead feat(server): authoritative Socket.IO multiplayer poker service
c70b2a0 feat(shared): Socket.IO event DTOs wire-contract package
0075782 feat(db): drizzle persistence package for poker PoC
839f919 feat(poker-core): pure rules engine package
6c01f87 feat(rig): bootstrap pnpm + TypeScript monorepo skeleton
fd53383 docs(gas-city): document end-to-end sling pipeline + ignore agent runtime
```
