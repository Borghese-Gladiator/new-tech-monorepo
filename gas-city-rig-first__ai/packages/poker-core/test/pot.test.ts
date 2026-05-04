import { describe, expect, it } from "vitest";
import { buildPots } from "../src/index.js";
import type { PlayerState } from "../src/index.js";

function p(seat: number, total: number, status: PlayerState["status"]): PlayerState {
  return {
    seat,
    stack: 0,
    holeCards: [],
    status,
    committedThisStreet: 0,
    committedTotal: total,
    hasActedThisStreet: true,
    actionReopened: false,
  };
}

describe("pots", () => {
  it("single pot when no all-ins of differing sizes", () => {
    const pots = buildPots([p(0, 10, "active"), p(1, 10, "active"), p(2, 10, "active")]);
    expect(pots.length).toBe(1);
    expect(pots[0]?.amount).toBe(30);
    expect(pots[0]?.eligibleSeats).toEqual([0, 1, 2]);
  });

  it("side pot when one player short-stacked", () => {
    // P0 went all-in for 10; P1, P2 each committed 30
    const pots = buildPots([
      p(0, 10, "all_in"),
      p(1, 30, "active"),
      p(2, 30, "active"),
    ]);
    expect(pots.length).toBe(2);
    // Main pot: 10 * 3 = 30, eligible 0,1,2
    expect(pots[0]?.amount).toBe(30);
    expect(pots[0]?.eligibleSeats).toEqual([0, 1, 2]);
    // Side pot: (30 - 10) * 2 = 40, eligible 1,2
    expect(pots[1]?.amount).toBe(40);
    expect(pots[1]?.eligibleSeats).toEqual([1, 2]);
  });

  it("two side pots when two all-ins of different sizes", () => {
    // P0 all-in 5, P1 all-in 20, P2 active 50
    const pots = buildPots([
      p(0, 5, "all_in"),
      p(1, 20, "all_in"),
      p(2, 50, "active"),
    ]);
    expect(pots.length).toBe(3);
    // tier 5: slice 5, contributors 3 → 15, eligible 0,1,2
    expect(pots[0]?.amount).toBe(15);
    expect(pots[0]?.eligibleSeats).toEqual([0, 1, 2]);
    // tier 20: slice 15, contributors 2 → 30, eligible 1,2
    expect(pots[1]?.amount).toBe(30);
    expect(pots[1]?.eligibleSeats).toEqual([1, 2]);
    // tier 50: slice 30, contributors 1 → 30, eligible 2
    expect(pots[2]?.amount).toBe(30);
    expect(pots[2]?.eligibleSeats).toEqual([2]);
  });

  it("folded player contributions go to pot but they aren't eligible", () => {
    const pots = buildPots([
      p(0, 10, "folded"),
      p(1, 10, "active"),
      p(2, 10, "active"),
    ]);
    expect(pots.length).toBe(1);
    expect(pots[0]?.amount).toBe(30);
    expect(pots[0]?.eligibleSeats).toEqual([1, 2]);
  });
});
