import { describe, expect, it } from "vitest";
import { applyAction, legalActions, startHand } from "../src/index.js";

const baseCfg = {
  blinds: { sb: 1, bb: 2 },
  startingStacks: 200,
  numSeats: 3,
  buttonSeat: 0,
  seed: 7,
};

// Sub-min all-in does NOT reopen action for seats that already acted.
// Seats: button=0 → SB=1, BB=2. UTG (first to act preflop with 3 players) is seat 0.
describe("sub-min all-in does not reopen action", () => {
  it("BTN may only call or fold after SB call + sub-min BB shove", () => {
    let state = startHand({
      config: baseCfg,
      players: [
        { seat: 0, stack: 200 }, // BTN / UTG preflop
        { seat: 1, stack: 200 }, // SB
        { seat: 2, stack: 9 }, // BB — only 7 left after posting 2
      ],
    });
    expect(state.currentSeat).toBe(0);

    // BTN raises to 6 (full min raise: increment 4 over BB of 2).
    let r = applyAction(state, { kind: "raise", amount: 6 });
    if (!r.ok) throw new Error(r.reason);
    state = r.state;
    expect(state.currentBet).toBe(6);
    expect(state.lastRaiseSize).toBe(4);
    expect(state.currentSeat).toBe(1);

    // SB calls 6.
    r = applyAction(state, { kind: "call" });
    if (!r.ok) throw new Error(r.reason);
    state = r.state;
    expect(state.currentSeat).toBe(2);

    // BB shoves all-in to 9. Increment = 3 < 4, so this is a sub-minimum all-in.
    r = applyAction(state, { kind: "raise", amount: 9 });
    if (!r.ok) throw new Error(r.reason);
    state = r.state;
    expect(state.currentBet).toBe(9);
    // lastRaiseSize must NOT advance — stays at the previous full-raise size.
    expect(state.lastRaiseSize).toBe(4);

    // Engine pulls BTN back via the partial-call shortfall path.
    expect(state.currentSeat).toBe(0);

    const opts = legalActions(state, 0);
    expect(opts.canRaise).toBe(false);
    expect(opts.canCall).toBe(true);
    expect(opts.canFold).toBe(true);
    expect(opts.callAmount).toBe(3);
  });

  it("full all-in DOES reopen action for prior actors", () => {
    let state = startHand({
      config: baseCfg,
      players: [
        { seat: 0, stack: 200 },
        { seat: 1, stack: 200 },
        { seat: 2, stack: 20 }, // BB — 18 left after posting; shove of 20 is a full raise
      ],
    });

    // BTN raises to 6 (increment 4).
    let r = applyAction(state, { kind: "raise", amount: 6 });
    if (!r.ok) throw new Error(r.reason);
    state = r.state;

    // SB calls 6.
    r = applyAction(state, { kind: "call" });
    if (!r.ok) throw new Error(r.reason);
    state = r.state;

    // BB shoves all-in to 20. Increment = 14 >= 4, this IS a full raise.
    r = applyAction(state, { kind: "raise", amount: 20 });
    if (!r.ok) throw new Error(r.reason);
    state = r.state;
    expect(state.currentBet).toBe(20);
    expect(state.lastRaiseSize).toBe(14);

    // Action is reopened — BTN is asked to act again because the raise was full.
    expect(state.currentSeat).toBe(0);

    const opts = legalActions(state, 0);
    expect(opts.canRaise).toBe(true);
    expect(opts.canCall).toBe(true);
    expect(opts.canFold).toBe(true);
  });
});
