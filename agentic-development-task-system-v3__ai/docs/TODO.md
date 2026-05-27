# TODO

## 1. Add a `/build` slash command — close the building-stage curated-entry enforcement gap

`/shape`, `/plan`, `/validate`, `/followups` each have a slash command that wraps the corresponding stage's `--init` (curated-entry staging) and finalize (transition + evidence) steps. **Building is the only LLM-bearing stage with no slash command** — the building agent enters passively after `/start`, with no scripted prompt that says "read `build-context.md` first." That asymmetry has two costs that surfaced in the 2026-05-25 `generalize-stage-context-md` run:

1. **No deterministic enforcement point** for the `build-context.md` curated-entry contract. The rule "read `build-context.md` first; do NOT re-read `brief.md` / `plan.md` separately if it already covers what you need" lives in `AGENTS.md` § Session discipline and in `docs/lifecycle.md` § building. The `/validate` slash command, by contrast, embeds the same rule in its Step 2 — impossible to miss because every validate session reads its own slash-command body. The building stage's contract is currently convention-strength only; an agent that ignores it pays a cache cost but no enforcement triggers.
2. **No symmetric `--init` step for building.** Today `build-context.md` is written as a side effect of `cmd_start.py`'s `ready → building` transition. That conflates the worktree-creation step with the curated-context-staging step. A `/build --init` would let `build-context.md` be regenerated on demand — closing F-004 from the 2026-05-25 rebuild (bounce rebuilds don't go through `cmd_start.run`, so `_write_build_context_artifacts` never fires; the rebuild agent has no `build-context.md` and falls back to reading `change-request.md` instead, which is the right curated file for a bounce but is produced by a different code path).

### Background

The 2026-05-25 run that shipped `build-context.md` already laid most of the infrastructure (`lib/build_context.py` + `cmd_start._write_build_context_artifacts`), but explicitly out-of-scope'd the `/build` slash command. The decision then was DR-002: "There is no `/build` slash command at all (subagent investigation confirmed). The building stage is entered passively by the agent operating inside the worktree after `/start`. So `/start` is the only deterministic write point upstream of building." That call was correct at landing time — adding a new slash command would have scope-crept the run. Now that build-context.md exists and the asymmetry is real, the slash command is the natural follow-up.

### Proposed shape

Mirror `/validate.md`'s shape (it's the most analogous LLM-bearing-stage slash command — has both `--init` curated-context staging and a finalize):

```
agent-workbench build <run_id> --init   # re-renders build-context.md from current artifacts
agent-workbench build <run_id>          # finalize building: verify build.md, transition building -> validating
```

**`/build --init`:**
- Idempotent.
- Re-renders `build-context.md` by calling the existing `cmd_start._write_build_context_artifacts` (or its extracted public form — see below). No transition (the run is already in `building`).
- Use cases: fresh entry into the building stage (regenerate after a manual brief/plan edit); after a `/bounce` (closes F-004); recovery from a stale curated file.
- Failure mode: same convenience-artifact swallow as today — never blocks; emits a warning to stderr if the helper fails.

**`/build` (default mode):**
- Verifies `build.md` exists and is non-empty (today's `validate --init` enforces this; the new flow shifts the gate one step earlier).
- Sets `build.iterations` and `build.exit_reason` evidence in metadata (today `validate --init` defaults them if not set; the new flow has the builder set them explicitly).
- Emits `BuildingFinalized` (or whatever event ID fits) and transitions `building → validating`.
- The existing `validate --init` retains its current `building → validating` transition logic for backward compat, but documents that `/build` is the preferred path.

**`.claude/commands/build.md`:**
- Step 1: invoke `agent-workbench build <run_id> --init` (if status is `building`).
- Step 2: **"Read `runs/$RUN_ID/stages/4_building/build-context.md`. Do NOT re-read `brief.md`, `plan.md`, or `templates/build.md` separately if `build-context.md` already covers what you need."** (Exact mirror of `validate.md` step 2's language.)
- Step 3: implement the change in the worktree.
- Step 4: write `build.md` per the template (Implementation summary, Files changed, Acceptance criteria coverage, Deviations from plan, Known issues, Commands run, Documentation touched).
- Step 5: finalize via `agent-workbench build <run_id>` — transitions to `validating`.

### Tasks

- [ ] **Decide the relationship to `cmd_start._write_build_context_artifacts`.** Two options: (a) extract it to a public `lib.build_context.materialize_for_run(cfg, run_id, staged)` and have both `cmd_start.py` and the new `cmd_build.py` call it; (b) call the existing private helper from `cmd_start.py` via a small wrapper. Option (a) is cleaner and matches DR-002's stance on deterministic write points; option (b) is smaller. Pick (a) unless friction surfaces.
- [ ] **Build `lib/cli/cmd_build.py`.** Two modes (`--init` and default). Mode dispatch mirrors `cmd_followups.py`'s shape. Default mode validates evidence + transitions.
- [ ] **Update `schemas/transitions.yaml`** if `validate --init` no longer drives the `building → validating` transition exclusively (it must still work, but `/build` becomes the canonical path). Decide whether the evidence keys move (`implementation_summary_path` / `diff_summary_path` / `build_iterations` / `build_exit_reason` — today required by `validate --init`).
- [ ] **Update `cmd_validate.py` `--init`** so it's a no-op transition when the run is already in `validating` (idempotent), or remove its building → validating transition path entirely if `/build` covers it. Decide based on what backward compat costs vs. cleanliness.
- [ ] **Write `.claude/commands/build.md`** with the Step 2 language mirroring `validate.md`'s.
- [ ] **Wire `/build --init` into `cmd_bounce.py`.** A bounce that returns to `building` should regenerate `build-context.md` automatically (or the rebuild's first `/build --init` does it). Pick one; document.
- [ ] **Update `docs/lifecycle.md` § building** to point at the new slash command; update `agent-workbench-live/AGENTS.md` § Session discipline.
- [ ] **Update `tests/test_e2e.py::TestE2EHappyPath::test_happy_path`** to drive through `/build --init` and `/build` finalize as new steps; assert the build-context.md regenerates on a bounce rebuild via `/build --init` (the F-004 close).
- [ ] **Unit tests for `cmd_build.py`** mirroring `tests/test_cmd_*` patterns: --init mode, default mode, status guards, evidence verification.

### Acceptance

- Every LLM-bearing stage has a slash command that prompts the agent to read its curated entry first. `/build` exists and is symmetric with `/shape` / `/plan` / `/validate` / `/followups`.
- A bounce rebuild can regenerate `build-context.md` via `/build --init` without re-running `/start` (closes F-004 from the 2026-05-25 `generalize-stage-context-md` run).
- `tests/test_e2e.py::TestE2EHappyPath::test_happy_path` drives through `/build --init` and `/build` finalize; passes deterministically.
- `validate --init` no longer needs to default `build_iterations` / `build_exit_reason` — `/build` finalize sets them explicitly. (Or `validate --init` keeps the defaulting for backward compat with pre-`/build` runs; pick one.)
- The Step 2 language in `.claude/commands/build.md` is identical in spirit to `validate.md`'s "Do NOT re-read X if `<stage>-context.md` already covers what you need."

### Non-goals

- **Behavioral enforcement of the read-only-curated-file contract.** The slash command nudges the agent; it does not technically restrict which files the agent's `Read` tool can open. Stronger enforcement (per-stage tool-policy allowlist, subagent isolation) is §9's territory, not this.
- **Renaming, merging, or restructuring other slash commands.** This is purely additive.
- **Building `plan-context.md`, `followups-context.md`, `shape-context.md`** — those are §3 (the renumbered "Generalize the `*-context.md` cross-stage contract" follow-up).
- **Subagent-based building.** Routing the builder through an `Agent`-tool subagent fed only `build-context.md` would be a stronger enforcement story; that's a separate design conversation (would touch §8 publishing-stage subagent pattern).
- **Tool-policy file at building stage.** §9 work; out of scope here.

### Origin

Surfaced 2026-05-27 in conversation immediately after `/complete`-ing the run that landed `build-context.md` (2026-05-25-generalize-stage-context-md). The asymmetry — every other LLM-bearing stage has a slash command except building — became visible the moment build-context.md existed, because the question "how does the building agent know to read it first?" had no satisfying answer at the code-execution level. The contract today is at convention-strength only (documented in AGENTS.md + lifecycle.md + the now-shipped build-context.md's own Rules block), not at instruction-presentation-strength like `/validate.md` step 2. F-004 from the same run's review.md flagged the bounce-rebuild gap separately; both close together with the `/build --init` mode.

---

## 2. Investigate the handoff-rendering failure cluster (HUMAN_REVIEW.md + stop banner)

### Symptom

The `human_review` handoff is supposed to give a reviewer a faithful, code-derived summary of what the run actually did. In practice, multiple recent runs produce handoffs whose `## Summary of changes` section is either fabricated (literal example bullets from a template comment) or hollow (parent headers with no detail). The stop banner that the agent reads after the handoff lands inherits these problems and amplifies them.

Two concrete examples on disk to investigate:

**Example A — fabricated bullets from template comment.** Run `2026-05-26-schema-level-validation-for-metadata`. HUMAN_REVIEW.md's `## Summary of changes` reads:

```
## Summary of changes

- 2 doc(s) touched:
  - `README.md — added a /hello endpoint example`
  - `docs/api.md — documented the new response schema`

→ Full diff: /Users/timothy.shee/GitHub/LOCAL_worktrees/new-tech-monorepo/agent-workbench-live/worktrees/agentic-development-task-system-v3-ai/20260526__schema-level-validation-for-metadata/agentic-development-task-system-v3__ai/agent-workbench-live/runs/2026-05-26-schema-level-validation-for-metadata/stages/4_building/build.md
```

Neither `README.md` nor `docs/api.md` was actually touched by this run. The build.md file at the path the handoff points to is byte-for-byte identical to `templates/build.md` — the builder wrote nothing into it. The two phantom bullets are the literal example lines that live *inside* an HTML comment under the `## Documentation touched` section of the template. `lib/human_review.py`'s `_section` + `_bullet_items` pair walks the section body for `- ` lines without stripping `<!-- -->` framing, so the examples get parsed as if they were real entries.

**Example B — hollow parent headers in the stop banner.** Run `2026-05-26-board-freshness-across-worktrees`. The stop banner printed after the `followups → human_review` transition shows:

```
Review:
  HUMAN_REVIEW.md: /Users/timothy.shee/GitHub/LOCAL_worktrees/new-tech-monorepo/agent-workbench-live/worktrees/agentic-development-task-system-v3-ai/20260526__board-freshness-across-worktrees/agentic-development-task-system-v3__ai/agent-workbench-live/runs/2026-05-26-board-freshness-across-worktrees/HUMAN_REVIEW.md

Summary of changes (≤3 bullets):
  - 5 file(s) touched:
  - 1 doc(s) touched:

Summary of testing (≤2 sentences, or "None recorded."):
  Unit tests passed; no known issues.
```

The two parent bullets end in colons with nothing after them. The detail *does* exist in HUMAN_REVIEW.md (per-file nested rows under each header — 500+ character bullets describing each touched file). But `lib/cli/_stop_banner.py`'s `_render_summary_bullets` deliberately drops nested `  - ` rows ("Top-level bullets only — no leading whitespace before the dash."). The result is structurally correct but reads as broken because the surviving headers were never meant to stand alone.

### Three observed failure modes

These came out of the conversation that surfaced this TODO; they may or may not be the full set.

1. **HTML-comment leakage in `lib/human_review.py`.** `_extract_build_summary` calls `_section` then `_bullet_items` on `## Documentation touched` (and would do the same on `## Files changed` if its template comment ever contained `- ` lines). Neither function strips `<!-- ... -->` blocks. Any `- ` line inside a comment is parsed as a real bullet. Affects `## Summary of changes` in HUMAN_REVIEW.md.

2. **Silent template fallback at `cmd_validate.py:290-298`.** `/validate --init` requires `build.md` to exist at the run root before the building→validating transition; if it's absent, the code stages `templates/build.md` and proceeds. The transition itself only checks file existence, not content (per the `("implementation_summary_path", "build.md", "building", "build.md")` row at `lib/lifecycle.py:152`). A builder that never wrote build.md is indistinguishable from one that did — until the unfilled template starts feeding bug 1 downstream.

3. **Stop-banner extractor drops the only level that has detail.** `_render_summary_bullets` in `lib/cli/_stop_banner.py` extracts column-0 `- ` bullets from HUMAN_REVIEW.md's `## Summary of changes`. The human_review renderer's convention for "files changed" is `- N file(s) touched:` as a parent + `  - <path>` rows as children. The banner extractor sees the parent, drops the children, and renders headers with empty colons.

### Tasks (investigation only — no fixes in this TODO)

- [ ] **Map all sites where text-shape parsing meets template-shaped input.** Grep for `_section`, `_bullet_items`, `## ` literal matching, anything that consumes `build.md` / `HUMAN_REVIEW.md` / `qa/report.md`. Each consumer should be examined for: does it assume content was written? Does it strip HTML comments? Does it understand the nested-bullet convention the producer uses? Write the findings as a table (file:line, what it reads, what assumption it makes, whether that assumption is safe today).
- [ ] **Audit `runs/` for how often the silent template fallback fires.** For each run with a `stages/4_building/build.md`, diff it against `templates/build.md`. Count how many are byte-identical (= builder wrote nothing) vs. partially filled vs. fully filled. The ratio tells us how systemic the unfilled-template handoff is.
- [ ] **Audit HUMAN_REVIEW.md across recent runs** for phantom example bullets, hollow header rows, or any other text that looks templated. Map each instance back to which producer/consumer pair produced it. The two examples above are a starting set; there may be more failure modes (e.g. `Manual testing performed` section, `Run timeline` empty rows).
- [ ] **Re-read the producer↔consumer contract** between the builder's `build.md`, the validate-init template fallback, the `human_review` renderer, the stop-banner builder, and the templates themselves. Specifically: is the right contract "the renderer parses build.md and templates are inert decoration," or "the builder writes structured fields the renderer consumes by name"? Today's mix of template HTML comments + free-form markdown + regex extraction is the weakest of both worlds.
- [ ] **Decide whether the broader pattern is the bug, not the individual sites.** Three different functions are each independently permissive. The conversation that surfaced this TODO suggested "common thread: shallow text-shape parsing without understanding semantics — comments are content, nested bullets are noise, an existing template file means done." That framing is worth pressure-testing: is there a single producer-side change (e.g. structured frontmatter in build.md, or a `build.json` sibling) that obsoletes all three consumer-side workarounds at once?

### Acceptance

- A written analysis (1–2 pages) that identifies every site involved in the handoff-rendering chain, names each failure mode observed, and proposes one or more candidate fix strategies (single-site patches vs. contract redesign vs. validation upstream).
- The analysis explicitly answers: should we strip HTML comments at the parsing layer (cheap, narrow), reject unfilled templates at `/validate --init` (changes lifecycle), restructure build.md to carry machine-readable fields (largest change), or some combination?
- A go/no-go recommendation for each candidate, with the smallest change that closes the example-A and example-B regressions called out as the minimum bar.

### Non-goals

Implementing any of the fixes. This TODO is the investigation; the fix(es) get their own TODO entry once the analysis lands and the user picks a direction. Re-running prior runs whose handoffs are already wrong — those are historical artifacts, not blockers.

### Origin

Surfaced 2026-05-26 while inspecting two recent runs' HUMAN_REVIEW.md and stop-banner output. The user noticed `## Summary of changes` was either fabricated (example A) or hollow (example B) and pushed back that "looks to me there is a larger issue at play." Three distinct bugs were identified in the same conversation, but the user asked to investigate thoroughly before designing solutions rather than patching each in isolation — the suspicion is that the right fix is at the contract level, not the regex level.

---

## 3. Generalize the `*-context.md` cross-stage contract (cont'd — `plan-context.md`, `followups-context.md`, `shape-context.md`)

The 2026-05-25 `generalize-stage-context-md` run shipped `build-context.md` (the highest-leverage of the four siblings) but explicitly deferred the other three to follow-up runs. This section tracks those follow-ups. The original framing from the 2026-05-25 brief still holds; only `build-context.md` and its wiring are removed from the task list.

The leverage is twofold:

1. **Cache footprint.** File reads in the master session stick in the prefix forever. Today the builder typically reads `brief.md` + `plan.md` + occasional `decisions.md` lookups; the reviewer (without the curated context) would read all of those plus the QA report plus the build summary. Each is a permanent prefix cost. One curated file per stage collapses that into a single read.
2. **Subagent-readiness.** A self-contained `<stage>-context.md` is the natural input for an Agent-tool subagent — the master spawns the subagent with that one file as context, the subagent's reads don't pollute the master's prefix, the master gets back structured findings. This is the same pattern the existing `Explore` rule uses; the cross-stage contract makes it the default shape for every LLM-bearing stage. The pre-PR adversarial reviewer (§8 `publishing` stage) depends on this — `validate-context.md` and `build-context.md` are already shaped right, but `plan-context.md` would need to exist before the subagent pattern can extend to the planning stage.

### What each remaining file contains

**`shape-context.md`** (written by `shape --init`)
- Original raw idea (verbatim from `raw-idea.md`)
- Answers from `answers.md` if present
- `brief.md` template skeleton inlined with one-line section descriptions
- The two shaping rules: no code reading, no questions

This one is thinnest — shaping has the least prior context to filter. The win is mostly inlining the template so the agent doesn't context-switch into `templates/`.

**`plan-context.md`** (written by `plan --init`)
- Full `brief.md` (small, load-bearing)
- Repo map: top-level dirs, detected languages, build/test commands from `agent-workbench.yaml` policies or inferred from the worktree
- `brief.md`'s "Files likely to change" lifted inline (the planner should validate or refute this)
- `plan.md` template skeleton with section descriptions
- Rules reminder: may read code, may not ask questions, record assumptions

**`build-context.md`** — shipped 2026-05-25 in run `2026-05-25-generalize-stage-context-md` (merge commit `c075b0c`). Lifts brief's Acceptance criteria + Non-goals, plan's Proposed changes + Files likely to change + Test plan + Definition of done, all DR/ASM blocks, worktree metadata, and the build.md template skeleton.

**`validate-context.md`** — already existed before 2026-05-25. This is the design template.

**`followups-context.md`** (written by `followups --init`)
- Brief's Non-goals (frequent source of follow-up candidates)
- Plan's Risks section
- Review's Decision + findings
- QA's Known issues
- Build's Deviations from plan
- `follow-ups.md` schema (category enum, frontmatter rules)
- Rules reminder: read-only, 1–5 entries or `no_followups` sentinel

### Tasks

- [x] Build `build-context.md` first — highest leverage, lowest risk. **Shipped 2026-05-25** in run `2026-05-25-generalize-stage-context-md` (merge `c075b0c`).
- [ ] Build `plan-context.md` next. Will require some new code: detecting repo languages and surfacing build/test commands from `agent-workbench.yaml` policies. Some of this overlap with `repo-map`-style work the planner does today; the goal is to make that deterministic and front-loaded.
- [ ] Build `followups-context.md`. Likely thin — most of what it needs is already in the staged artifacts; the deterministic builder is mostly a filter + headline rollup.
- [ ] Build `shape-context.md` last (or skip if the inlined-template gain doesn't justify the code).
- [ ] For each, update the corresponding `.claude/commands/*.md` so step 1 reads `<stage>-context.md` rather than the prior artifacts directly. Mirror the `validate.md` step 2 language: "Do NOT re-read X if `<stage>-context.md` already covers what you need." For building, this is the new `/build` slash command (§1).
- [ ] Document the contract in `docs/lifecycle.md` — add a `*-context.md` row to each remaining stage's table, sibling to "Reads" and "Produces." (Building stage is already documented; the others follow.)
- [ ] Each new `<stage>-context.md` builder gets unit tests that mirror `tests/test_build_context.py`'s shape (or `tests/test_validate_context_build.py`'s — both work) — synthetic prior artifacts → assert the generated context has the expected sections.

### Acceptance

- Every LLM-bearing stage (`shape`, `plan`, `build`, `validate`, `followups`) has a `<stage>-context.md` generated by `--init` before the agent reads anything. Building is done; three remain.
- A spot-check of three runs after the change shows the master session's prefix during each stage growing primarily from the curated file plus the worktree code the agent actively edits — not from re-reads of prior artifacts.

### Non-goals

Changing the artifact contents themselves (brief/plan/build/review keep their current sections); merging stages or changing the lifecycle; replacing template-driven artifact authoring with anything generative; building a `repo-map.md` artifact separate from `plan-context.md`'s repo-map section (keep it inline for now); shipping `/build` (that's §1's territory now).

### Origin

Surfaced 2026-05-25 in a design conversation comparing agent-workbench to a proposed planner/implementer/reviewer/PR-writer system. The proposed system's "shared durable context, not many independent workers" framing matched what `validate-context.md` already does — but agent-workbench only built that pattern for the validate boundary. Generalizing is straightforward and the cache-discipline payoff is concrete. Build-context.md shipped 2026-05-25 (merge `c075b0c`); the remaining three siblings stay TODO. Renumbered to §3 on 2026-05-27 when `/build` slash command was promoted to §1.

---

## 4. Canonicalize `repo_name` so the same repo always gets one worktree parent dir

### Symptom

`make_worktree_path` composes `<worktrees_dir>/<repo_name>/<YYYYMMDD>__<slug>`. `repo_name` is `slugify(basename(--repo-path))` (`lib/cli/cmd_new_run.py:54` → `lib/run_ids.py:52-54`). Three valid ways to point at the *same* monorepo today produce three different second-level dirs:

| `--repo-path` value | derived `repo_name` |
|---|---|
| `.../new-tech-monorepo` | `new-tech-monorepo` |
| `.../new-tech-monorepo/agentic-development-task-system-v3__ai` | `agentic-development-task-system-v3-ai` |
| `.../new-tech-monorepo/agentic-development-task-system-v3__ai/agent-workbench-live` | `agent-workbench-live` |

All three are the same git repo (same `git rev-parse --show-toplevel`). The worktree parent dir disagrees because the CLI never asks git "what is this repo's real root?" — it just slugifies the path the user typed. Anyone running `/new-run` from a different cwd, or invoking `agent-workbench new-run` against a subpath, opens a new top-level dir under `worktrees/`. The intent of `paths.worktrees_dir` is one normalized location per repo; the implementation only normalizes the root, not the per-repo namespace under it.

### Confirmed root cause

`derive_repo_name(repo_path.name)` in `cmd_new_run.py:54` takes the basename of whatever path was passed, never the repo toplevel. There's a `--repo-name` override (`naming.duplicate_repo_basename_strategy: require_repo_name_override` triggers it only on basename collision), but no automatic canonicalization. The `agent-workbench-live/.claude/commands/new-run.md` slash command just shells out to `agent-workbench new-run --repo-path <whatever>`; it inherits the same gap.

The current behavior is also what produced the 578 orphan `aw-e2e-repo-*`/`aw-repo-*`/`aw-self-mod-*`/`aw-snap-repo-*` directories before this cleanup landed — pytest fixtures `mkdtemp` source repos in `/var/folders/...` and the CLI obediently writes their worktrees under the *real* `worktrees_dir`, leaving headless shells when the tmpdir is wiped. Canonicalizing by toplevel won't fix the test-detritus problem (the tests still point `--repo-path` at distinct tmp repos), but it does fix the same-repo-different-cwd case, and it makes the test-fixture fix (route their worktrees into the tmpdir via `AGENT_WORKBENCH_ROOT` or a `paths.worktrees_dir` override) more obviously correct.

### Tasks

- [ ] **Resolve the repo to its git toplevel before deriving `repo_name`.** In `cmd_new_run.py`, after `repo_path = args.repo_path.resolve()`, run `git -C <path> rev-parse --show-toplevel` (already available via `lib/repos.py` — add a thin wrapper if not). Use the toplevel's basename as input to `derive_repo_name`. Fall back to the old behavior if the path isn't inside a git repo (i.e. `new-repo` mode, where the repo doesn't exist yet).
- [ ] **Honor `--repo-name` unchanged.** The explicit override path stays exactly as today; it's the only escape hatch for users who really do want a second namespace for the same repo (e.g. testing two branches in parallel). Canonicalization only kicks in when `--repo-name` is not passed.
- [ ] **Optional: detect "same toplevel, different existing `repo_name`" and warn.** If the canonical `repo_name` is `foo` but `<worktrees_dir>/foo/` doesn't exist and `<worktrees_dir>/foo-subpath/` does (i.e. a prior run from a subpath created a different parent), print a one-line warning at `new-run` time so the user notices the drift. Don't auto-merge — the existing dir might genuinely belong to a different intent.
- [ ] **Add a test in `tests/test_run_ids.py` (or wherever `derive_repo_name` is covered) that exercises the canonicalization.** Synthetic repo at `/tmp/foo/`; passing `--repo-path /tmp/foo/sub/dir` derives `repo_name=foo`, not `dir`. Make sure the `--repo-name` override still wins.
- [ ] **Document the rule in `agent-workbench-live/.claude/commands/new-run.md` and `lib/run_ids.py` module docstring.** "`repo_name` defaults to the slugified basename of the *git toplevel*, not the path you typed. Use `--repo-name` to override."

### Acceptance

- `agent-workbench new-run --repo-path .../new-tech-monorepo/agentic-development-task-system-v3__ai/agent-workbench-live …` and `agent-workbench new-run --repo-path .../new-tech-monorepo …` produce worktrees under the **same** second-level dir under `worktrees/`.
- `--repo-name foo` still wins unconditionally.
- New repos (`--new-repo-path`) keep working — toplevel resolution skipped before init, then the new repo's own basename is used.
- A test demonstrates the canonical behavior and would fail under today's `cmd_new_run.py:54`.

### Non-goals

Re-homing the 578 orphan e2e/snap/self-mod directories (those are a separate test-hygiene issue — the e2e fixtures should set `AGENT_WORKBENCH_ROOT` or override `paths.worktrees_dir` to a tmpdir, not depend on canonical naming). Renaming or merging existing pre-canonicalization worktree dirs on disk — that's a migration script, not a behavior change. Cross-machine path canonicalization (`/Users/x` vs `/home/x` symlinks etc.) — out of scope; we canonicalize via `git rev-parse`, not by string-matching.

### Origin

Surfaced 2026-05-26 while auditing the worktree list in this repo. Two real worktrees existed for the same monorepo under different `repo_name` parents (`agent-workbench-live/` vs `agentic-development-task-system-v3-ai/` vs `new-tech-monorepo/`) purely because of which subpath was passed to `--repo-path` at `/new-run` time. The user pushed back: paths "look all over the place, but they SHOULD be normalized. Different ways of creating like claude commands vs cli commands should make the same result." Slash commands and the CLI already share one code path; the gap is that the shared path doesn't canonicalize the input. This TODO closes that.

---

## 5. Schema-level validation for `metadata.yaml` on load

`lib/metadata.py:_validate` enforces top-level keys + the status enum only. `schemas/run-metadata.yaml` is descriptive — `metadata.load()` doesn't read it. Typos like `bse_ref` instead of `base_ref` load silently, surface later as missing-field crashes or wrong-data renders. As fields proliferate (`base_ref_sha`, `target.worktree.branch_name`, the `build:` block, the new `completion:` shape), the surface area for silent drift grows.

- [ ] Add a lightweight YAML-schema validator (or hand-roll typed accessors that raise on missing-or-mistyped) that walks `target.repo`, `target.worktree`, `validation`, `completion`, `build` and enforces field types + enum values on load.
- [ ] Surface mismatches as warnings by default; error behind a strict mode toggled in `agent-workbench.yaml`'s policies block.
- [ ] Keep `artifacts` and `scope` un-validated for this pass — they're free-form by design.
- [ ] Update `schemas/run-metadata.yaml` to be load-bearing rather than descriptive; document the field-type contract in `lib/metadata.py`'s module docstring.

### Acceptance

- A `metadata.yaml` with a typo'd top-level key under `target.repo` produces a warning at load time and an error under strict mode.
- Existing `runs/` directories load without warnings (no false positives on real data).
- `tests/test_metadata.py` covers at least: missing required field, mistyped scalar, enum violation, additive backward compat (unknown extra key tolerated under default mode).

---

## 6. Test-coverage gaps

Six gaps that have shown up twice or more across follow-ups since 2026-05-24. Grouped because they all share the same shape: a code path that's verified by code-reading or by tmp-dir structural assertions, but doesn't have a runtime drive-and-assert.

- [ ] **Full self-modifying lifecycle E2E.** `tests/test_self_modifying.py` covers `new-run` only (`test_new_run_creates_worktree_and_clean_master`). Add a test that drives `shape → plan → start → validate → complete` end-to-end on a synthetic self-modifying workbench; assert master's `git status --porcelain` is clean of `runs/` entries at every step and that the final merge commit contains the run dir at the worktree-side path. Reuse `_make_self_modifying_workbench` from the existing class.
- [ ] **Flat-layout E2E fixture.** `cmd_validate.py`'s flat path (`validating → human_review` directly) is the only one of the five banner sites without runtime coverage. Add `tests/fixtures/flat_happy/` (or similar) and a test method mirroring `test_happy_path` minus the followups stage. Asserts `STOP.` appears after `validate` and not after `validate --init`.
- [ ] **No-banner-on-abort runtime test for `cmd_complete`.** The existing `TestE2ECompleteMerge::test_merge_conflict_aborts_and_stays_in_human_review` checks status + events but does not assert `STOP.` is absent from stdout. Add the assertion (or a sibling test) so a future refactor that moves the banner above the failure paths fails loudly.
- [ ] **Direct unit tests for `lib/repos.py:stage_and_commit_run_dir` and `archive_tree_to_path`.** Only exercised via `cmd_complete` / `cmd_abandon` integration today. The `--strip-components` count in `archive_tree_to_path` depends on the source path's segment count and would benefit from a focused fixture (2-segment vs. 4-segment source paths).
- [ ] **Snapshot test for the full `human_review` stop banner.** Today the structured body is checked by `TestFullBanner` structural assertions + E2E `assertIn` substring checks; wording drift in the body (e.g. "auto-merges worktree branch into parent" → "merges into parent") would pass. Reuse the `_normalize`-style helper from `tests/test_human_review.py` (collapse `<TMP>`, `<TEST_REPO>`, `<HH:MM:SS>`, `<RUN_ROOT>`) and add two fixture-driven snapshots — one for the happy path, one for bounce-pass2 — under `tests/snapshots/stop_banner_human_review_{happy,bounce_pass2}.expected.txt`.
- [ ] **`_write_validate_context_artifacts` error-path coverage.** `cmd_validate.py:82-84` wraps the whole generator in `try: ... except Exception: pass`. The convenience-artifacts-must-not-break-the-transition intent is right, but the catch silences any bug in the generator. Add: (a) one test that monkey-patches `validate_context.build` to raise and asserts the transition still succeeds AND that the file is NOT written (proving the catch fired), (b) one test that constructs an unparseable `build.md` and asserts the generator produces a sentinel-fallback file rather than crashing. Optional: log the swallowed exception to `events.jsonl`.

### Acceptance

- All six gaps closed; suite count rises by the corresponding number of cases (rough estimate: +10 to +15 tests).
- Each new test would fail under today's behavior if the relevant code were reverted (verify by spot-check).

---

## 7. Subagent cost measurement — verify `metrics.jsonl` captures subagent token spend

`lib/metrics/writer.record_run_metrics` writes `metrics.jsonl` at the validate / followups / abandon boundaries. The intent is to attribute token spend to the run. The open question: when a stage spawns a Claude Code Agent-tool subagent (an `Explore` for read-heavy lookup, a `Plan` for design, a `general-purpose` for fan-out), **is the subagent's token spend captured in `metrics.jsonl`, or is only the master session's spend recorded?**

This isn't a correctness concern about the agent's behavior — subagents should keep being spawned, the architecture says they should, and they're how the workbench keeps the master session's prefix bounded (see AGENTS.md "Subagent-first read strategy"). It's an accounting concern: if subagent spend isn't attributed to the run, then any run that fans out heavily looks artificially cheap, and cross-run comparisons (which the board surfaces) are misleading.

### Tasks

- [ ] **Read `lib/metrics/writer.py` + `lib/metrics/buckets.py` + the bucket sources to determine what counts as "input/output tokens" for a run.** The relevant question: does the underlying telemetry source (whatever the writer pulls from — `claude-code session metrics`, the Anthropic API ledger, something else?) include nested-Agent-tool calls in the parent session's totals, or are they tracked separately?
- [ ] **Write a synthetic run that explicitly spawns N Agent-tool subagents from `/validate` and compare the resulting `metrics.jsonl` against the master-session-only baseline.** If the subagent spend is invisible, the delta will be small / zero; if it's captured, it'll match the subagents' individual spend.
- [ ] **If subagent spend is NOT captured: extend the writer.** This may require the writer to read from a more comprehensive source, or to walk subagent IDs and sum them. Implementation depends entirely on the telemetry source's shape — investigate first, design after.
- [ ] **If subagent spend IS captured but not labeled: add a `subagent_spend` rollup to the metrics.** Even if the totals are correct, knowing "how much of this run's spend was master vs. subagent" is useful diagnostic information for tuning the subagent-first strategy.
- [ ] **Document the contract.** Whatever the answer turns out to be, write it in `lib/metrics/writer.py`'s module docstring and link from `agent-workbench-live/AGENTS.md` § "Subagent discipline" so the next person isn't unsure what they're looking at.

### Acceptance

- A test or measurement script demonstrates whether subagent tokens are captured in `metrics.jsonl`. Answer is one of: (a) yes, captured in totals, (b) yes, captured separately, (c) no, missing.
- If (c), the writer is updated and the next test run shows the spend included. If (a) or (b), the docstring documents which case applies.
- The board's per-run spend display (if it shows a token total) is accurate within ~5% of the true total including subagent work.

### Non-goals

Throttling, capping, or denying subagent spawn — the policy is "spawn subagents when the work justifies it, and measure honestly." This TODO is purely measurement. Building a per-subagent breakdown in the audit (e.g. "this run spawned 3 Explore subagents, here's what each cost") would be nice but is a follow-on; the immediate concern is total-accuracy.

### Origin

Surfaced 2026-05-25 in a design conversation about subagent cost. The architecture explicitly permits subagent spawning and the AGENTS.md "subagent-first read strategy" actively encourages it for read-heavy work. The question of whether the resulting spend is captured in the workbench's own metrics is open — the writer code may or may not pull from a telemetry source that includes nested calls, and verifying this is a small but real piece of work. The concern is cross-run comparability: if fan-out runs look artificially cheap, the board's metrics column lies, and decisions about session boundaries (the validate-cut, the cache-discipline rules) get made against bad data.

---

## 8. GitHub PR delivery: `publishing` stage + minimal lifecycle fork

Today the workbench is built for personal-repo, single-author work. `done` means "human accepted + locally merged to parent branch" — `cmd_complete` checks out the parent and runs `git merge --no-ff` directly. That model collapses two things that are separate in a team workflow: author sign-off and team sign-off. For team work the workbench needs to model the PR-review world as first-class lifecycle states, not a slash-command bolt-on after `done`.

The user-stated workflow:

> I give a Linear ticket so things are implemented → Human Review → approved means PR is created and run is marked as Done. If PR gets comments, it can get reopened somehow.

The key requirement: **the human must see and approve the PR description before anything gets pushed**. PR descriptions are not a fire-and-forget concern — they are an LLM-bearing artifact with its own drafting stage. And `done` for team work cannot mean "auto-merged into master" — it means "PR merged on GitHub."

### Design — minimal fork at `human_review`

The delivery choice is **not** declared at `new-run` time. Forcing it that early couples a run's identity to a decision the author hasn't made yet — often you don't know if a change is PR-worthy until you've built it. Instead, the fork happens at the `human_review` terminal boundary, by which slash command the author invokes:

```text
human_review --(/complete)----> done             # local merge (today's behavior, unchanged)
human_review --(/publish-pr)--> publishing       # PR-flow entry
human_review --(/bounce)------> building         # rebuild (unchanged)
human_review --(/abandon)-----> abandoned        # (unchanged)

# PR-flow continuation:
publishing       --(/publish-pr)--> in_pr_review  # human-confirmed; pushes + opens PR
publishing       --(/bounce)------> human_review  # draft rejected; nothing pushed
in_pr_review     --(/complete)----> done          # one-shot `gh pr view` confirms PRMerged
in_pr_review     --(/bounce)------> building      # human-invoked; pulls comments to change-request.md
in_pr_review     --(/abandon)-----> abandoned     # local abandon; PR is orphaned (see hard parts)
in_pr_review     --(/closed)------> closed        # human marks PR was closed on GitHub
any non-terminal --(/abandon)-----> abandoned
```

`completion.delivery` (`local-merge` | `github-pr`) is set by whichever terminal command runs — it is recorded, not declared. Metadata grows `completion.pr_number` + `completion.pr_url` once `/publish-pr` succeeds.

### The new stages

**`publishing` — LLM-bearing, drafts the PR description**

The single purpose of this stage is to produce a high-quality PR description before anything is pushed. It is the GitHub-shaped sibling of `/handoff`. Reuses TODO §1's curated-context pattern: `publishing --init` writes `publishing-context.md` deterministically from prior artifacts; the LLM session reads only that file.

Reads (via `publishing-context.md`):
- `brief.md` — original intent, acceptance criteria, non-goals
- `plan.md` — decisions, files-changed, test plan
- `build.md` — what got built, deviations from plan
- `validate-context.md` — already curated for review purposes; reused here
- `review.md` — reviewer's findings + decision
- `HUMAN_REVIEW.md` — author's sign-off notes
- The diff (`git diff <base_ref_sha>..HEAD`)
- Linked Linear ticket if `target.linear_ticket` is set (via Linear MCP)

Writes:
- `stages/7_publishing/pr-draft.md` — title (line 1) + body (rest). This file becomes the PR description verbatim.
- `stages/7_publishing/pr-meta.yaml` — base branch, suggested reviewers, labels, linked Linear ticket URL, draft-vs-ready flag.

STOPs with a banner instructing the human to review `pr-draft.md`, edit it directly if needed, then run `/publish-pr` to push — or `/bounce` if the draft reveals the implementation itself is wrong.

The draft is the artifact you said you need: "I want and need to see exactly what's going to get pushed." `pr-draft.md` is what gets pushed.

**`/publish-pr` — the human-gated push**

A thin command, not a stage. Validates `pr-draft.md` is non-empty, then forks on `completion.pr_number`:
- **Not set (first publish):** pushes the branch, runs `gh pr create --title "$(head -1 pr-draft.md)" --body-file <(tail -n +2 pr-draft.md)`, captures the returned PR number/URL into `completion.pr_number` + `completion.pr_url`, transitions `publishing → in_pr_review`.
- **Already set (re-publish, body changed):** runs `gh pr edit <pr_number> --title ... --body-file ...`. No `gh pr create`.
- **Already set, body unchanged:** `git push` only. PR auto-updates via the new commits.

`gh` failures (auth expired, branch protection forbids, network) keep the run in `publishing`, emit a structured error event, and the STOP banner reprints with the specific failure + remediation. Human fixes the cause, reruns `/publish-pr`. No partial state — either the PR exists and we transition, or it doesn't and we don't.

**`in_pr_review` — passive holding state, no polling**

No background process. No agent activity. No `pr-sync` command. The board shows `PR #1234 (link)` and the row sits until the human invokes one of:
- `/complete <run_id>` — does a one-shot `gh pr view --json state,mergeCommitOid`. Asserts `state == MERGED`. Records `completion.merge_sha` from `mergeCommitOid`. Transitions to `done`. Refuses if not yet merged.
- `/bounce <run_id>` — pulls open PR comments at invocation time (single `gh api repos/<owner>/<repo>/pulls/<n>/comments`), populates `change-request.md` from the response, transitions to `building`. No background sync — comments are fetched on demand only.
- `/closed <run_id>` — human marks "team closed this PR without merging." Transitions to `closed`.
- `/abandon <run_id>` — author's call; transitions to `abandoned`. Leaves PR open on GitHub untouched (see hard parts).

**Re-entering `building` from `in_pr_review` (`change-request.md`)**

When `/bounce` pulls PR comments, it writes `change-request.md` to the new building stage's directory. This is the curated entry point (analog of `*-context.md` from TODO §1). Shape:

```markdown
# Change request — PR #1234 (round N)

## Reviewer threads
### thread 1 — src/exports/csv.py:147 (reviewer: alice)
> "This unconditionally loads all archived profiles into memory. Can we stream?"

### thread 2 — tests/test_exports.py:89 (reviewer: bob)
> "Missing explicit test for the false case."

## CI failures (if any)
- buildkite job xyz: pytest tests/test_exports.py::test_archived_filter — assertion failed (link)
```

The builder reads `change-request.md` first; `brief.md` and `plan.md` remain available if the comments warrant replanning. After `building`, the run flows back through `validating → human_review → /publish-pr` as normal — re-validate is the existing invariant, not optional. Because `/publish-pr` is deterministic on `pr_number`, the same PR gets updated (no new PR created).

**`closed` — new terminal state**

PR was closed without merge (declined, superseded, abandoned by team). Terminal. Distinct from `abandoned` because `abandoned` was the author's call; `closed` was the team's. Both preserve artifacts. Reached only by explicit human `/closed` invocation — the workbench never closes PRs itself.

### What `/complete` does in `github-pr` mode

`/complete` in `in_pr_review` is a verification-only command, not a merge. It runs `gh pr view --json state,mergeCommitOid` once, asserts `state == MERGED`, and records the SHA. No `git merge`, no `gh pr merge`. The human does the actual merge via GitHub UI or `gh pr merge` themselves; `/complete` just acknowledges it landed.

This preserves the workbench's "we don't talk to remotes for write operations on behalf of the agent" stance. The only `gh` writes anywhere in the lifecycle are `gh pr create` and `gh pr edit --body/--title`, both gated behind explicit human `/publish-pr` invocation.

### Hard parts worth flagging

1. **CI failures vs. reviewer comments are different change types.** Both end up in `change-request.md` when the human bounces, but CI failures are deterministic and a future automation could act on them autonomously; reviewer comments often need judgment. Tag `change-request.md`'s top-level type (`ci_only`, `reviewer_only`, `mixed`) so future automation has a hook. V1: tag the field, don't act on it.
2. **Stale PR state on `/abandon`.** Abandoning a run with an open PR orphans the PR on GitHub. The workbench does **not** close it — that would be an unsolicited write. `/abandon` records the orphan in metadata (`completion.pr_orphaned: true` plus the URL); the human decides whether to close it on GitHub themselves. The STOP banner surfaces the PR URL and reminds the human it's still open.
3. **Branch-name stability across bounces.** PRs anchor on branch names. Today the branch (`agent/<slug>`) stays stable across `human_review → building` bounces; the same invariant must hold across `in_pr_review → building` bounces or PR updates will fail.
4. **Multi-round comment state.** PR comments accumulate across rounds. `/bounce` pulling at invocation time gets the *current* snapshot from GitHub, including comments marked resolved. The `gh api` query should filter to unresolved threads (or annotate resolved ones) so the builder doesn't re-address already-resolved feedback. Heuristic: `is_resolved == false` from GraphQL `pullRequestReviewThreads`. V1 may take the simpler "all comments since last push timestamp" approach; revisit if it produces noisy `change-request.md` files.
5. **Re-publish body diffing.** When `publishing` re-runs after a CR cycle, the new `pr-draft.md` may be substantially different from the previous one (different rationale, different test coverage). The human is reading `pr-draft.md` fresh each cycle — the previous draft is archived under `archive/`. No automatic diffing; the human reads the current draft as they would the first one.

### Tasks

This will land across several runs. Discrete unit-of-work breakdown:

- [ ] Update `schemas/transitions.yaml` with the new states (`publishing`, `in_pr_review`, `closed`) and their transition evidence requirements. `publishing → in_pr_review` needs `pr_number`, `pr_url`, `branch_pushed_sha`. `in_pr_review → done` needs `merge_sha`. `in_pr_review → closed` needs `closed_by`.
- [ ] Add `completion.delivery`, `completion.pr_number`, `completion.pr_url`, `completion.merge_sha`, `completion.pr_orphaned` to `schemas/run-metadata.yaml`. (TODO §5 schema validation should land first or co-land to catch typos.) No new fields under `target` — the choice is made at terminal-command time.
- [ ] Build the `publishing` LLM-bearing slash command. `publishing --init` writes `publishing-context.md` deterministically from brief + plan + build + validate-context + review + HUMAN_REVIEW + diff + linked Linear ticket. The LLM session reads only `publishing-context.md` and writes `pr-draft.md` + `pr-meta.yaml`.
- [ ] Build `cmd_publish_pr.py` — validates `pr-draft.md` non-empty; forks on `completion.pr_number` (create vs. edit vs. push-only). Captures `pr_number`/`pr_url` on creation. On `gh` failure, keeps run in `publishing` and emits structured error event for the STOP banner.
- [ ] Update `cmd_complete.py` for `in_pr_review`-state runs: one-shot `gh pr view --json state,mergeCommitOid`, assert merged, record `merge_sha`, transition to `done`. Local-merge path (called from `human_review`) preserved unchanged.
- [ ] Update `cmd_bounce.py` to handle the `in_pr_review → building` path: pulls open PR comments via `gh api repos/<owner>/<repo>/pulls/<n>/comments`, writes `change-request.md` to the new building stage, with `change_request_type: ci_only | reviewer_only | mixed` annotation.
- [ ] Add `cmd_closed.py` — small command for human-invoked `in_pr_review → closed` transition.
- [ ] Update `cmd_abandon.py` to detect an open PR and record `completion.pr_orphaned: true` + URL in metadata. Does **not** call `gh pr close`. STOP banner mentions the orphaned PR.
- [ ] Board changes — surface `completion.pr_number` + URL on `publishing` / `in_pr_review` / `closed` rows. No CI/approval status (those are read on GitHub directly).
- [ ] Documentation — `architecture.md` § "Non-goals for V1" currently says "No PR creation." Update with the new contract: `gh pr create` + `gh pr edit --body/--title` are the only writes; everything else is read-only `gh pr view` / `gh api`. Update `docs/lifecycle.md` with the new states and the `human_review` fork.
- [ ] Tests — E2E coverage for happy path (`human_review → publishing → in_pr_review → done` via simulated `gh` binary), CR path (`in_pr_review → /bounce → building → ... → publishing` with `change-request.md` populated from fake `gh api` output), closed path, abandon-with-open-PR path. `local-merge` regression suite stays untouched.

### Acceptance

- From `human_review`, `/publish-pr` drafts `pr-draft.md`, STOPs; a second `/publish-pr` (after human review) pushes and creates the PR via `gh pr create`, transitions to `in_pr_review` with `completion.pr_number` + `completion.pr_url` recorded.
- `pr-draft.md`'s body cites: acceptance criteria from `brief.md`, the actual diff (files + LOC), the test plan from `plan.md`, and any deviations from `build.md`. Title is one line, ≤72 chars, imperative mood.
- After the PR is merged on GitHub, `/complete` does a one-shot `gh pr view`, records the merge SHA, and transitions to `done`. No `git merge` runs locally.
- `/bounce` from `in_pr_review` pulls open PR comments via `gh api`, writes a populated `change-request.md` with `change_request_type` tag, transitions to `building`. A subsequent `/publish-pr` updates the existing PR (via `gh pr edit`), does not create a new one.
- `/abandon` from `in_pr_review` records `completion.pr_orphaned: true` in metadata, leaves the PR open on GitHub, and the STOP banner surfaces the PR URL.
- The workbench never calls `gh pr comment`, `gh pr review`, `gh pr merge`, `gh pr close`, `gh pr edit --add-reviewer`. Only `gh pr create`, `gh pr edit --title/--body`, `gh pr view`, `gh api .../comments` (read-only).
- `local-merge` runs continue to work exactly as today — no regression in the `/complete`-from-`human_review` path.
- The board shows distinct rows for `publishing`, `in_pr_review`, `closed`.
- `architecture.md` and `docs/lifecycle.md` document the new states and the `human_review` fork.

### Non-goals

- **No PR comment writes by the workbench.** The agent never posts comments, never resolves threads, never requests reviewers. The human does all of those via GitHub UI or `gh` themselves.
- **No auto-merge.** Even when CI + reviews are green, the human runs `gh pr merge` or clicks the GitHub button. `/complete` only verifies and records.
- **No auto-close on `/abandon`.** Orphaned PRs are recorded but left open; the human decides their fate.
- **No background polling.** No `pr-sync`, no cron, no webhooks. State changes happen only when the human invokes a command.
- **No auto-assigning reviewers from CODEOWNERS.** `pr-meta.yaml` may *suggest* reviewers in the draft for human review, but `gh pr create` is invoked without `--reviewer` flags. Reviewers are added on GitHub manually.
- **Multi-PR runs.** One run still maps to one branch maps to one PR.
- **Cross-repo PRs / monorepo PR splits.** Out of scope until the multi-repo run model lands.
- **Merge-strategy configurability (squash/rebase/merge).** Whatever the GitHub repo's settings allow is what happens; the workbench is uninvolved.

### Origin

Surfaced 2026-05-25 by the user after I sketched a too-thin `/publish` slash command in a prior turn. Refined 2026-05-26: the original §7 had a per-run `target.delivery` field set at `new-run` time, an automated `pr-sync` poller, an adversarial-review subagent inside `publishing`, and `/abandon` prompting to close PRs. All four were cut. The delivery choice belongs at the terminal boundary, not the run's identity. There is no polling because re-reading the PR on GitHub is the human's job; the workbench only fetches comments when the human explicitly bounces. The adversarial pass was redundant with `/validate`'s standard review. And the workbench never writes PR state it wasn't explicitly asked to write — closing a PR on the user's behalf is exactly the kind of unsolicited remote action the architecture refuses.

---

## 9. Restrictive tool policy for the `publishing` stage only (relevant once §8 ships)

Today the workbench's safety story is filesystem-via-worktrees + evidence-gated transitions. There's no per-run tool bounding because there's no need — `local_only: true` in `agent-workbench.yaml` means no remote calls, the worktree confines git operations to one branch, and the agent's shell tool is the agent's-harness problem.

§8 punctures that **for one stage**. `cmd_publish_pr.py` runs `gh pr create` (pushes the branch, creates a PR against a real GitHub repo). `cmd_pr_sync.py` runs `gh pr view --json …` and `gh api repos/<owner>/<repo>/pulls/<n>/comments`. The architecture statement "Talk to GitHub or any remote API → Agent Workbench does NOT do this" becomes false during `publishing`. Blast radius for that stage grew from "the worktree" to "the user's GitHub credentials + every repo they can write to."

The narrow threat: an agent inside `publishing` could run `gh pr merge`, `gh repo delete`, `gh api` against an unrelated repo, or `git push --force` to an unrelated branch. Restricting that one stage is sufficient. Every other stage stays safe under the user's default Claude Code allowlist — `git` is worktree-bounded, test runners and file I/O are filesystem-bounded, none touch remotes, and the default allowlist doesn't include `gh` for them to misuse.

### Design — one stage, one policy

**`publishing`** runs under a restrictive allowlist written per run. Every other stage (`shaping`, `planning`, `building`, `validating`, `followups`) inherits the user's default Claude allowlist with no per-run override and no per-run policy file.

Why this works:

- **The threat surface is exactly one stage.** `publishing` is the only stage that legitimately needs `gh`. There's nothing for a per-stage policy to add for the others that the global allowlist isn't already doing — the default allowlist doesn't include `gh`, so non-publishing stages can't call it regardless.
- **`in_pr_review` doesn't need a policy.** Per §8 it's a passive wait state — no agent activity. `cmd_pr_sync.py` is invoked by the human (or cron), not by an LLM session. The workbench's CLI code is trusted code, not agent-emitted shell.
- **Symmetry with worktrees.** Worktrees are the filesystem bound; this is the remote bound. Both narrow and load-bearing, not blanket.

### What the `publishing` policy contains

A static YAML file the workbench writes per run at `publishing`-stage entry. Loaded by the harness; commands outside the list are refused.

```yaml
# stages/7_publishing/tool-policy.yaml — written by `/publishing --init` for pull-request runs
schema_version: 1
kind: tool_policy
stage: publishing

shell_allowlist:
  - gh pr view                       # read PR state
  - gh pr create                     # create the PR (the one mutating call this stage needs)
  - gh api repos/<owner>/<repo>/*    # scoped reads against the target repo only
  - git push origin <branch>         # push the branch this PR will open against
  - git diff
  - git log
  - git status

shell_denylist_explicit:
  - gh pr merge                      # workbench never auto-merges; human merges via gh / GitHub UI
  - gh pr close                      # closing happens via /abandon, not by the publishing agent
  - gh repo *                        # no repo-level mutations
  - git push --force*
```

`<owner>/<repo>` and `<branch>` are templated at policy-write time from the run's `target.repo` and worktree branch name — so a `publishing` agent for a run targeting `klaviyo/app` cannot `gh api` against `klaviyo/fender` even though the user's credentials cover both. This is the "per-run scope" piece: not a separate concept, just substitution into the allowlist patterns.

The explicit denylist exists for clarity even though the allowlist would already block these — `gh pr merge` and `git push --force` are foot-guns worth naming so a future loosening of the allowlist (e.g. adding `gh pr *`) can't accidentally permit them.

### Enforcement path

**Harness-mediated.** The workbench writes the policy file at stage entry; the Claude Code harness reads it via a settings.json hook (PreToolUse) and refuses tool calls outside the list. No new infrastructure beyond emitting the file.

If a future harness can't honor the policy file, the escalation is a wrapped `gh` on a stage-specific PATH — but this is YAGNI until a second harness shows up. For V1, Claude Code is the harness, and its hooks are sufficient.

This is **not** capability tokens (no crypto, no expiry, no issuance). Static file, loaded at stage entry, denying anything not listed. AppArmor-shaped, not OAuth-shaped.

### Tasks

- [ ] **Do nothing until §8 actually starts.** Sequential dependency. Pre-§8, no stage has a remote-mutating tool surface, so there's nothing to restrict. Adding policy infrastructure now would be premature.
- [ ] **When §8 starts: spec the policy file.** Settle the exact `shell_allowlist` for `publishing` once `cmd_publish_pr.py` is landing — the allowlist follows the commands the implementation actually needs, not the other way around. Document the contract (`shell_allowlist`, `shell_denylist_explicit`, templated `<owner>/<repo>`/`<branch>`) in `schemas/tool-policy.yaml`.
- [ ] **Wire the hook.** Claude Code's settings.json PreToolUse hook reads `stages/7_publishing/tool-policy.yaml` when the `/publishing` command starts and applies the allowlist for that session. Spike on `gh pr view` first to confirm the hook shape end-to-end before encoding the full list.
- [ ] **Add a `doctor` check.** `agent-workbench doctor` extends to scan a run's `events.jsonl` for any tool call emitted during `publishing` that isn't in that run's policy. Retrospective audit complements the preventative hook — if the hook misfires or a future harness ignores the file, doctor catches it.
- [ ] **Document the contract.** `agent-workbench-live/AGENTS.md` § "Publishing stage rules" names the policy and explains why this stage is special. Note in `architecture.md` that the workbench's safety bounds are now (1) worktrees for filesystem, (2) `publishing`-stage policy for remote — and that every other stage inherits the harness default.

### Acceptance

- `publishing` cannot run `gh pr merge`, `gh pr close`, `gh repo delete`, `gh api` against any repo other than `target.repo`, or `git push --force`. Attempts are refused by the hook and recorded by `doctor`.
- `publishing` CAN run `gh pr view`, `gh pr create`, scoped `gh api repos/<target.repo>/*`, and `git push origin <branch>`.
- Every other stage (`shaping`, `planning`, `building`, `validating`, `followups`) runs with no per-run policy file and inherits the user's default Claude allowlist — verified by `doctor` not flagging anything and by the absence of a `tool-policy.yaml` under those stage directories.
- `local-merge` runs never produce a policy file under any stage (no `publishing` stage exists for them).
- A run's policy file missing or malformed at `publishing` entry: `transitions.transition(... → publishing)` rejects with a clear error.

### Non-goals

Per-stage policy for stages other than `publishing` (the default Claude allowlist already covers them; adding per-run policy elsewhere is overhead with no threat to mitigate). Capability tokens (no crypto, no expiry). Sandboxing the agent's shell tool generally (worktree is sufficient bound for filesystem; `publishing` policy is sufficient bound for remote). OS-level network egress filtering (per-command policy, not a firewall). MCP-server-level policy (harness's problem). Wrapper scripts as primary enforcement (escalation only, if a future harness can't honor the file).

### Origin

Surfaced 2026-05-25 in a discussion of agent-workbench's safety mechanisms. The first draft proposed a full per-stage allowlist for every lifecycle state. Pushed back 2026-05-26: every stage except `publishing` is already safe under the default Claude allowlist (no `gh` in it, worktree-bounded `git`, filesystem-bounded I/O). The only stage that needs a policy is the one that punctures `local_only`, so the mechanism should be scoped to it. Net: one policy file at one stage boundary, not a per-stage matrix.

