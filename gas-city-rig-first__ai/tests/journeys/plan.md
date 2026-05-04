# tests/journeys — plan

## Brief

Playwright smoke browser journeys for the multiplayer poker PoC. Lives at
`tests/journeys/` at the rig root with its own `package.json` so the
Playwright tooling is isolated from the apps that share React/Next deps.

## Changes

```
tests/journeys/
  package.json         # @gas-city/journeys, devDeps: @playwright/test
  playwright.config.ts # webServer boots apps/server (4000) + apps/web (3000)
  tsconfig.json        # extends rig base, includes spec files
  create-and-join.spec.ts
  fold-resolves-hand.spec.ts
  reconnect-survives-refresh.spec.ts
```

Root `package.json` adds `test:e2e` and `test:e2e:install` scripts
that delegate into the `@gas-city/journeys` workspace package.

## Key behaviors

- **webServer boot order**: server first (no env), then web (with
  `NEXT_PUBLIC_SERVER_URL=http://localhost:4000`). Both must be reachable
  before any test runs.
- **Two browser contexts**: each spec creates two `browser.newContext()`
  pairs so two players don't share cookies/localStorage.
- **Timing tolerance**: rely on Playwright auto-waiting for selectors
  (e.g. `getByRole`/`locator(...)`) rather than fixed sleeps where possible.
- **Reconnect test**: snapshot stack/cards via `data-seat`/`aria-label`
  selectors before reload; assert via the `role="status"` connection pill
  and unchanged stack text.

## Tests

### Unit
N/A — these journeys are themselves the tests.

### Manual
- `pnpm test:e2e:install` (downloads chromium binary)
- `pnpm test:e2e` from rig root → all 3 specs pass
- Visit `http://localhost:3000` after running `pnpm --filter @gas-city/server dev`
  + `pnpm --filter @gas-city/web dev` to spot-check the same flow manually.

## Acceptance

- `pnpm test:e2e:install`
- `pnpm test:e2e` (all 3 specs pass; flakes retried 2x; `.skip` only as a
  documented last resort)
