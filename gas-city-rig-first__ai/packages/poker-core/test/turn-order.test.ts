import { describe, expect, it } from "vitest";
import {
  bigBlindSeat,
  firstToActPostflop,
  firstToActPreflop,
  smallBlindSeat,
  startHand,
} from "../src/index.js";

const cfg6 = {
  blinds: { sb: 1, bb: 2 },
  startingStacks: 200,
  numSeats: 6,
  buttonSeat: 0,
  seed: 1,
};

describe("turn order", () => {
  it("button → SB → BB → ... cycle (6 seats)", () => {
    const { state } = startHand({ config: cfg6 });
    expect(smallBlindSeat(state.players, 0)).toBe(1);
    expect(bigBlindSeat(state.players, 0)).toBe(2);
    // First to act preflop is UTG (seat 3)
    expect(firstToActPreflop(state.players, 0)).toBe(3);
    expect(state.currentSeat).toBe(3);
  });

  it("first to act postflop is first non-folded seat after button", () => {
    const { state } = startHand({ config: cfg6 });
    expect(firstToActPostflop(state.players, 0)).toBe(1);
  });

  it("heads-up: button is SB, opponent is BB, button acts first preflop", () => {
    const cfg = { ...cfg6, numSeats: 2, buttonSeat: 0 };
    const { state } = startHand({ config: cfg });
    expect(smallBlindSeat(state.players, 0)).toBe(0);
    expect(bigBlindSeat(state.players, 0)).toBe(1);
    expect(firstToActPreflop(state.players, 0)).toBe(0);
  });
});
