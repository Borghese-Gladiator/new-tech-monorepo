export const ErrorCode = {
  NOT_YOUR_TURN: "NOT_YOUR_TURN",
  ILLEGAL_ACTION: "ILLEGAL_ACTION",
  GAME_NOT_FOUND: "GAME_NOT_FOUND",
  SEAT_TAKEN: "SEAT_TAKEN",
  GAME_NOT_OPEN: "GAME_NOT_OPEN",
  NO_OPEN_SEATS: "NO_OPEN_SEATS",
  NOT_SEATED: "NOT_SEATED",
  INVALID_PAYLOAD: "INVALID_PAYLOAD",
  SESSION_NOT_FOUND: "SESSION_NOT_FOUND",
  INTERNAL: "INTERNAL",
} as const;

export type ErrorCode = (typeof ErrorCode)[keyof typeof ErrorCode];

export type GameError = { code: ErrorCode; message: string };

export function makeError(code: ErrorCode, message: string): GameError {
  return { code, message };
}
