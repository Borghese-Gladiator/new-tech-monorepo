import { describe, expect, it } from "vitest";
import { cardId, startHand, advanceStreet, applyAction } from "../src/index.js";

const cfg = {
  blinds: { sb: 1, bb: 2 },
  startingStacks: 200,
  numSeats: 3,
  buttonSeat: 0,
  seed: 99,
};

describe("deal", () => {
  it("deals 2 hole cards to each player", () => {
    const state = startHand({ config: cfg });
    for (const p of state.players) {
      expect(p.holeCards.length).toBe(2);
    }
  });

  it("draws community cards from the same deck (no duplicates with hole cards)", () => {
    let state = startHand({ config: cfg });
    // everyone calls / checks through to the river
    while (state.street !== "river" || !canAdvance(state)) {
      if (state.currentSeat === null) {
        const r = advanceStreet(state);
        if (!r.ok) break;
        state = r.state;
        continue;
      }
      // Have everyone just call/check. SB needs to call, then everyone checks.
      const seat = state.currentSeat;
      const player = state.players.find((p) => p.seat === seat);
      if (!player) break;
      const toCall = state.currentBet - player.committedThisStreet;
      const action = toCall > 0 ? ({ kind: "call" as const }) : ({ kind: "check" as const });
      const r = applyAction(state, action);
      if (!r.ok) throw new Error(r.reason);
      state = r.state;
      if (state.currentSeat === null) {
        const adv = advanceStreet(state);
        if (!adv.ok) break;
        state = adv.state;
      }
    }
    // collect all dealt cards and check uniqueness
    const all: string[] = [];
    for (const p of state.players) for (const c of p.holeCards) all.push(cardId(c));
    for (const c of state.community) all.push(cardId(c));
    expect(new Set(all).size).toBe(all.length);
  });

  it("flop has 3 cards, turn 1, river 1", () => {
    let state = startHand({ config: cfg });
    state = drainBettingRound(state);
    let adv = advanceStreet(state);
    expect(adv.ok).toBe(true);
    if (!adv.ok) return;
    state = adv.state;
    expect(state.community.length).toBe(3);
    state = drainBettingRound(state);
    adv = advanceStreet(state);
    if (!adv.ok) throw new Error(adv.reason);
    state = adv.state;
    expect(state.community.length).toBe(4);
    state = drainBettingRound(state);
    adv = advanceStreet(state);
    if (!adv.ok) throw new Error(adv.reason);
    state = adv.state;
    expect(state.community.length).toBe(5);
  });
});

function canAdvance(state: ReturnType<typeof startHand>): boolean {
  return state.currentSeat === null;
}

function drainBettingRound(state: ReturnType<typeof startHand>): ReturnType<typeof startHand> {
  let s = state;
  while (s.currentSeat !== null) {
    const seat = s.currentSeat;
    const player = s.players.find((p) => p.seat === seat);
    if (!player) break;
    const toCall = s.currentBet - player.committedThisStreet;
    const action = toCall > 0 ? ({ kind: "call" as const }) : ({ kind: "check" as const });
    const r = applyAction(s, action);
    if (!r.ok) throw new Error(r.reason);
    s = r.state;
  }
  return s;
}
