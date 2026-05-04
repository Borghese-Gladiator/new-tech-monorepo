import { describe, expect, it } from "vitest";
import { buildDeck, cardId, mulberry32, shuffle } from "../src/index.js";

describe("deck", () => {
  it("builds 52 cards", () => {
    const deck = buildDeck();
    expect(deck.length).toBe(52);
  });

  it("contains 52 unique cards", () => {
    const deck = buildDeck();
    const ids = new Set(deck.map((c) => cardId(c)));
    expect(ids.size).toBe(52);
  });

  it("shuffle preserves all cards", () => {
    const deck = buildDeck();
    const shuffled = shuffle(deck, mulberry32(1));
    const ids = new Set(shuffled.map((c) => cardId(c)));
    expect(shuffled.length).toBe(52);
    expect(ids.size).toBe(52);
  });

  it("shuffle is deterministic given the same seed", () => {
    const deck = buildDeck();
    const a = shuffle(deck, mulberry32(42));
    const b = shuffle(deck, mulberry32(42));
    expect(a.map(cardId)).toEqual(b.map(cardId));
  });

  it("shuffle differs for different seeds", () => {
    const deck = buildDeck();
    const a = shuffle(deck, mulberry32(1));
    const b = shuffle(deck, mulberry32(2));
    expect(a.map(cardId)).not.toEqual(b.map(cardId));
  });
});
