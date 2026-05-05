import type {
  Card,
  GameEvent,
  GameState,
  Seat,
} from "@gas-city/shared";

export type ConnState = "connected" | "reconnecting" | "disconnected";

export type EventLogEntry = {
  id: number;
  event: GameEvent;
  receivedAt: number;
};

export type TableState = {
  state: GameState | null;
  you: { seatIndex: Seat; holeCards: [Card, Card] } | null;
  events: ReadonlyArray<EventLogEntry>;
  connection: ConnState;
  error: string | null;
  flashSeats: ReadonlyArray<Seat>;
  sessionToken: string | null;
};

export const initialTableState: TableState = {
  state: null,
  you: null,
  events: [],
  connection: "disconnected",
  error: null,
  flashSeats: [],
  sessionToken: null,
};

export type TableAction =
  | {
      type: "snapshot";
      state: GameState;
      you?: { seatIndex: Seat; holeCards: [Card, Card] };
    }
  | { type: "event"; event: GameEvent }
  | { type: "connection"; state: ConnState }
  | { type: "session-token"; token: string }
  | { type: "error"; message: string }
  | { type: "clear-error" }
  | { type: "clear-flash" };

let eventIdCounter = 0;

function flashSeatsForEvent(event: GameEvent): ReadonlyArray<Seat> {
  switch (event.type) {
    case "action-taken":
      return [event.seat];
    case "blinds-posted":
      return [event.sb.seat, event.bb.seat];
    case "hand-resolved":
      return event.winners.map((w) => w.seat);
    default:
      return [];
  }
}

export function tableReducer(
  state: TableState,
  action: TableAction,
): TableState {
  switch (action.type) {
    case "snapshot": {
      // Per-seat snapshot includes `you`; public snapshot does not. Don't
      // overwrite `you` when only the public snapshot arrives.
      const next: TableState = {
        ...state,
        state: action.state,
      };
      if (action.you) {
        next.you = action.you;
      }
      return next;
    }
    case "event": {
      eventIdCounter += 1;
      const entry: EventLogEntry = {
        id: eventIdCounter,
        event: action.event,
        receivedAt: Date.now(),
      };
      const trimmed = [...state.events, entry].slice(-50);
      return {
        ...state,
        events: trimmed,
        flashSeats: flashSeatsForEvent(action.event),
      };
    }
    case "connection":
      return { ...state, connection: action.state };
    case "session-token":
      return { ...state, sessionToken: action.token };
    case "error":
      return { ...state, error: action.message };
    case "clear-error":
      return { ...state, error: null };
    case "clear-flash":
      return { ...state, flashSeats: [] };
    default:
      return state;
  }
}
