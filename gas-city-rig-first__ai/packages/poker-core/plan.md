# packages/poker-core — plan

## Brief
Implement a pure TypeScript Texas Hold'em rules engine as a workspace package. Pure library — no socket / db / fs imports. Strict TS (noUncheckedIndexedAccess, exactOptionalPropertyTypes). Vitest unit tests, all deterministic.

## Changes

```
packages/poker-core/
  package.json          # name, scripts (typecheck, lint, test), devDeps (typescript, vitest, tsd-style)
  tsconfig.json         # extends ../../tsconfig.base.json, rootDir src, outDir dist
  vitest.config.ts      # node env, deterministic
  src/
    index.ts            # barrel — re-exports everything public
    types.ts            # Suit, Rank, Card, Deck, Seat, PlayerState, Street, Action, ActionResult, Pot, GameEvent, GameState
    rng.ts              # mulberry32 seeded RNG
    deck.ts             # buildDeck(), shuffle(deck, rng)
    deal.ts             # dealHoleCards, dealFlop/Turn/River
    legal.ts            # legalActions(state, seatIdx)
    betting.ts          # applyAction(state, action) → ActionResult; isBettingRoundClosed; advanceCurrent
    street.ts           # advanceStreet(state) — only when round closed
    showdown.ts         # evaluateHand7(cards), determineWinners, distributePots (incl. side pots)
    pot.ts              # buildPotsFromContributions (handles all-in side pots)
  test/
    deck.test.ts        # 52 unique cards
    rng.test.ts         # determinism
    deal.test.ts        # hole cards, board cards
    turn-order.test.ts  # button → SB → BB → ... cycle
    legal.test.ts       # cannot check vs bet, min raise, etc.
    betting.test.ts     # fold/check/call/raise advance
    pot.test.ts         # side pots when all-ins
    street.test.ts      # only advance when closed
    showdown.test.ts    # winner determination + distribution
```

## Tests

### Unit (vitest, all deterministic — seeded)
- deck: 52 cards, all distinct, build is stable
- rng: same seed → same sequence
- deal: hole cards correct count per player; flop=3, turn=1, river=1; community drawn from same deck
- turn order: button → SB → BB → ... wraps; folded/all-in seats skipped
- legal action:
  - facing no bet: check + bet (raise) legal; call illegal
  - facing a bet: call + raise legal; check illegal; raise must be ≥ minRaise
  - all-in for less than min raise does not reopen action
- betting: fold removes player from contention; call adds chips; raise sets new currentBet
- pot: single pot when no all-ins; main + side(s) when one or more all-ins of differing sizes
- street: cannot advance if round not closed; advances clears currentBet
- showdown: high card → straight flush ranking; chops split correctly; side pots paid by participants only

### Manual
N/A — pure library, no UI.

## Acceptance
- `pnpm install` (root, regenerates lockfile)
- `pnpm --filter ./packages/poker-core typecheck` clean
- `pnpm --filter ./packages/poker-core test` green
