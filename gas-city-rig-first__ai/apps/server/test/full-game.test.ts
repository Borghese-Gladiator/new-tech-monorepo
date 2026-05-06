import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { io as ioClient, type Socket as ClientSocket } from "socket.io-client";
import type {
  AckResult,
  ClientToServerEvents,
  GameSnapshotPayload,
  PlayerErrorPayload,
  ServerToClientEvents,
} from "@gas-city/shared";
import { createServer, type ServerHandle } from "../src/server.js";

type TypedClient = ClientSocket<ServerToClientEvents, ClientToServerEvents>;

function joinAck(
  client: TypedClient,
  gameId: string,
  displayName: string,
): Promise<AckResult> {
  return new Promise((resolve) => {
    client.emit("joinGame", { gameId, displayName }, (ack: AckResult) => {
      resolve(ack);
    });
  });
}

function waitForFirstPlayerError(
  client: TypedClient,
  timeoutMs: number,
): Promise<PlayerErrorPayload> {
  return new Promise((resolve, reject) => {
    const t = setTimeout(
      () => reject(new Error("timed out waiting for playerError")),
      timeoutMs,
    );
    client.once("playerError", (payload: PlayerErrorPayload) => {
      clearTimeout(t);
      resolve(payload);
    });
  });
}

describe("@gas-city/server joinGame — full-game rejection (BUG-V1)", () => {
  let server: ServerHandle;
  let port: number;

  beforeEach(async () => {
    server = createServer({ databaseUrl: ":memory:" });
    port = await server.listen(0);
  });

  afterEach(async () => {
    await server.close();
  });

  it("rejects a 3rd joinGame without sessionToken with playerError code GAME_FULL", async () => {
    const url = `http://localhost:${port}`;
    const a: TypedClient = ioClient(url, {
      transports: ["websocket"],
      forceNew: true,
    });
    const b: TypedClient = ioClient(url, {
      transports: ["websocket"],
      forceNew: true,
    });
    const c: TypedClient = ioClient(url, {
      transports: ["websocket"],
      forceNew: true,
    });

    try {
      await new Promise<void>((resolve) => a.on("connect", () => resolve()));
      await new Promise<void>((resolve) => b.on("connect", () => resolve()));
      await new Promise<void>((resolve) => c.on("connect", () => resolve()));

      // Two players fill the table; the 2nd join flips status to 'in_progress'.
      const ackA = await joinAck(a, "new", "alice");
      expect(ackA.ok).toBe(true);
      const ackB = await joinAck(b, "1", "bob");
      expect(ackB.ok).toBe(true);

      // Track snapshots & errors received by the 3rd client.
      const cSnapshots: GameSnapshotPayload[] = [];
      c.on("gameSnapshot", (p) => cSnapshots.push(p));

      const errPromise = waitForFirstPlayerError(c, 2000);
      const ackC = await joinAck(c, "1", "carol");

      // Ack must also report failure so any caller relying on it sees the error.
      expect(ackC.ok).toBe(false);
      if (ackC.ok) throw new Error("unreachable");
      expect(ackC.error.code).toBe("GAME_FULL");

      const err = await errPromise;
      expect(err.code).toBe("GAME_FULL");
      expect(err.message).toMatch(/full/i);

      // Carol must not have received a gameSnapshot.
      // Allow a beat for any stray broadcasts (there should be none —
      // joinGame must NOT have joined Carol to the room).
      await new Promise((r) => setTimeout(r, 100));
      expect(cSnapshots.length).toBe(0);
    } finally {
      a.close();
      b.close();
      c.close();
    }
  });

  it("does not include the in-progress game with > 2 seats in listOpenGames", async () => {
    const url = `http://localhost:${port}`;
    const a: TypedClient = ioClient(url, {
      transports: ["websocket"],
      forceNew: true,
    });
    const b: TypedClient = ioClient(url, {
      transports: ["websocket"],
      forceNew: true,
    });

    try {
      await new Promise<void>((resolve) => a.on("connect", () => resolve()));
      await new Promise<void>((resolve) => b.on("connect", () => resolve()));

      const ackA = await joinAck(a, "new", "alice");
      expect(ackA.ok).toBe(true);
      const ackB = await joinAck(b, "1", "bob");
      expect(ackB.ok).toBe(true);

      // Hit the HTTP /games endpoint and ensure no entry has seatsTaken > numSeats.
      const res = await fetch(`${url}/games`);
      expect(res.ok).toBe(true);
      const body = (await res.json()) as {
        games: ReadonlyArray<{
          id: string;
          status: string;
          seatsTaken: number;
          numSeats: number;
        }>;
      };
      for (const g of body.games) {
        expect(g.seatsTaken).toBeLessThanOrEqual(g.numSeats);
      }
    } finally {
      a.close();
      b.close();
    }
  });
});
