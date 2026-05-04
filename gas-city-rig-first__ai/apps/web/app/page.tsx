"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

type OpenGame = {
  id: string;
  status: string;
  seatsTaken: number;
  numSeats: number;
  createdAt: number;
  updatedAt: number;
};

type GamesResponse = { games: ReadonlyArray<OpenGame> };

async function fetchOpenGames(): Promise<ReadonlyArray<OpenGame>> {
  const res = await fetch("/api/games", { cache: "no-store" });
  if (!res.ok) throw new Error(`fetch /api/games -> ${res.status}`);
  const body = (await res.json()) as GamesResponse;
  return body.games ?? [];
}

async function createGame(): Promise<{ id: string }> {
  const res = await fetch("/api/games", { method: "POST" });
  if (!res.ok) throw new Error(`POST /api/games -> ${res.status}`);
  return (await res.json()) as { id: string };
}

export default function LobbyPage(): JSX.Element {
  const router = useRouter();
  const [games, setGames] = useState<ReadonlyArray<OpenGame>>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [displayName, setDisplayName] = useState<string>("");
  const [joinGameId, setJoinGameId] = useState<string>("");
  const [busy, setBusy] = useState<boolean>(false);

  const refresh = useCallback(async () => {
    try {
      const list = await fetchOpenGames();
      setGames(list);
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 3000);
    return () => clearInterval(t);
  }, [refresh]);

  const goToGame = useCallback(
    (gameId: string, name: string) => {
      const params = new URLSearchParams();
      if (name) params.set("name", name);
      router.push(`/game/${encodeURIComponent(gameId)}?${params.toString()}`);
    },
    [router],
  );

  const onCreate = useCallback(async () => {
    if (!displayName.trim()) {
      setError("Display name required to create a game.");
      return;
    }
    setBusy(true);
    try {
      const created = await createGame();
      goToGame(created.id, displayName.trim());
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }, [displayName, goToGame]);

  const onJoin = useCallback(() => {
    if (!displayName.trim()) {
      setError("Display name required.");
      return;
    }
    if (!joinGameId.trim()) {
      setError("Game id required to join.");
      return;
    }
    goToGame(joinGameId.trim(), displayName.trim());
  }, [displayName, joinGameId, goToGame]);

  return (
    <main className="mx-auto flex max-w-3xl flex-col gap-8 p-8">
      <header className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight">Gas City Poker</h1>
        <p className="text-zinc-400">2-handed Texas Hold&apos;em PoC</p>
      </header>

      <section className="flex flex-col gap-3 rounded-2xl bg-zinc-950/70 p-6 ring-1 ring-zinc-800">
        <h2 className="text-lg font-semibold">Your name</h2>
        <input
          type="text"
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          placeholder="Display name"
          className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 outline-none focus:border-amber-400"
          aria-label="display name"
        />
      </section>

      <section className="grid gap-6 md:grid-cols-2">
        <div className="flex flex-col gap-3 rounded-2xl bg-zinc-950/70 p-6 ring-1 ring-zinc-800">
          <h2 className="text-lg font-semibold">Create new game</h2>
          <p className="text-sm text-zinc-400">
            Start a fresh table. Share the game id with a friend to join.
          </p>
          <button
            type="button"
            disabled={busy}
            onClick={onCreate}
            className="mt-auto rounded-lg bg-amber-500 px-4 py-2 font-semibold text-zinc-900 disabled:opacity-50"
          >
            {busy ? "Creating…" : "Create"}
          </button>
        </div>

        <div className="flex flex-col gap-3 rounded-2xl bg-zinc-950/70 p-6 ring-1 ring-zinc-800">
          <h2 className="text-lg font-semibold">Join existing</h2>
          <input
            type="text"
            value={joinGameId}
            onChange={(e) => setJoinGameId(e.target.value)}
            placeholder="Game id (e.g. 1)"
            className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 outline-none focus:border-amber-400"
            aria-label="game id"
          />
          <button
            type="button"
            onClick={onJoin}
            className="mt-auto rounded-lg bg-emerald-600 px-4 py-2 font-semibold text-white"
          >
            Join
          </button>
        </div>
      </section>

      <section className="flex flex-col gap-3 rounded-2xl bg-zinc-950/70 p-6 ring-1 ring-zinc-800">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Open games</h2>
          <button
            type="button"
            onClick={refresh}
            className="text-xs text-zinc-300 underline-offset-2 hover:underline"
          >
            Refresh
          </button>
        </div>
        {loading ? (
          <p className="text-sm text-zinc-400">Loading…</p>
        ) : games.length === 0 ? (
          <p className="text-sm text-zinc-400">No open games. Create one above.</p>
        ) : (
          <ul className="flex flex-col divide-y divide-zinc-800">
            {games.map((g) => (
              <li
                key={g.id}
                className="flex items-center justify-between gap-3 py-3"
              >
                <div className="flex flex-col">
                  <span className="font-mono text-sm">#{g.id}</span>
                  <span className="text-xs text-zinc-400">
                    {g.status} · {g.seatsTaken}/{g.numSeats} seated
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    if (!displayName.trim()) {
                      setError("Display name required to join.");
                      return;
                    }
                    goToGame(g.id, displayName.trim());
                  }}
                  className="rounded-lg bg-emerald-700 px-3 py-1 text-sm font-semibold text-white"
                >
                  Resume / Join
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      {error ? (
        <div className="rounded-lg bg-rose-700/30 px-4 py-2 text-sm text-rose-200 ring-1 ring-rose-700">
          {error}
        </div>
      ) : null}
    </main>
  );
}
