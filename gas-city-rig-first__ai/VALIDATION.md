# Live Playwright MCP validation — Gas City Poker PoC

Run date: 2026-05-05
Validator: claude (driving the live browser via Playwright MCP)
Apps under test:
- `apps/server` (`pnpm --filter @gas-city/server start`) on `http://localhost:4000`
- `apps/web` (`pnpm --filter @gas-city/web dev`) on `http://localhost:3000`

This is a manual end-to-end validation against the running services, separate from the headless Playwright suite in `tests/journeys/`. The headless suite is asserting; this run is exploring.

## Verdict

| Path | Result |
|---|---|
| Lobby renders, "Open games" lists existing games | ✅ |
| Create-new-game flow (Alice) | ✅ |
| Join-existing flow (Bob, 2nd browser context) | ✅ |
| Hand auto-starts on 2nd seat filled | ✅ |
| Server-authoritative state synced across both clients | ✅ |
| Hole cards visible only to the owning seat | ✅ |
| Fold-resolves-hand journey (Alice folds → Bob wins pot) | ✅ |
| Chip conservation (199 + 201 = 400 = 200 + 200) | ✅ |
| Reconnect-survives-refresh (F5 on Bob's tab) | ✅ |
| Reconnect-survives-server-restart | ✅ (validates m2 atomicity in practice) |
| Join-when-game-is-full | ❌ silent no-op (BUG) |

## Findings

### BUG-V1 (MAJOR): Joining a full game silently leaves the client stuck on "Waiting for opponent…"

**Repro:** game `#18` is `in_progress` with 2/2 seats (Alice + Bob). Open a third browser context, type `Carol` + game id `18` + click Join.

**Observed:**
- The client navigates to `/game/18?name=Carol`.
- The connection pill shows `Connected`.
- The page renders the empty-state `Waiting for opponent…`, not Bob/Alice's table state.
- No `playerError` toast, no redirect back to the lobby, no "game full" indication.
- The server log records nothing for Carol's join attempt — it doesn't appear the server even processed a `joinGame` event for her, OR the server quietly emitted a snapshot Carol's client ignored.

**Why this matters:**
- The bead's stated contract for `joinGame` says "if the game is in 'open' status [create a new seat]". For non-`open` games it should reject with a `playerError` carrying code `GAME_FULL` or similar (see `apps/server/src/errors.ts`).
- The web client also doesn't pre-filter the lobby's "Join existing" path — there's no "this game is full" check before sending the join.

**Recommended fix:** server-side reject in `joinGame.ts` when `gameStatus !== "open"` AND no matching `sessionToken` for resume. Emit `playerError({ code: "GAME_FULL", message: "Game is full" })`. Web client surfaces it via the existing error toast.

### BUG-V2 (MINOR, cosmetic): Pot panel shows "2 side pots" for a heads-up preflop fold with no all-in

**Repro:** at any point in the heads-up game, the pot panel renders `2 side pots` directly under the pot total even when the only contributions are SB + BB and no all-in has occurred.

**Observed:** `apps/web/src/components/Pot.tsx` (or whichever renders the side-pot count) appears to count `state.pots.length` directly without filtering empty/identical pots. With 1 chip from SB and 2 chips from BB, the side-pot algorithm produces two pot entries (one of size 1 between both, one of size 1 covering only BB's call-overage). Both contribute to the same total, so showing "2 side pots" is technically true but misleading on a hand that hasn't seen an all-in.

**Why this matters:** confusing UX. Players will see "2 side pots" and assume someone went all-in.

**Recommended fix:** only render the side-pot count when `state.pots.length > 1 AND any pot has a different eligible-seat set`, OR display "Pot 3" without the "2 side pots" subtext on hands with no all-in.

### Observation: lobby's "Open games" hides resolved hands

After Alice folded and the hand resolved, game `#18` disappeared from the lobby's "Open games" list (a third browser context opening `/` no longer sees it). It's still reachable by typing `18` in the join input.

This may be intentional (`listOpenGames` filters by status, and maybe the server flips a finished-hand game to a non-open status), but the table page is still functional for the seated players. **It does mean a refreshing user can't find their game from the lobby.** Worth confirming intended behavior; if intentional, document; if accidental, fix.

## Validations that confirmed claimed fixes

| Fix bead | Validated by |
|---|---|
| B1 (sub-min all-in no reopen) | Not exercised in live run (would require all-in scenarios). Covered by `all-in-no-reopen.test.ts`. |
| M1 (web→shared boundary) | Live web app builds and runs without depending on `@gas-city/poker-core`. Verified `apps/web/package.json` and the rig's working tree before run. |
| M2 (snapshot size) | Live run produced normal snapshots; size implicitly bounded since `state.events` is no longer threaded through. |
| m2 (transaction wrap) | **Validated by server-restart reconnect**: killing the server mid-session, restarting, and seeing Bob's tab rehydrate with intact stacks (199/201), hole cards (9♣ 7♠), and event log proves snapshot+events are written atomically and survived the cold start. |
| m5 (sessionToken UNIQUE) | Not directly exercisable in browser (would need two seats with the same token). Schema migration applied at server boot without errors. |

## Screenshots

- `validation-carol-stuck.png` — Carol's stuck "Waiting for opponent…" after attempting to join a full game (BUG-V1).
- `validation-bob-reconnecting.png` — Bob's connection pill flipping to `Reconnecting…` after the server was killed.

## Console / network notes

- `GET /favicon.ico → 404` (cosmetic; would only show in browsers that auto-fetch `/favicon.ico`). Not blocking.
- One transient `WebSocket connection ... failed: WebSocket is closed before the connection is established` warning per tab on initial connect. Socket.IO falls back to long-polling and the app works. Looks like a Next dev-server proxy timing issue, not a server bug.

## Recommended next beads

1. **Fix BUG-V1** — server-side `GAME_FULL` rejection in `joinGame.ts` + web error-toast plumbing.
2. **Fix BUG-V2** — side-pot count rendering in `Pot.tsx`.
3. **Document or fix** the resolved-hands-disappear-from-lobby behavior.
