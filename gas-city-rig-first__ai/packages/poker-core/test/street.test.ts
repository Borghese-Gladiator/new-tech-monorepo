import { describe, expect, it } from "vitest";
import { advanceStreet, applyAction, startHand, type GameState } from "../src/index.js";

const cfg = {
  blinds: { sb: 1, bb: 2 },
  startingStacks: 200,
  numSeats: 3,
  buttonSeat: 0,
  seed: 5,
};

describe("street advance", () => {
  it("refuses to advance while betting round still open", () => {
    const { state } = startHand({ config: cfg });
    const r = advanceStreet(state);
    expect(r.ok).toBe(false);
  });

  it("advances after round closes; resets street betting", () => {
    let { state } = startHand({ config: cfg });
    while (state.currentSeat !== null) {
      const seat = state.currentSeat;
      const p = state.players.find((pp) => pp.seat === seat);
      if (!p) break;
      const toCall = state.currentBet - p.committedThisStreet;
      const r = applyAction(state, toCall > 0 ? { kind: "call" } : { kind: "check" });
      if (!r.ok) throw new Error(r.reason);
      state = r.state;
    }
    const r = advanceStreet(state);
    expect(r.ok).toBe(true);
    if (!r.ok) return;
    expect(r.state.street).toBe("flop");
    expect(r.state.currentBet).toBe(0);
    for (const p of r.state.players) {
      expect(p.committedThisStreet).toBe(0);
      expect(p.hasActedThisStreet).toBe(false);
    }
  });

  it("advances flop → turn → river → showdown", () => {
    let { state } = startHand({ config: cfg });
    state = drain(state);
    let adv = advanceStreet(state);
    if (!adv.ok) throw new Error(adv.reason);
    state = adv.state;
    expect(state.street).toBe("flop");
    state = drain(state);
    adv = advanceStreet(state);
    if (!adv.ok) throw new Error(adv.reason);
    state = adv.state;
    expect(state.street).toBe("turn");
    state = drain(state);
    adv = advanceStreet(state);
    if (!adv.ok) throw new Error(adv.reason);
    state = adv.state;
    expect(state.street).toBe("river");
    state = drain(state);
    adv = advanceStreet(state);
    if (!adv.ok) throw new Error(adv.reason);
    state = adv.state;
    expect(state.street).toBe("showdown");
  });
});

function drain(state: GameState): GameState {
  let s = state;
  while (s.currentSeat !== null) {
    const seat = s.currentSeat;
    const p = s.players.find((pp) => pp.seat === seat);
    if (!p) break;
    const toCall = s.currentBet - p.committedThisStreet;
    const r = applyAction(s, toCall > 0 ? { kind: "call" } : { kind: "check" });
    if (!r.ok) throw new Error(r.reason);
    s = r.state;
  }
  return s;
}
