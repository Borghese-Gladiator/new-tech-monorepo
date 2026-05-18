# TODO

What needs to be implemented to turn the design in `agent-workbench-final/` into a working system.

Ordered roughly by dependency. Items inside a section can move in parallel.

---

## 0. Repo bootstrap

- [ ] Pick the implementation language. Default: Python 3 (stdlib only for V1).
- [ ] Create the project skeleton:
  ```text
  agent-workbench/
    AGENTS.md                    # how any agent should operate here
    bin/agent-workbench          # CLI entrypoint
    lib/                         # Python modules
    .claude/commands/            # slash commands (markdown)
    scripts/                     # deterministic bash glue
    runs/                        # created lazily per run
    worktrees/                   # created lazily per run
    tests/
  ```
- [ ] Wire `bin/agent-workbench` so `agent-workbench <subcommand>` dispatches.
- [ ] Decide where the workbench root lives on disk (env var `AGENT_WORKBENCH_ROOT` or fixed default).
- [ ] Write `AGENTS.md` at the workbench root. Audience: any AI agent (Claude Code, Codex, etc.) that opens this folder. Must contain:
  - The 8-state lifecycle in one sentence each.
  - The "only `draft` may ask questions" rule.
  - The "only the transition engine writes `status`" rule.
  - Which command to run for each state change (table mirroring §2).
  - Where the source of truth lives: `runs/<run_id>/metadata.yaml` for state, `events.jsonl` for history.
  - When to use a slash command vs. a CLI call (LLM-bearing vs. deterministic).
  - Pointer to `architecture.md` and `lifecycle.md` for deeper context.
  - Regenerate when CLI contracts or lifecycle change.

## 1. Core libraries

These are the modules every CLI command depends on. Build them first.

### 1a. `lib/metadata.py` — run metadata read/write
- [ ] `load(run_id) -> dict` and `save(run_id, data)` against `runs/<run_id>/metadata.yaml`.
- [ ] Stdlib-only YAML reader/writer for the flat subset used by `schemas/run-metadata.yaml`.
- [ ] `create(run_id, initial_fields)` — builds a new `metadata.yaml` from the template.
- [ ] Validation against the required-fields list in `schemas/run-metadata.yaml`.
- [ ] **No other module writes `metadata.yaml`.**

### 1b. `lib/events.py` — append-only event log
- [ ] `append(run_id, event_type, payload, actor)` writes one JSON line to `runs/<run_id>/events.jsonl`.
- [ ] Auto-fills `schema_version`, `seq`, `event_id`, `at`, `status`.
- [ ] Validate the payload against `schemas/events.jsonl` for the given `event_type`.
- [ ] Reject the write if required payload fields are missing.

### 1c. `lib/transitions.py` — the transition engine
- [ ] `transition(run_id, to_state, evidence, actor)`:
  - Loads current metadata.
  - Looks up `(from, to)` in `schemas/transitions.yaml`.
  - Verifies every required evidence field is present and non-empty.
  - Rejects if current state is terminal.
  - Emits `TransitionApplied` (and any secondary events listed in the schema, e.g. `WorktreeCreated`, `RunCompleted`, `RunAbandoned`, `BounceRequested`).
  - Updates `metadata.status` and `updated_at`.
  - Emits `TransitionRejected` with a structured `reason` on failure.
- [ ] Honor the `any_non_terminal -> abandoned` wildcard.
- [ ] **No other module changes `metadata.status`.**

### 1d. `lib/locks.py` — per-run lock
- [ ] Create/release `runs/<run_id>/.lock`.
- [ ] Block concurrent mutating commands on the same run.
- [ ] No-op for read-only commands.

### 1e. `lib/repos.py` — git/worktree manager
- [ ] `verify_existing(repo_path, base_ref)` — confirms path, git status, base ref, no branch/worktree collisions.
- [ ] `create_new(repo_path)` — init repo, write minimal scaffold (monorepo layout default), make initial commit, return SHA.
- [ ] `create_worktree(repo_path, branch_name, worktree_path, base_ref)` — runs `git worktree add -b ...`.
- [ ] `remove_worktree(repo_path, worktree_path)` — used by future cleanup, not by lifecycle commands.
- [ ] Repo-name disambiguation when two `repo_path` basenames collide.
- [ ] Always shell out with `git -C <repo_path>`, never `cd`.

### 1f. `lib/run_ids.py` — naming
- [ ] Generate `run_id` as `YYYY-MM-DD-<slug>` from a user-supplied slug or the brief title.
- [ ] Slug sanitization (kebab-case, ascii, length cap).
- [ ] Worktree-name and branch-name templates from `agent-workbench.yaml`.

### 1g. `lib/audit.py` — render `audit.md`
- [ ] Read `events.jsonl` + all artifacts for one run.
- [ ] Produce `audit.md` containing: original request, scope, repo path, branch name, worktree path, assumptions, decisions, commands run, implementation summary, diff summary, review result, QA result, transition timeline, final status.
- [ ] Idempotent: rerunning overwrites cleanly.

### 1h. `lib/config.py` — workbench config loader
- [ ] Read `agent-workbench.yaml` (paths, defaults, policies, gates).
- [ ] Expose typed accessors instead of dict lookups in command code.

## 2. CLI command contracts

Each subcommand is a thin shell around the libraries. Every command should:
- acquire `lib/locks` (if mutating),
- read state via `lib/metadata`,
- gather evidence,
- call `lib/transitions.transition(...)`,
- append any extra events,
- print a structured result to stdout.

### 2a. `new-run`
- [ ] Flags: `--repo-path <path>` OR `--new-repo-path <path>`, `--worktree-name <slug>`, `--idea-file <path>` or stdin, `--scope-kind <enum>` (default `implementation`), `--repo-name <override>`.
- [ ] Creates `runs/<run_id>/`, writes `raw-idea.md`, emits `RunCreated`.
- [ ] Initial state: `draft`.
- [ ] For `--new-repo-path`, calls `lib/repos.create_new` immediately so the path is real before planning.
- [ ] **Exit codes:** 0 success; 2 validation error; 3 path collision.

### 2b. `shape <run_id>`
- [ ] Slash command (`/shape`) wrapper, since shaping is LLM-bearing.
- [ ] Reads `raw-idea.md` (+ optional `answers.md`).
- [ ] Writes `brief.md`.
- [ ] Transitions `draft -> shaping -> planning`. (Two transitions in one command is fine; the engine records both.)
- [ ] Emits `ArtifactWritten` for `brief.md`.

### 2c. `plan <run_id>`
- [ ] Slash command (`/plan`) wrapper. May spawn `Explore` subagents to map the target repo.
- [ ] Writes `plan.md`, `preflight.md`, `assumptions.md`, `decisions.md`.
- [ ] Populates `target.worktree.name`, `target.worktree.branch_name` in metadata.
- [ ] Emits `ArtifactWritten` ×4, `AssumptionRecorded` per assumption, `DecisionRecorded` per decision, `PreflightCompleted`.
- [ ] Transitions `shaping -> planning -> ready`. (Or assumes already in `planning` and only fires the second.)

### 2d. `start <run_id>`
- [ ] Flags: `--approved-by <name>`.
- [ ] Verifies pre-implementation artifacts exist (uses `agent-workbench.yaml.gates.require_preimplementation_audit_inputs`).
- [ ] Calls `lib/repos.create_worktree`.
- [ ] Emits `WorktreeCreated`.
- [ ] Transitions `ready -> building`.
- [ ] Prints the worktree path so the user can `cd` into it.

### 2e. `validate <run_id>`
- [ ] Slash command (`/validate`) wrapper, since review and QA are LLM-bearing.
- [ ] Reads the worktree and all prior artifacts.
- [ ] Writes `implementation-summary.md`, `diff-summary.md` first if missing.
- [ ] Runs review skill; writes `review.md`; emits `ReviewCompleted`.
- [ ] Runs QA (unit/integration/lint/Playwright as applicable); writes `qa/report.md`, `qa/commands.txt`, populates `qa/artifacts/`, `qa/recordings/`, `qa/traces/`; emits `QACompleted` and `CommandRun` per command.
- [ ] Calls `lib/audit.render` to produce `audit.md`; emits `AuditRendered`.
- [ ] Writes `handoff.md`; emits `HumanHandoffCreated`.
- [ ] Transitions `building -> validating -> human_review`.

### 2f. `handoff <run_id>`
- [ ] Read-only command that prints `handoff.md` + branch + worktree path to stdout.
- [ ] Used to re-display handoff info without re-running validation.

### 2g. `complete <run_id>`
- [ ] Flags: `--accepted-by <name>`, `--completion-ref <ref>` (defaults to `local-branch:<branch_name>`).
- [ ] Transitions `human_review -> done`.
- [ ] Emits `RunCompleted`.

### 2h. `bounce <run_id>`
- [ ] Flags: `--reason <text>` (required), `--requested-by <name>`.
- [ ] Transitions `human_review -> building`.
- [ ] Emits `BounceRequested`.

### 2i. `abandon <run_id>`
- [ ] Flags: `--reason <text>` (required), `--abandoned-by <name>`.
- [ ] Wildcard transition from any non-terminal state.
- [ ] Emits `RunAbandoned`.

### 2j. Read-only helpers
- [ ] `agent-workbench list` — table of runs with `run_id`, `status`, `repo_name`, `branch_name`, `updated_at`.
- [ ] `agent-workbench show <run_id>` — pretty-print metadata + artifact paths.
- [ ] `agent-workbench events <run_id>` — tail `events.jsonl`.

## 3. Slash commands

Live under `.claude/commands/` in this repo. Each is a markdown file. Two flavors:

- **Thin wrappers** — front-ends for deterministic CLI commands. The skill exists so an agent can discover the right invocation without reading the full docs. Body is mostly Bash + a short usage paragraph.
- **LLM-bearing** — Bash prefix sets up state, the markdown body is the prompt the model executes (shaping, planning, validation).

**Thin wrappers**

- [ ] `/new-run` — describes flags, prompts for `--repo-path` or `--new-repo-path` + `--worktree-name` + idea text, then runs `agent-workbench new-run`. Prints the `run_id`.
- [ ] `/start` — confirms the human approves, prompts for `--approved-by`, runs `agent-workbench start <run_id>`, prints the worktree path.
- [ ] `/handoff` — runs `agent-workbench handoff <run_id>` and renders the result.
- [ ] `/complete` — prompts for `--accepted-by` and optional `--completion-ref`, runs `agent-workbench complete <run_id>`.
- [ ] `/bounce` — prompts for `--reason`, runs `agent-workbench bounce <run_id>`.
- [ ] `/abandon` — prompts for `--reason`, runs `agent-workbench abandon <run_id>`.
- [ ] `/runs` — wraps `agent-workbench list` for a quick "what runs exist".
- [ ] `/run-show` — wraps `agent-workbench show <run_id>`.

**LLM-bearing**

- [ ] `/shape` — Bash prefix verifies state; LLM body writes `brief.md` from `raw-idea.md` per the lifecycle contract.
- [ ] `/plan` — Bash prefix verifies state; LLM body inspects the target repo (may spawn `Explore` subagents) and writes `plan.md`, `preflight.md`, `assumptions.md`, `decisions.md`.
- [ ] `/validate` — Bash prefix captures diff + opens worktree; LLM body runs review + QA, calls `lib/audit.render`, writes `handoff.md`.

**Rules for all slash commands**

- [ ] Must end by calling `agent-workbench <cmd>` (which calls `lib/transitions.transition(...)` internally). Never edit `metadata.yaml` or `events.jsonl` directly from the slash command body.
- [ ] Frontmatter `description:` should be specific enough that Claude Code's skill router picks the right one ("Run an Agent Workbench shaping pass on run <id>", not "shape something").
- [ ] Each skill links back to the relevant section of `lifecycle.md` so the agent can read the contract if it needs more detail.

## 4. Templates

Stub markdown files the agents fill in (kept under `templates/`):

- [ ] `templates/raw-idea.md`
- [ ] `templates/brief.md` (with the section headers from `lifecycle.md`)
- [ ] `templates/plan.md`
- [ ] `templates/preflight.md`
- [ ] `templates/assumptions.md` (one entry per assumption, `assumption_id` required)
- [ ] `templates/decisions.md` (DR-NNN style)
- [ ] `templates/implementation-summary.md`
- [ ] `templates/diff-summary.md`
- [ ] `templates/review.md`
- [ ] `templates/qa/report.md`
- [ ] `templates/handoff.md`
- [ ] `templates/audit.md`

## 5. Testing

- [ ] Unit tests for `lib/metadata` round-trip.
- [ ] Unit tests for `lib/events` payload validation against `schemas/events.jsonl`.
- [ ] Unit tests for `lib/transitions` — every `(from, to)` pair in `schemas/transitions.yaml`, plus rejection cases (missing evidence, terminal-state transition, manual-edit detection).
- [ ] Integration test: full happy path against a throwaway repo — `new-run -> shape -> plan -> start -> validate -> complete`.
- [ ] Integration test: bounce loop — `human_review -> building -> validating -> human_review`.
- [ ] Integration test: abandon from each non-terminal state.
- [ ] Integration test: new-repo flow — `--new-repo-path` creates the repo, scaffolds monorepo layout, ends with a worktree.

## 6. Schema validation

- [ ] On startup, the CLI should `json.loads` each line of `schemas/events.jsonl` and parse `schemas/transitions.yaml`/`schemas/run-metadata.yaml` to catch authoring errors early.
- [ ] Provide `agent-workbench doctor` that re-runs these checks plus verifies the workbench root layout.

## 7. Documentation polish (after the system works)

- [ ] Add a `QUICKSTART.md` walking through one full run end-to-end.
- [ ] Add `commands.md` generated from the CLI argparse definitions (not hand-written) so it stays in sync.

## 8. Out of scope for V1 (do not build yet)

- PR creation, merge automation, remote providers.
- Multi-repo runs.
- `project_subpath` and any global repo registry.
- Long-running daemon, job queue, or worker pool.
- Web UI.
