"use client";

import { useMemo, useState } from "react";
import type { GameState, PlayerState } from "@gas-city/poker-core";
import type { PlayerActionPayload } from "@gas-city/shared";

type Action = PlayerActionPayload["action"];

export type ActionBarProps = {
  state: GameState;
  localSeat: number;
  onAction: (action: Action) => void;
  disabled?: boolean;
};

function localPlayer(state: GameState, seat: number): PlayerState | undefined {
  return state.players.find((p) => p.seat === seat);
}

function callAmount(state: GameState, player: PlayerState): number {
  const owed = state.currentBet - player.committedThisStreet;
  return Math.max(0, Math.min(owed, player.stack));
}

function minRaiseTo(state: GameState, player: PlayerState): number {
  const minDelta = Math.max(state.lastRaiseSize, state.config.blinds.bb);
  const target = state.currentBet + minDelta;
  const max = player.committedThisStreet + player.stack;
  return Math.min(target, max);
}

function maxRaiseTo(_state: GameState, player: PlayerState): number {
  return player.committedThisStreet + player.stack;
}

export function ActionBar({
  state,
  localSeat,
  onAction,
  disabled,
}: ActionBarProps): JSX.Element | null {
  const player = localPlayer(state, localSeat);
  const yourTurn = state.currentSeat === localSeat;
  const isInteractive = !!player && !disabled && yourTurn && player.status === "active";

  const callAmt = player ? callAmount(state, player) : 0;
  const min = useMemo(
    () => (player ? minRaiseTo(state, player) : 0),
    [state, player],
  );
  const max = useMemo(
    () => (player ? maxRaiseTo(state, player) : 0),
    [state, player],
  );
  const [raiseTo, setRaiseTo] = useState<number>(min);

  if (!player) return null;

  const canCheck = isInteractive && callAmt === 0;
  const canCall = isInteractive && callAmt > 0;
  const canRaise = isInteractive && max > state.currentBet && player.stack > 0;

  return (
    <div className="flex flex-wrap items-center gap-3 rounded-xl bg-zinc-950/80 p-4 ring-1 ring-zinc-800">
      <button
        type="button"
        disabled={!isInteractive}
        onClick={() => onAction({ kind: "fold" })}
        className="rounded-lg bg-rose-700 px-4 py-2 font-semibold text-white shadow disabled:cursor-not-allowed disabled:bg-zinc-700 disabled:text-zinc-400"
      >
        Fold
      </button>
      <button
        type="button"
        disabled={!canCheck}
        onClick={() => onAction({ kind: "check" })}
        className="rounded-lg bg-zinc-700 px-4 py-2 font-semibold text-white shadow disabled:cursor-not-allowed disabled:bg-zinc-800 disabled:text-zinc-500"
      >
        Check
      </button>
      <button
        type="button"
        disabled={!canCall}
        onClick={() => onAction({ kind: "call" })}
        className="rounded-lg bg-emerald-700 px-4 py-2 font-semibold text-white shadow disabled:cursor-not-allowed disabled:bg-zinc-800 disabled:text-zinc-500"
      >
        Call {callAmt > 0 ? <span className="font-mono">{callAmt}</span> : null}
      </button>

      <div className="flex flex-1 items-center gap-3 sm:min-w-[260px]">
        <input
          type="range"
          min={min}
          max={max}
          step={1}
          value={Math.min(Math.max(raiseTo, min), max)}
          disabled={!canRaise}
          onChange={(e) => setRaiseTo(Number(e.target.value))}
          className="flex-1 accent-amber-400 disabled:opacity-40"
          aria-label="raise amount"
        />
        <span className="w-16 text-right font-mono text-sm">
          {Math.min(Math.max(raiseTo, min), max)}
        </span>
        <button
          type="button"
          disabled={!canRaise}
          onClick={() =>
            onAction({
              kind: "raise",
              amount: Math.min(Math.max(raiseTo, min), max),
            })
          }
          className="rounded-lg bg-amber-500 px-4 py-2 font-semibold text-zinc-900 shadow disabled:cursor-not-allowed disabled:bg-zinc-800 disabled:text-zinc-500"
        >
          Raise
        </button>
      </div>

      {!yourTurn ? (
        <span className="text-sm italic text-zinc-400">Waiting for opponent…</span>
      ) : null}
    </div>
  );
}
