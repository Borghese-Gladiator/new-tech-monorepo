import type { Card, GameEvent, GameState } from "@gas-city/poker-core";

export type AckResult =
  | { ok: true }
  | { ok: false; error: { code: string; message: string } };

export type JoinGamePayload = {
  gameId: string;
  displayName: string;
  sessionToken?: string;
};

export type LeaveGamePayload = {
  gameId: string;
};

export type PlayerActionPayload = {
  gameId: string;
  action:
    | { kind: "fold" }
    | { kind: "check" }
    | { kind: "call" }
    | { kind: "raise"; amount: number };
};

export type ReconnectSessionPayload = {
  gameId: string;
  sessionToken: string;
};

export type GameSnapshotPayload = {
  gameId: string;
  state: GameState;
  you?: {
    seatIndex: number;
    holeCards: [Card, Card];
  };
};

export type GameEventPayload = {
  gameId: string;
  event: GameEvent;
};

export type PlayerErrorPayload = {
  code: string;
  message: string;
};

export type ConnectionStatusPayload = {
  state: "connected" | "reconnecting" | "disconnected";
  sessionToken?: string;
};

export type ClientToServerEvents = {
  joinGame: (payload: JoinGamePayload, ack: (res: AckResult) => void) => void;
  leaveGame: (payload: LeaveGamePayload, ack: (res: AckResult) => void) => void;
  playerAction: (
    payload: PlayerActionPayload,
    ack: (res: AckResult) => void,
  ) => void;
  reconnectSession: (
    payload: ReconnectSessionPayload,
    ack: (res: AckResult) => void,
  ) => void;
};

export type ServerToClientEvents = {
  gameSnapshot: (payload: GameSnapshotPayload) => void;
  gameEvent: (payload: GameEventPayload) => void;
  playerError: (payload: PlayerErrorPayload) => void;
  connectionStatus: (payload: ConnectionStatusPayload) => void;
};
