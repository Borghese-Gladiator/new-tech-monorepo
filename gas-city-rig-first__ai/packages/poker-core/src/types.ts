export type Suit = "c" | "d" | "h" | "s";
export type Rank =
  | "2"
  | "3"
  | "4"
  | "5"
  | "6"
  | "7"
  | "8"
  | "9"
  | "T"
  | "J"
  | "Q"
  | "K"
  | "A";

export type Card = { rank: Rank; suit: Suit };
export type Deck = ReadonlyArray<Card>;

export type Street = "preflop" | "flop" | "turn" | "river" | "showdown";

export type SeatStatus = "active" | "folded" | "all_in";

export type Seat = number;

export type PlayerState = {
  seat: Seat;
  stack: number;
  holeCards: ReadonlyArray<Card>;
  status: SeatStatus;
  committedThisStreet: number;
  committedTotal: number;
  hasActedThisStreet: boolean;
  // True iff this seat is allowed to raise on its next turn this street.
  // A sub-minimum all-in does not reopen action for seats that already acted,
  // so those seats keep actionReopened=false until a full raise comes in.
  actionReopened: boolean;
};

export type ActionKind = "fold" | "check" | "call" | "raise";

export type Action =
  | { kind: "fold" }
  | { kind: "check" }
  | { kind: "call" }
  | { kind: "raise"; amount: number };

export type ActionResult = {
  ok: true;
  state: GameState;
  events: ReadonlyArray<GameEvent>;
} | {
  ok: false;
  reason: string;
};

export type Pot = {
  amount: number;
  eligibleSeats: ReadonlyArray<Seat>;
};

export type GameEvent =
  | { type: "hand-started"; handId: number; buttonSeat: Seat }
  | { type: "cards-dealt"; street: Street; community: ReadonlyArray<Card> }
  | { type: "hole-cards-dealt"; seat: Seat; cards: ReadonlyArray<Card> }
  | { type: "blinds-posted"; sb: { seat: Seat; amount: number }; bb: { seat: Seat; amount: number } }
  | { type: "action-taken"; seat: Seat; action: Action; amount: number }
  | { type: "street-advanced"; from: Street; to: Street }
  | { type: "pot-updated"; pots: ReadonlyArray<Pot> }
  | { type: "hand-resolved"; winners: ReadonlyArray<{ seat: Seat; amount: number; potIndex: number }> };

export type Blinds = { sb: number; bb: number };

export type GameConfig = {
  blinds: Blinds;
  startingStacks: number;
  numSeats: number;
  buttonSeat: Seat;
  seed: number;
};

export type GameState = {
  config: GameConfig;
  handId: number;
  street: Street;
  deck: Deck;
  community: ReadonlyArray<Card>;
  players: ReadonlyArray<PlayerState>;
  pots: ReadonlyArray<Pot>;
  currentSeat: Seat | null;
  currentBet: number;
  lastRaiseSize: number;
  buttonSeat: Seat;
};
