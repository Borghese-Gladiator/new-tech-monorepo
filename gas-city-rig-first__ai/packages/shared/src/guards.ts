import type { JoinGamePayload } from "./events.js";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

export function isJoinGamePayload(value: unknown): value is JoinGamePayload {
  if (!isRecord(value)) return false;
  if (typeof value.gameId !== "string") return false;
  if (typeof value.displayName !== "string") return false;
  if (
    value.sessionToken !== undefined &&
    typeof value.sessionToken !== "string"
  ) {
    return false;
  }
  return true;
}
