import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { io as ioClient, type Socket as ClientSocket } from "socket.io-client";
import type {
  AckResult,
  ClientToServerEvents,
  GameEventPayload,
  GameSnapshotPayload,
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

function actionAck(
  client: TypedClient,
  gameId: string,
  action: { kind: "fold" } | { kind: "check" } | { kind: "call" } | { kind: "raise"; amount: number },
): Promise<AckResult> {
  return new Promise((resolve) => {
    client.emit(
      "playerAction",
      { gameId, action },
      (ack: AckResult) => {
        resolve(ack);
      },
    );
  });
}

describe("@gas-city/server integration", () => {
  let server: ServerHandle;
  let port: number;

  beforeEach(async () => {
    server = createServer({ databaseUrl: ":memory:" });
    port = await server.listen(0);
  });

  afterEach(async () => {
    await server.close();
  });

  it("two players join, hand starts, fold resolves the hand", async () => {
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
      // Track snapshots and events for each client.
      const aSnapshots: GameSnapshotPayload[] = [];
      const bSnapshots: GameSnapshotPayload[] = [];
      const aEvents: GameEventPayload[] = [];
      const bEvents: GameEventPayload[] = [];

      a.on("gameSnapshot", (p) => aSnapshots.push(p));
      b.on("gameSnapshot", (p) => bSnapshots.push(p));
      a.on("gameEvent", (p) => aEvents.push(p));
      b.on("gameEvent", (p) => bEvents.push(p));

      await new Promise<void>((resolve) => a.on("connect", () => resolve()));
      await new Promise<void>((resolve) => b.on("connect", () => resolve()));

      const ackA = await joinAck(a, "new", "alice");
      expect(ackA.ok).toBe(true);

      // The 2nd join triggers startHand server-side.
      const ackB = await joinAck(b, "1", "bob");
      expect(ackB.ok).toBe(true);

      // Wait for both clients to receive at least one snapshot WITH hole cards.
      await new Promise((r) => setTimeout(r, 150));
      const firstBSnap = bSnapshots.find((s) => s.you !== undefined);
      const firstASnap = aSnapshots.find((s) => s.you !== undefined);
      expect(firstBSnap, "B should have received a per-seat snapshot").toBeDefined();
      expect(firstASnap, "A should have received a per-seat snapshot").toBeDefined();
      expect(firstBSnap?.state.street).toBe("preflop");
      expect(firstBSnap?.you?.holeCards.length).toBe(2);
      expect(firstASnap?.state.street).toBe("preflop");
      expect(firstASnap?.you?.holeCards.length).toBe(2);
      const lastA = aSnapshots[aSnapshots.length - 1];

      // The current actor preflop in 2-handed is the button (= seat 0 = alice).
      const startState = lastA?.state;
      expect(startState?.currentSeat).toBe(0);

      // Reset event/snapshot trackers for the action phase.
      aEvents.length = 0;
      bEvents.length = 0;
      aSnapshots.length = 0;
      bSnapshots.length = 0;

      if (!firstBSnap) throw new Error("missing snapshot for B");
      const gameId = firstBSnap.gameId;
      const ackFold = await actionAck(a, gameId, { kind: "fold" });
      expect(ackFold.ok).toBe(true);

      // Wait for both clients to see hand-resolved + a fresh snapshot.
      await new Promise((r) => setTimeout(r, 100));

      const handResolvedOnA = aEvents.some((e) => e.event.type === "hand-resolved");
      const handResolvedOnB = bEvents.some((e) => e.event.type === "hand-resolved");
      const actionTakenOnA = aEvents.some((e) => e.event.type === "action-taken");
      const actionTakenOnB = bEvents.some((e) => e.event.type === "action-taken");
      expect(handResolvedOnA).toBe(true);
      expect(handResolvedOnB).toBe(true);
      expect(actionTakenOnA).toBe(true);
      expect(actionTakenOnB).toBe(true);

      const finalA = aSnapshots[aSnapshots.length - 1];
      const finalB = bSnapshots[bSnapshots.length - 1];
      expect(finalA?.state.pots.length).toBe(0);
      expect(finalB?.state.pots.length).toBe(0);
      expect(finalA?.state.currentSeat).toBeNull();
      expect(finalB?.state.currentSeat).toBeNull();
    } finally {
      a.close();
      b.close();
    }
  });
});
