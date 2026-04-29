# Gas City Bootstrap TODO

Scope: only modify `gas-city-controller-first__ai/` and `gas-city-rig-first__ai/`.

Mapping rule:
- Orchestration artifacts (city.toml, agents, formulas, orders, prompts) → **controller**
- Application code (apps/*, packages/*) → **rig**

---

## 1. Controller — `gas-city-controller-first__ai/`

### 1a. Update `city.toml`
Replace current minimal config with the multiplayer-poker scaffold config:
- [X] Do NOT change the name for the city controller
- [ ] Add `[project]` block (name, description, repo, stack)
- [ ] Add `[defaults]` (pnpm, node >=20)
- [ ] Add `[workspace]` mapping `web`, `server`, `core`, `db`, `shared`
- [ ] Add `[quality]` commands (typecheck, lint, unit, browser)
- [ ] Add `[constraints]` (real_money=false, auth=false, multiplayer, persistence, socket.io, drizzle, playwright)
- [ ] Keep existing `[[rigs]]` entry pointing at `gas-city-rig-first__ai`

### 1b. Agents — `agents/`
Existing: `mayor/`. Use a leaner, fully-generic 5-agent set so domain
specifics live in formulas, not agent names (per Gas City guidance).
- [ ] `agents/frontend-engineer.toml` — any UI / client work
- [ ] `agents/backend-engineer.toml` — server + pure-logic packages (folds in rules + data/migrations for the PoC)
- [ ] `agents/verification-engineer.toml` — static checks + unit/integration tests
- [ ] `agents/journey-tester.toml` — Playwright / browser journeys
- [ ] `agents/code-steward.toml` — review before merge
- [ ] Decide: keep or retire `agents/mayor/` (legacy from gas-town carryover)

Dropped from earlier draft: `app-engineer`, `service-engineer`,
`rules-engineer` — responsibility-specific names. Their domain context
belongs in the formulas (`implement-web-client`, `implement-realtime-service`,
`implement-poker-engine`), which is what gets slung at the generic agents.

### 1c. Formulas — `formulas/`
Currently empty. Add seven `*.formula.toml` files:
- [ ] `formulas/implement-poker-engine.formula.toml`
- [ ] `formulas/implement-realtime-service.formula.toml`
- [ ] `formulas/implement-persistence.formula.toml`
- [ ] `formulas/implement-web-client.formula.toml`
- [ ] `formulas/run-verification.formula.toml`
- [ ] `formulas/run-browser-journeys.formula.toml`
- [ ] `formulas/review-change.formula.toml`

### 1d. Orders — `orders/`
Currently empty. Add:
- [ ] `orders/verify-on-change.toml` (formula = run-verification, agents = [verification-engineer])
- [ ] `orders/review-before-merge.toml` (formula = review-change, agents = [code-steward])

### 1e. Prompts — `prompts/`
Directory does not exist yet. Create it and add the four prompt files
in the order below — each one assumes the previous as context.

1. [ ] **2026-04-29** — `prompts/product-scope.md` — in/out of scope for the PoC *(defines the "what" — must come first; everything else narrows from here)*
2. [ ] **2026-04-29** — `prompts/architecture.md` — monorepo layout (web / server / poker-core / db / shared) *(turns scope into structure)*
3. [ ] **2026-04-29** — `prompts/multiplayer-rules.md` — server-authoritative event contract *(fills in runtime behavior across the architecture)*
4. [ ] **2026-04-29** — `prompts/testing-policy.md` — required checks + minimum browser journeys *(verifies the three above)*

---

## 2. Rig — `gas-city-rig-first__ai/`

Currently empty. This is where actual code lives.

### 2a. Monorepo skeleton
- [ ] `package.json` (root, pnpm workspaces, scripts: typecheck, lint, test, test:e2e)
- [ ] `pnpm-workspace.yaml` (`apps/*`, `packages/*`)
- [ ] `tsconfig.base.json`
- [ ] `.nvmrc` (>=20)
- [ ] `.gitignore`

### 2b. `packages/poker-core/` — pure rules engine (no socket / no db imports)
- [ ] Types: `GameState`, `PlayerState`, `Seat`, `Deck`, `Card`, `Action`, `Street`, `Pot`, `GameEvent`
- [ ] State transitions: shuffle, deal, legal actions, betting rounds, fold/check/call/raise, showdown
- [ ] Deterministic unit tests: deck uniqueness, turn order, legal-action validation, pot updates, street transitions

### 2c. `packages/db/` — Drizzle persistence
- [ ] Schema: `games`, `players`, `seats`, `game_snapshots`, `game_events`
- [ ] Repository fns: `saveSnapshot`, `appendGameEvent`, `loadGame`, `listOpenGames`, `restorePlayerSeat`
- [ ] `drizzle-kit generate` + `migrate` wired into scripts

### 2d. `packages/shared/` — wire contracts
- [ ] Socket event DTOs: `joinGame`, `leaveGame`, `playerAction`, `gameSnapshot`, `gameEvent`, `reconnectSession`, `playerError`, `connectionStatus`

### 2e. `apps/server/` — authoritative Socket.IO service
- [ ] Socket.IO gateway + room lifecycle
- [ ] Server-side validation through `poker-core`
- [ ] Reconnect support (Socket.IO + persisted session token → seat restore)
- [ ] Persist game/player/seat/action-log/snapshot via `db`

### 2f. `apps/web/` — Next.js client
- [ ] Lobby: create / join / resume / list open games
- [ ] Table: seats, hole cards, community cards, pot, current player, street, action controls
- [ ] Socket.IO client: connection status, reconnect, snapshot/event handlers, error display

### 2g. Browser journeys
- [ ] Playwright config + smoke journeys: create game, second player joins, hand starts, fold, reconnect, refresh-survives-state

---

## 3. Build order (ship-vertical)
1. Controller scaffolding (1a–1e) so `gc sling` has agents/formulas/orders to dispatch.
2. `packages/poker-core` (rules + tests) — no external deps.
3. `packages/db` (schema + repos + migrations).
4. `packages/shared` (event contracts) — unblocks both server and web.
5. `apps/server` (authoritative service).
6. `apps/web` (lobby + table + socket client).
7. Playwright journeys.
8. Wire `orders/verify-on-change` + `orders/review-before-merge` into the loop.

---

## 4. Out of scope (do not touch)
- Any directory other than `gas-city-controller-first__ai/` and `gas-city-rig-first__ai/`.
- Real money, auth, payments, tournaments, rankings.
