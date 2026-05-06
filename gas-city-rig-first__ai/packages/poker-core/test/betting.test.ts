import { describe, expect, it } from "vitest";
import { applyAction, isBettingRoundClosed, isHandOver, startHand } from "../src/index.js";

const cfg = {
  blinds: { sb: 1, bb: 2 },
  startingStacks: 200,
  numSeats: 3,
  buttonSeat: 0,
  seed: 11,
};

describe("betting", () => {
  it("fold: player removed from contention; hand ends if only one left", () => {
    let { state } = startHand({ config: cfg });
    // UTG (seat 2) folds, button (seat 0) folds, SB (seat 1) wins uncontested.
    let r = applyAction(state, { kind: "fold" });
    expect(r.ok).toBe(true);
    if (!r.ok) return;
    state = r.state;
    r = applyAction(state, { kind: "fold" });
    expect(r.ok).toBe(true);
    if (!r.ok) return;
    state = r.state;
    expect(isHandOver(state)).toBe(true);
  });

  it("call: chips moved from stack to committed", () => {
    const { state } = startHand({ config: cfg });
    const utg = state.players.find((p) => p.seat === state.currentSeat);
    if (!utg) throw new Error("no utg");
    const r = applyAction(state, { kind: "call" });
    expect(r.ok).toBe(true);
    if (!r.ok) return;
    const after = r.state.players.find((p) => p.seat === utg.seat);
    if (!after) throw new Error("no after");
    expect(after.stack).toBe(utg.stack - 2);
    expect(after.committedThisStreet).toBe(2);
  });

  it("raise: sets currentBet and lastRaiseSize; reopens action for others", () => {
    const { state } = startHand({ config: cfg });
    const r = applyAction(state, { kind: "raise", amount: 6 });
    expect(r.ok).toBe(true);
    if (!r.ok) return;
    expect(r.state.currentBet).toBe(6);
    expect(r.state.lastRaiseSize).toBe(4);
    // SB and BB must still act
    const sb = r.state.players.find((p) => p.seat === 1);
    const bb = r.state.players.find((p) => p.seat === 2);
    if (!sb || !bb) throw new Error("missing");
    expect(sb.hasActedThisStreet).toBe(false);
    expect(bb.hasActedThisStreet).toBe(false);
  });

  it("betting round closes when all active players matched and acted", () => {
    // 3 seats: button=0, SB=1, BB=2. Preflop order: 0 → 1 → 2.
    // Seat 0 calls, seat 1 calls, seat 2 (BB) checks option → round closed.
    let { state } = startHand({ config: cfg });
    let r = applyAction(state, { kind: "call" });
    if (!r.ok) throw new Error(r.reason);
    state = r.state;
    r = applyAction(state, { kind: "call" });
    if (!r.ok) throw new Error(r.reason);
    state = r.state;
    r = applyAction(state, { kind: "check" });
    if (!r.ok) throw new Error(r.reason);
    state = r.state;
    expect(state.currentSeat).toBe(null);
    expect(isBettingRoundClosed(state)).toBe(true);
  });
});
