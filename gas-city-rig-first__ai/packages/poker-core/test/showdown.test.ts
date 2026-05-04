import { describe, expect, it } from "vitest";
import {
  compareHandValues,
  evaluateBest5,
  resolveHand,
} from "../src/index.js";
import type { Card, GameState, PlayerState, Pot } from "../src/index.js";

function c(rank: string, suit: string): Card {
  return { rank: rank as Card["rank"], suit: suit as Card["suit"] };
}

describe("hand evaluation", () => {
  it("recognises straight flush as best", () => {
    const sf = evaluateBest5([
      c("9", "h"),
      c("T", "h"),
      c("J", "h"),
      c("Q", "h"),
      c("K", "h"),
      c("2", "c"),
      c("3", "d"),
    ]);
    expect(sf.category).toBe("straight_flush");
  });

  it("recognises a flush", () => {
    const f = evaluateBest5([
      c("2", "h"),
      c("5", "h"),
      c("8", "h"),
      c("J", "h"),
      c("K", "h"),
      c("3", "c"),
      c("4", "d"),
    ]);
    expect(f.category).toBe("flush");
  });

  it("recognises wheel straight (A-2-3-4-5)", () => {
    const s = evaluateBest5([
      c("A", "s"),
      c("2", "d"),
      c("3", "h"),
      c("4", "c"),
      c("5", "s"),
      c("K", "d"),
      c("Q", "h"),
    ]);
    expect(s.category).toBe("straight");
    expect(s.ranks[0]).toBe(5);
  });

  it("higher pair beats lower pair", () => {
    const aa = evaluateBest5([
      c("A", "s"),
      c("A", "h"),
      c("3", "d"),
      c("7", "c"),
      c("9", "s"),
      c("2", "d"),
      c("4", "h"),
    ]);
    const kk = evaluateBest5([
      c("K", "s"),
      c("K", "h"),
      c("3", "d"),
      c("7", "c"),
      c("9", "s"),
      c("2", "d"),
      c("4", "h"),
    ]);
    expect(compareHandValues(aa, kk)).toBeGreaterThan(0);
  });

  it("pair beats high card", () => {
    const pair = evaluateBest5([
      c("2", "s"),
      c("2", "h"),
      c("5", "d"),
      c("9", "c"),
      c("J", "s"),
      c("K", "d"),
      c("3", "h"),
    ]);
    const high = evaluateBest5([
      c("A", "s"),
      c("K", "h"),
      c("5", "d"),
      c("9", "c"),
      c("J", "s"),
      c("3", "d"),
      c("4", "h"),
    ]);
    expect(compareHandValues(pair, high)).toBeGreaterThan(0);
  });
});

describe("resolveHand", () => {
  it("awards a single pot to the better hand", () => {
    const state = makeShowdown({
      community: [c("2", "c"), c("7", "d"), c("J", "s"), c("3", "h"), c("4", "c")],
      players: [
        // P0: AA
        { seat: 0, stack: 0, hole: [c("A", "s"), c("A", "h")], total: 50 },
        // P1: KK
        { seat: 1, stack: 0, hole: [c("K", "s"), c("K", "h")], total: 50 },
      ],
      pots: [{ amount: 100, eligibleSeats: [0, 1] }],
    });
    const r = resolveHand(state);
    const p0 = r.state.players.find((p) => p.seat === 0);
    const p1 = r.state.players.find((p) => p.seat === 1);
    expect(p0?.stack).toBe(100);
    expect(p1?.stack).toBe(0);
  });

  it("chops a tied pot, with remainder going to lower seat", () => {
    const state = makeShowdown({
      community: [c("A", "c"), c("A", "d"), c("K", "s"), c("K", "h"), c("Q", "c")],
      players: [
        { seat: 0, stack: 0, hole: [c("2", "s"), c("3", "h")], total: 5 },
        { seat: 1, stack: 0, hole: [c("4", "s"), c("5", "h")], total: 5 },
      ],
      // both play AAKKQ — odd pot of 11 — one gets 6, other 5
      pots: [{ amount: 11, eligibleSeats: [0, 1] }],
    });
    const r = resolveHand(state);
    const p0 = r.state.players.find((p) => p.seat === 0);
    const p1 = r.state.players.find((p) => p.seat === 1);
    expect((p0?.stack ?? 0) + (p1?.stack ?? 0)).toBe(11);
    // Lower seat gets the extra chip
    expect(p0?.stack).toBe(6);
    expect(p1?.stack).toBe(5);
  });

  it("side pot is paid only to eligible players", () => {
    const state = makeShowdown({
      community: [c("2", "c"), c("7", "d"), c("J", "h"), c("Q", "s"), c("3", "c")],
      players: [
        // P0 went all-in for 10 with the weakest hand (high card)
        { seat: 0, stack: 0, hole: [c("5", "s"), c("6", "h")], total: 10 },
        // P1 has the best hand (pair of aces)
        { seat: 1, stack: 0, hole: [c("A", "s"), c("A", "h")], total: 30 },
        // P2 second-best (pair of kings)
        { seat: 2, stack: 0, hole: [c("K", "s"), c("K", "h")], total: 30 },
      ],
      pots: [
        { amount: 30, eligibleSeats: [0, 1, 2] }, // main pot
        { amount: 40, eligibleSeats: [1, 2] }, // side pot
      ],
    });
    const r = resolveHand(state);
    const p0 = r.state.players.find((p) => p.seat === 0);
    const p1 = r.state.players.find((p) => p.seat === 1);
    const p2 = r.state.players.find((p) => p.seat === 2);
    // P1 (AA) wins both pots (30 + 40 = 70)
    expect(p1?.stack).toBe(70);
    expect(p2?.stack).toBe(0);
    expect(p0?.stack).toBe(0);
  });

  it("eligible-only side pot pays the best eligible hand even if the all-in had a stronger hand on the main pot", () => {
    const state = makeShowdown({
      community: [c("5", "c"), c("7", "d"), c("J", "h"), c("Q", "s"), c("3", "c")],
      players: [
        // P0 all-in for 10 with the BEST hand (pair of aces)
        { seat: 0, stack: 0, hole: [c("A", "s"), c("A", "h")], total: 10 },
        // P1 mid (pair of kings)
        { seat: 1, stack: 0, hole: [c("K", "s"), c("K", "h")], total: 30 },
        // P2 weak (pair of fours)
        { seat: 2, stack: 0, hole: [c("4", "s"), c("4", "h")], total: 30 },
      ],
      pots: [
        { amount: 30, eligibleSeats: [0, 1, 2] }, // main pot
        { amount: 40, eligibleSeats: [1, 2] }, // side pot
      ],
    });
    const r = resolveHand(state);
    const p0 = r.state.players.find((p) => p.seat === 0);
    const p1 = r.state.players.find((p) => p.seat === 1);
    const p2 = r.state.players.find((p) => p.seat === 2);
    expect(p0?.stack).toBe(30); // wins main pot
    expect(p1?.stack).toBe(40); // wins side pot
    expect(p2?.stack).toBe(0);
  });
});

function makeShowdown(opts: {
  community: ReadonlyArray<Card>;
  players: ReadonlyArray<{ seat: number; stack: number; hole: ReadonlyArray<Card>; total: number }>;
  pots: ReadonlyArray<Pot>;
}): GameState {
  const players: PlayerState[] = opts.players.map((p) => ({
    seat: p.seat,
    stack: p.stack,
    holeCards: p.hole,
    status: "active",
    committedThisStreet: 0,
    committedTotal: p.total,
    hasActedThisStreet: true,
  }));
  return {
    config: {
      blinds: { sb: 1, bb: 2 },
      startingStacks: 100,
      numSeats: players.length,
      buttonSeat: 0,
      seed: 0,
    },
    handId: 1,
    street: "river",
    deck: [],
    community: opts.community,
    players,
    pots: opts.pots,
    currentSeat: null,
    currentBet: 0,
    lastRaiseSize: 0,
    buttonSeat: 0,
    events: [],
  };
}
