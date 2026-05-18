# Run Lifecycle

Every run moves through a small explicit state machine.

The current state lives in:

```text
runs/<run_id>/metadata.yaml
```

The append-only history lives in:

```text
runs/<run_id>/events.jsonl
```

Each meaningful transition requires evidence. Evidence is recorded in the `TransitionApplied` event and should also be reflected in `audit.md`.

## States

| Status | Meaning | May ask human questions? | May read code? |
|---|---|---:|---:|
| `draft` | Raw idea exists. Clarification may happen. | Yes | No |
| `shaping` | Convert raw input and answers into a code-blind brief. | No | No |
| `planning` | Inspect the target repo if applicable and create an implementation plan. | No | Yes |
| `ready` | Human approval gate before code changes begin. | No | No |
| `building` | Branch and worktree exist. Agent is implementing. | No | Yes |
| `validating` | Agent runs review, tests, QA, and records evidence. | No | Yes |
| `human_review` | Worktree and branch are ready for human inspection. | Yes, by human choice | Yes |
| `done` | Human accepted the work or closed it as complete. | No | No |
| `abandoned` | Run intentionally stopped. Artifacts are preserved. | No | No |

Terminal states:

```text
done
abandoned
```

Terminal states cannot transition further. Reopening work means creating a new run or bouncing from `human_review` before accepting.

## Canonical flow

```text
draft
  -> shaping
  -> planning
  -> ready
  -> building
  -> validating
  -> human_review
  -> done
```

Bounce-back flow:

```text
human_review -> building
```

Abandon flow:

```text
any non-terminal -> abandoned
```

## Transition evidence

| From | To | Required evidence |
|---|---|---|
| `draft` | `shaping` | `raw_idea_path` |
| `shaping` | `planning` | `brief_path` |
| `planning` | `ready` | `plan_path`, `assumptions_path`, `decisions_path`, `preflight_path`, `repo_path`, `repo_name`, `worktree_name`, `branch_name` |
| `ready` | `building` | `approved_by`, `repo_path`, `repo_name`, `base_ref`, `branch_name`, `worktree_name`, `worktree_path`, `preflight_path` |
| `building` | `validating` | `implementation_summary_path`, `diff_summary_path` |
| `validating` | `human_review` | `review_report_path`, `qa_report_path`, `audit_path`, `handoff_path`, `branch_name`, `worktree_path` |
| `human_review` | `building` | `bounce_reason` |
| `human_review` | `done` | `accepted_by`, `completion_ref`, `audit_path` |
| any non-terminal | `abandoned` | `abandoned_reason` |

Evidence fields must be present and non-empty.

## Stage contracts

Every non-terminal stage has its own contract: what it reads, what it produces, what it must write before it can exit, and what it must not do.

The artifacts listed under **Produces** are required to advance to the next state. The transition engine rejects the transition if any required artifact is missing or empty.

---

### draft

| | |
|---|---|
| Owner | Human + intake agent |
| May read code? | No |
| May ask questions? | Yes |
| Next state | `shaping` |

**Reads**

- User input (raw idea pasted at run creation).

**Produces**

- `raw-idea.md` — the original user request, captured verbatim.
- `answers.md` *(optional)* — clarifying Q&A, only if the run asked questions.

**Rules**

- The only state in which the agent may ask the human clarifying questions.
- Good questions materially change scope, target repo, behavior, or acceptance criteria.
- Bad questions can be resolved by existing repo conventions or by recording a reasonable assumption.

**To exit → `shaping`**

- `raw_idea_path` must point at a non-empty `raw-idea.md`.

---

### shaping

| | |
|---|---|
| Owner | Shaping agent |
| May read code? | No |
| May ask questions? | No |
| Next state | `planning` |

**Reads**

- `raw-idea.md`
- `answers.md` *(if present)*

**Produces**

- `brief.md` — code-blind specification of the work.

**`brief.md` sections**

```text
Goal
User-facing behavior
Acceptance criteria
Non-goals
Good examples
Bad examples
Constraints
Assumptions
Suggested QA scenarios
```

**Rules**

- Shaping must not read the target repo.
- Shaping must not ask the human questions.
- If the idea is too broad to shape, the brief should identify a smaller first run (bootstrap, vertical slice, roadmap) rather than try to spec the full thing.

**To exit → `planning`**

- `brief_path` must point at a non-empty `brief.md`.

---

### planning

| | |
|---|---|
| Owner | Planning agent |
| May read code? | Yes |
| May ask questions? | No |
| Next state | `ready` |

**Reads**

- `brief.md`
- Target repo files (if applicable).

**Produces**

- `plan.md` — implementation plan grounded in the actual repo.
- `preflight.md` — confirms repo path, base ref, target branch name, target worktree name, and any blockers.
- `assumptions.md` — every assumption made instead of asking the human.
- `decisions.md` — design and implementation choices, with rationale and alternatives.

**`plan.md` sections**

```text
Current repo understanding
Relevant files
Proposed changes
Files likely to change
Data model changes
UI changes
Test plan
QA plan
Risks
Definition of done
```

**Rules**

- Planning may read code; planning may not ask the human questions.
- If planning finds ambiguity, it records an assumption and chooses the safest small implementation.
- If the task is too broad, planning should reduce scope to a useful first run.

**To exit → `ready`**

- `plan_path`, `preflight_path`, `assumptions_path`, `decisions_path` must all exist and be non-empty.
- `repo_path`, `repo_name`, `worktree_name`, `branch_name` must be set in metadata.

---

### ready

| | |
|---|---|
| Owner | Human |
| May read code? | N/A |
| May ask questions? | N/A |
| Next state | `building` |

**Reads**

- `brief.md`, `plan.md`, `preflight.md`, `assumptions.md`, `decisions.md`

**Produces**

- No new artifacts. This is a human approval gate.

**Rules**

- The branch and worktree do not exist yet — they are created on the `ready -> building` transition.
- The human reviews the plan and approves (or bounces back to `planning` by abandoning and starting over).

**To exit → `building`**

- `approved_by` must be set.
- Branch and worktree must be created or verified (the transition emits `WorktreeCreated`).
- `worktree_path` must be populated in metadata.

---

### building

| | |
|---|---|
| Owner | Building agent |
| May read code? | Yes |
| May ask questions? | No, unless hard-blocked |
| Next state | `validating` |

**Works inside**

```text
agent-workbench/worktrees/<repo_name>/<worktree_name>/
```

**Reads**

- `plan.md`, `brief.md`, `assumptions.md`, `decisions.md`
- The worktree.

**Produces**

- `implementation-summary.md` — what changed and why, mapped to acceptance criteria.
- `diff-summary.md` — high-level rundown of the diff (files changed, scope, callouts).

**`implementation-summary.md` sections**

```text
What changed
Files changed
Acceptance criteria coverage
Deviations from plan
Known issues
Commands run
```

**Rules**

- Follow `plan.md`.
- Keep scope bounded by `brief.md`.
- Record deviations explicitly.
- Do not modify the original checkout.
- Do not silently skip acceptance criteria.

**To exit → `validating`**

- `implementation_summary_path`, `diff_summary_path` must exist and be non-empty.

---

### validating

| | |
|---|---|
| Owner | Review + QA agents |
| May read code? | Yes |
| May ask questions? | No |
| Next state | `human_review` |

**Reads**

- The worktree and all preceding artifacts.

**Produces**

- `review.md` — adversarial self-review against the brief and plan.
- `qa/report.md` — QA results.
- `qa/commands.txt` — every command run, in order.
- `qa/artifacts/`, `qa/recordings/`, `qa/traces/` — supporting evidence captured during QA.
- `audit.md` — human-readable timeline rendered from `events.jsonl` + artifacts.
- `handoff.md` — what the human needs to know to start their review.

**`review.md` should answer**

```text
Did the implementation satisfy the brief?
Did it accidentally expand scope?
Are there fragile assumptions?
Are there missing tests?
Are there security, data loss, or migration risks?
What should the human review first?
```

**QA should run at least one of**

```text
unit tests
integration tests
lint / typecheck
Playwright (MCP or direct)
custom smoke scripts
```

**Rules**

- Validation is adversarial. The reviewer is not the builder.
- A failed command does not auto-abandon the run. The agent may repair, retry, or hand off with known issues — but the audit must say what happened.

**To exit → `human_review`**

- `review_report_path`, `qa_report_path`, `audit_path`, `handoff_path` must exist and be non-empty.
- `branch_name`, `worktree_path` must be set.

---

### human_review

| | |
|---|---|
| Owner | Human |
| May read code? | Yes (human decides) |
| May ask questions? | Yes (human decides) |
| Next states | `done`, `building`, `abandoned` |

**Reads**

- `handoff.md`, `audit.md`, `review.md`, `qa/report.md`, the branch and worktree.

**Produces**

- No required new artifacts. The human may add notes.

**Exits**

```text
complete -> done       (accepted)
bounce   -> building   (changes requested; requires bounce_reason)
abandon  -> abandoned  (stopped; requires abandoned_reason)
```

`human_review` is not `done`. It means the system has handed off local work for inspection.

---

### done (terminal)

| | |
|---|---|
| Owner | Human / system |
| Terminal? | Yes |

**Required evidence on entry**

- `accepted_by`
- `completion_ref`
- `audit_path`

For V1, completion evidence is local:

```text
completion_ref: local-branch:<branch_name>
```

Examples:

```text
local-branch:agent/add-login-form
accepted-local-worktree:/path/to/agent-workbench/worktrees/app/add-login-form
closed-without-merge:prototype accepted
```

---

### abandoned (terminal)

| | |
|---|---|
| Owner | Human / system |
| Terminal? | Yes |
| Reachable from | Any non-terminal state |

**Required evidence on entry**

- `abandoned_reason`

**Rules**

- Artifacts are preserved.
- Worktrees may be cleaned up later by an explicit command, but the run record stays.

## Scope classification

Each run may classify its scope in metadata:

```yaml
scope:
  kind: implementation
```

Allowed values:

```text
implementation
bootstrap
roadmap
research
repair
```

This field does not change the lifecycle. It only clarifies what the run is trying to accomplish.

Rules:

- Clear ideas may go directly to implementation after `ready`.
- Broad ideas should become a bootstrap, roadmap, or vertical slice.
- One run must still target one repo and one worktree.

## Transition rules

- Status changes must go through the transition engine.
- Manual metadata edits are not valid transitions.
- Each transition appends a `TransitionApplied` event.
- Missing evidence rejects the transition.
- Terminal states cannot transition.
- Run artifacts are never deleted by lifecycle transitions.
- Worktrees may be cleaned up later, but run records stay.
