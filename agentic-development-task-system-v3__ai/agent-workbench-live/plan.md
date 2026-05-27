# plan.md — auto-chain /plan → /start (remove the `ready` agent stop)

## Brief

Today the agent stops at the `ready` state because `.claude/commands/plan.md`
tells it to: "Stop here. This is a real human approval gate." The CLI also
emits a `STOP.` banner at `planning -> ready`, and `AGENTS.md` instructs the
agent to stop on any `STOP.` banner. The user wants runs to flow straight
through into `building` without stopping.

Chosen approach (per user selection): **auto-chain into `/start`**. The agent
calls `/start $RUN_ID --approved-by <user>` immediately after `/plan` finishes,
so `ready` becomes a transient state that the agent passes through.

The CLI lifecycle is unchanged — `ready` still exists in the state machine,
`agent-workbench start` still requires `--approved-by`, and the `STOP.` banner
on the `planning -> ready` transition is still written to disk for audit. Only
the agent's interpretation of that banner changes for the `ready` case.

## Changes

1. **`.claude/commands/plan.md`** — rewrite the "Next step" section.
   - Remove "Stop here. This is a real human approval gate…"
   - Replace with an auto-chain instruction: immediately invoke
     `/start $RUN_ID` (the agent provides `--approved-by` from the env user;
     `start.md` already documents how it gets that value).
   - Keep the user-facing report (the path to `plan.md`, the one-paragraph
     summary), but reframe it as "told the user before starting" rather than
     "told the user instead of starting".

2. **`AGENTS.md`** — narrow the `STOP.` banner rule.
   - Line 28 currently says: "the run has landed in a state the agent does
     not drive (`ready`, `human_review`, or terminal). Do not invoke the
     listed next commands."
   - Update: only `human_review` and the terminal states are agent-stopping.
     `ready` is now a transient state the agent passes through via `/start`.

3. **`.claude/commands/new-run.md`** — update the "two real human gates" claim.
   - Line 90 says: "The agent only stops at the two real human gates
     (`ready` and `human_review`)…"
   - Update to a single human gate: `human_review`.

4. **`.claude/commands/shape.md`** — update the gate forward-reference.
   - Line 60 says: "the next human gate is `ready -> building`, which is
     owned by `/start`."
   - Update to point at `human_review` instead.

5. **`.claude/commands/start.md`** — clarify how the agent obtains
   `--approved-by` when auto-chaining (no prompt; use `$USER`). Today it says
   "defaults to current user if you ask"; rephrase so the auto-chain path
   doesn't require asking.

The CLI code (`lib/cli/cmd_plan.py`, `cmd_start.py`, `_stop_banner.py`) and
the lifecycle / transitions schemas are unchanged. The `ready` state stays in
the state machine; only the agent's stop-on-banner rule narrows. This keeps
the human-driven CLI path (`agent-workbench start` from a terminal) working
exactly as before.

## Tests

### Unit

No code changes → no new unit tests. The existing banner snapshot
(`tests/snapshots/stop_banner_ready.expected.txt`) still matches because the
banner text isn't changing.

### Manual

Slash-command markdown is agent-facing, not executable, so verification is by
inspection plus an end-to-end re-read:

- Re-read `.claude/commands/plan.md` and confirm the "Next step" section
  unambiguously instructs auto-chain into `/start` with no stop language.
- Re-read `AGENTS.md` § "How to drive the workbench" and confirm the
  `STOP.` rule now lists only `human_review` + terminals.
- Re-read `new-run.md` and `shape.md` and confirm no remaining references to
  "ready" as a human gate.
- Grep the repo for any leftover phrases like "ready human gate" / "ready
  is human-owned" / "Stop here" tied to `/plan` and fix any stragglers.

No actual `/plan` run is required to verify — the change is purely in
agent-facing instructions. If we want a live confirmation, the user can pick
any draft run and run `/shape` → `/plan` and watch whether the agent
auto-invokes `/start`.
