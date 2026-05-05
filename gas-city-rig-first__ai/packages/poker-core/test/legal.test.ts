import { describe, expect, it } from "vitest";
import { advanceStreet, applyAction, legalActions, startHand } from "../src/index.js";

const cfg = {
  blinds: { sb: 1, bb: 2 },
  startingStacks: 200,
  numSeats: 3,
  buttonSeat: 0,
  seed: 7,
};

describe("legal actions", () => {
  it("UTG facing the BB cannot check, must call/raise/fold", () => {
    const { state } = startHand({ config: cfg });
    const opts = legalActions(state, state.currentSeat ?? -1);
    expect(opts.canCheck).toBe(false);
    expect(opts.canCall).toBe(true);
    expect(opts.canFold).toBe(true);
    expect(opts.canRaise).toBe(true);
  });

  it("min raise after BB equals 2*BB total committed-to (raise-to)", () => {
    const { state } = startHand({ config: cfg });
    const opts = legalActions(state, state.currentSeat ?? -1);
    // BB is 2; min raise increment is BB; so min raise-to = 4
    expect(opts.minRaiseTo).toBe(4);
  });

  it("rejects raise below min-raise (and not all-in)", () => {
    const { state } = startHand({ config: cfg });
    const r = applyAction(state, { kind: "raise", amount: 3 });
    expect(r.ok).toBe(false);
  });

  it("accepts a min raise to 4", () => {
    const { state } = startHand({ config: cfg });
    const r = applyAction(state, { kind: "raise", amount: 4 });
    expect(r.ok).toBe(true);
  });

  it("after a raise, next actor cannot check (facing a bet)", () => {
    const { state } = startHand({ config: cfg });
    const r1 = applyAction(state, { kind: "raise", amount: 6 });
    if (!r1.ok) throw new Error(r1.reason);
    const opts = legalActions(r1.state, r1.state.currentSeat ?? -1);
    expect(opts.canCheck).toBe(false);
    expect(opts.canCall).toBe(true);
    expect(opts.canRaise).toBe(true);
  });

  it("postflop with no bet: can check, cannot call, can bet (raise from 0)", () => {
    let { state } = startHand({ config: cfg });
    // Everyone calls/checks to the flop.
    while (state.currentSeat !== null) {
      const seat = state.currentSeat;
      const p = state.players.find((pp) => pp.seat === seat);
      if (!p) break;
      const toCall = state.currentBet - p.committedThisStreet;
      const r = applyAction(state, toCall > 0 ? { kind: "call" } : { kind: "check" });
      if (!r.ok) throw new Error(r.reason);
      state = r.state;
    }
    const adv = advanceStreet(state);
    if (!adv.ok) throw new Error(adv.reason);
    state = adv.state;
    const opts = legalActions(state, state.currentSeat ?? -1);
    expect(opts.canCheck).toBe(true);
    expect(opts.canCall).toBe(false);
    expect(opts.canRaise).toBe(true);
  });
});
