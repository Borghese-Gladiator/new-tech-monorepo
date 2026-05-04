"use client";

import { useCallback, useEffect, useReducer, useRef } from "react";
import { useParams, useSearchParams } from "next/navigation";
import type {
  AckResult,
  ConnectionStatusPayload,
  GameEventPayload,
  GameSnapshotPayload,
  PlayerActionPayload,
  PlayerErrorPayload,
} from "@gas-city/shared";
import {
  clearSessionToken,
  readSessionToken,
  writeSessionToken,
} from "@/lib/cookies";
import { createGameSocket, type GameSocket } from "@/lib/socket";
import {
  initialTableState,
  tableReducer,
  type EventLogEntry,
} from "@/lib/tableState";
import { ActionBar } from "@/components/ActionBar";
import { Board } from "@/components/Board";
import { ConnectionPill } from "@/components/ConnectionPill";
import { ErrorToast } from "@/components/ErrorToast";
import { Pot } from "@/components/Pot";
import { SeatView } from "@/components/Seat";

type Action = PlayerActionPayload["action"];

function describeEvent(entry: EventLogEntry): string {
  const e = entry.event;
  switch (e.type) {
    case "hand-started":
      return `Hand ${e.handId} started · button=seat${e.buttonSeat}`;
    case "blinds-posted":
      return `SB ${e.sb.amount} (seat${e.sb.seat}) · BB ${e.bb.amount} (seat${e.bb.seat})`;
    case "cards-dealt":
      return `Dealt ${e.street} (${e.community.length} community)`;
    case "hole-cards-dealt":
      return `Hole cards dealt to seat${e.seat}`;
    case "action-taken": {
      const a = e.action;
      const detail =
        a.kind === "raise"
          ? `raise to ${a.amount}`
          : a.kind === "call"
            ? `call ${e.amount}`
            : a.kind;
      return `Seat${e.seat} ${detail}`;
    }
    case "street-advanced":
      return `${e.from} → ${e.to}`;
    case "pot-updated":
      return `Pot updated (${e.pots.length} pots)`;
    case "hand-resolved":
      return `Resolved · winners: ${e.winners
        .map((w) => `seat${w.seat}+${w.amount}`)
        .join(", ")}`;
    default:
      return "(unknown event)";
  }
}

export default function GamePage(): JSX.Element {
  const params = useParams<{ gameId: string }>();
  const searchParams = useSearchParams();
  const gameId = params?.gameId ?? "";
  const displayName = searchParams?.get("name") ?? "";

  const [state, dispatch] = useReducer(tableReducer, initialTableState);
  const socketRef = useRef<GameSocket | null>(null);
  const joinedRef = useRef<boolean>(false);

  // Bootstrap socket once per gameId.
  useEffect(() => {
    if (!gameId) return undefined;
    const socket = createGameSocket();
    socketRef.current = socket;

    const join = (): void => {
      const cookieToken = readSessionToken(gameId);
      const payload = cookieToken
        ? { gameId, displayName: displayName || "player", sessionToken: cookieToken }
        : { gameId, displayName: displayName || "player" };
      socket.emit("joinGame", payload, (ack: AckResult) => {
        if (!ack.ok) {
          dispatch({
            type: "error",
            message: `Join failed: ${ack.error.message}`,
          });
          return;
        }
        joinedRef.current = true;
      });
    };

    socket.on("connect", () => {
      dispatch({ type: "connection", state: "connected" });
      const cookieToken = readSessionToken(gameId);
      if (joinedRef.current && cookieToken) {
        socket.emit(
          "reconnectSession",
          { gameId, sessionToken: cookieToken },
          (ack: AckResult) => {
            if (!ack.ok) {
              dispatch({
                type: "error",
                message: `Reconnect failed: ${ack.error.message}`,
              });
            }
          },
        );
      } else {
        join();
      }
    });

    socket.on("disconnect", () => {
      dispatch({ type: "connection", state: "reconnecting" });
    });

    socket.io.on("reconnect_attempt", () => {
      dispatch({ type: "connection", state: "reconnecting" });
    });

    socket.io.on("reconnect_failed", () => {
      dispatch({ type: "connection", state: "disconnected" });
    });

    socket.on("connectionStatus", (payload: ConnectionStatusPayload) => {
      dispatch({ type: "connection", state: payload.state });
      if (payload.sessionToken) {
        writeSessionToken(gameId, payload.sessionToken);
        dispatch({ type: "session-token", token: payload.sessionToken });
      }
    });

    socket.on("gameSnapshot", (payload: GameSnapshotPayload) => {
      const action: Parameters<typeof dispatch>[0] = payload.you
        ? { type: "snapshot", state: payload.state, you: payload.you }
        : { type: "snapshot", state: payload.state };
      dispatch(action);
    });

    socket.on("gameEvent", (payload: GameEventPayload) => {
      dispatch({ type: "event", event: payload.event });
    });

    socket.on("playerError", (payload: PlayerErrorPayload) => {
      dispatch({
        type: "error",
        message: `${payload.code}: ${payload.message}`,
      });
    });

    return () => {
      socket.removeAllListeners();
      socket.io.removeAllListeners();
      socket.close();
      socketRef.current = null;
    };
  }, [gameId, displayName]);

  // Auto-clear flash after a beat.
  useEffect(() => {
    if (state.flashSeats.length === 0) return undefined;
    const t = setTimeout(() => dispatch({ type: "clear-flash" }), 700);
    return () => clearTimeout(t);
  }, [state.flashSeats]);

  const onAction = useCallback(
    (action: Action) => {
      const socket = socketRef.current;
      if (!socket) return;
      socket.emit(
        "playerAction",
        { gameId, action },
        (ack: AckResult) => {
          if (!ack.ok) {
            dispatch({
              type: "error",
              message: `${ack.error.code}: ${ack.error.message}`,
            });
          }
        },
      );
    },
    [gameId],
  );

  const onLeave = useCallback(() => {
    const socket = socketRef.current;
    socket?.emit("leaveGame", { gameId }, () => {
      clearSessionToken(gameId);
    });
  }, [gameId]);

  const gameState = state.state;
  const localSeat = state.you?.seatIndex;

  return (
    <main className="mx-auto flex max-w-5xl flex-col gap-6 p-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-col">
          <span className="text-xs uppercase tracking-wide text-zinc-400">
            Game
          </span>
          <span className="font-mono text-lg">#{gameId}</span>
        </div>
        <ConnectionPill state={state.connection} />
        <button
          type="button"
          onClick={onLeave}
          className="rounded-lg bg-zinc-800 px-3 py-1 text-sm text-zinc-200 hover:bg-zinc-700"
        >
          Leave
        </button>
      </header>

      {!gameState ? (
        <div className="rounded-2xl bg-zinc-950/70 p-10 text-center text-zinc-400 ring-1 ring-zinc-800">
          Waiting for opponent…
        </div>
      ) : (
        <>
          <section className="flex flex-col items-center gap-6 rounded-3xl bg-felt p-10 ring-1 ring-emerald-900/60">
            <div className="grid w-full grid-cols-2 gap-6">
              {gameState.players.map((player) => {
                const isLocal = localSeat === player.seat;
                const youCards =
                  isLocal && state.you ? state.you.holeCards : undefined;
                return (
                  <SeatView
                    key={player.seat}
                    player={player}
                    isCurrent={gameState.currentSeat === player.seat}
                    isLocal={isLocal}
                    {...(youCards ? { holeCards: youCards } : {})}
                    flash={state.flashSeats.includes(player.seat)}
                  />
                );
              })}
            </div>

            <Pot pots={gameState.pots} />
            <Board community={gameState.community} street={gameState.street} />
          </section>

          {localSeat !== undefined ? (
            <ActionBar
              state={gameState}
              localSeat={localSeat}
              onAction={onAction}
              disabled={state.connection !== "connected"}
            />
          ) : (
            <p className="text-center text-sm italic text-zinc-400">
              Spectating (no seat assigned).
            </p>
          )}

          <section className="rounded-2xl bg-zinc-950/70 p-4 ring-1 ring-zinc-800">
            <h3 className="mb-2 text-sm font-semibold text-zinc-200">
              Event log
            </h3>
            <ul className="flex max-h-40 flex-col gap-1 overflow-auto text-xs text-zinc-300">
              {state.events.length === 0 ? (
                <li className="text-zinc-500">No events yet.</li>
              ) : (
                state.events
                  .slice()
                  .reverse()
                  .map((entry) => (
                    <li key={entry.id} className="font-mono">
                      {describeEvent(entry)}
                    </li>
                  ))
              )}
            </ul>
          </section>
        </>
      )}

      {state.error ? (
        <ErrorToast
          message={state.error}
          onDismiss={() => dispatch({ type: "clear-error" })}
        />
      ) : null}
    </main>
  );
}
