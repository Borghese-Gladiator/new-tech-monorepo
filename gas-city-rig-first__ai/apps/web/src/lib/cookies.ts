// sessionToken cookie scoped to a specific gameId so refresh survives.
const COOKIE_PREFIX = "gc_session_";
const ONE_DAY_SECONDS = 60 * 60 * 24;

function cookieName(gameId: string): string {
  return `${COOKIE_PREFIX}${encodeURIComponent(gameId)}`;
}

export function readSessionToken(gameId: string): string | null {
  if (typeof document === "undefined") return null;
  const target = `${cookieName(gameId)}=`;
  const parts = document.cookie ? document.cookie.split("; ") : [];
  for (const part of parts) {
    if (part.startsWith(target)) {
      const value = part.slice(target.length);
      return value ? decodeURIComponent(value) : null;
    }
  }
  return null;
}

export function writeSessionToken(gameId: string, token: string): void {
  if (typeof document === "undefined") return;
  const value = encodeURIComponent(token);
  document.cookie =
    `${cookieName(gameId)}=${value}; ` +
    `path=/game/${encodeURIComponent(gameId)}; ` +
    `max-age=${ONE_DAY_SECONDS}; SameSite=Lax`;
}

export function clearSessionToken(gameId: string): void {
  if (typeof document === "undefined") return;
  document.cookie =
    `${cookieName(gameId)}=; ` +
    `path=/game/${encodeURIComponent(gameId)}; ` +
    `max-age=0; SameSite=Lax`;
}
