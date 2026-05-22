# Plan — TODO §1: Automatic E2E testing

## Brief

Implement automatic E2E testing that drives a run from `new-run` to a
terminal state (`done` or `abandoned`) without human-in-the-loop. The
existing `test_integration.py` already does this in concept by hand-writing
canned artifacts inline. The TODO asks for two things on top of that:

1. A **`--stub-llm` env-var mode** (`AGENT_WORKBENCH_STUB_LLM=<fixture-dir>`)
   so the LLM-bearing subcommands (`shape`, `plan`, `validate`, `followups`)
   automatically copy canned artifacts in lieu of calling the model. Slash
   command bodies stay unchanged — the existing `--init` Bash step is where
   the stubbing fires.
2. A **fixtures tree** under `tests/fixtures/e2e/` so adding a new scenario
   is a matter of creating a new fixture directory and a small test method.

## Changes

- `agent-workbench-live/lib/stub_llm.py` — new module.
  `fixture_dir_from_env()` reads `AGENT_WORKBENCH_STUB_LLM` and returns a
  `pathlib.Path` or `None`. `materialize(run_dir, stage, fixture_dir)`
  copies the canned artifacts for a given stage (`shaping`, `planning`,
  `building`, `validating`, `followups`) from `fixture_dir/<stage>/` into
  the run directory at the locations the finalize-mode subcommands expect.

- Wire stub-llm into the four LLM-bearing CLI subcommands. In each `--init`
  path, after staging the template and applying the transition, if
  `fixture_dir_from_env()` returns a path, call `stub_llm.materialize(...)`.
  Subcommands touched: `cmd_shape.py`, `cmd_plan.py`, `cmd_validate.py`,
  `cmd_followups.py`. No new flag added to the CLI — env-var is the only
  knob, exactly as the TODO specifies.

- `agent-workbench-live/tests/fixtures/e2e/happy/` — canned artifacts for
  the happy-path scenario: `raw-idea.md`, `shaping/brief.md`,
  `planning/plan.md`, `building/build.md`, `validating/review.md`,
  `validating/qa/report.md`, `validating/HUMAN_REVIEW.md`,
  `followups/follow-ups.md`.

- `agent-workbench-live/tests/fixtures/e2e/bounce_pass1/` and `bounce_pass2/`
  — two fixture sets for the bounce scenario. Pass 1 ships
  `validating/review.md` with `## Decision\nrequest_changes` and a HR
  doc. Pass 2 ships passing artifacts. Driver swaps the env var between
  passes.

- `agent-workbench-live/tests/test_e2e.py` — new test module. Three classes:
  `TestE2EHappyPath`, `TestE2EBounceLoop`, `TestE2EAbandon`. Each
  subprocesses the CLI with `AGENT_WORKBENCH_STUB_LLM` set to the fixture
  dir; the test body issues `new-run`, then `shape --init`, `shape`,
  `plan --init`, `plan`, `start`, `validate --init`, `validate`,
  `followups`, `complete`. After each step it asserts state, expected
  stage-dir files, and event-log invariants.

- `agent-workbench-live/tests/README.md` — new file. How E2E works, how to
  add a scenario, how to run only the E2E suite.

## Tests

### Unit

- `lib/stub_llm.py` — small helper, covered end-to-end by the new
  E2E tests; no separate unit module.

### Manual

- Run the full test suite from the worktree:
  ```
  cd agent-workbench-live
  python -m unittest discover -s tests -p "test_*.py"
  ```
  Expected: 188 (current) + new E2E tests passing.

- Stub-LLM env-var smoke (outside CI):
  ```
  export AGENT_WORKBENCH_STUB_LLM=$PWD/tests/fixtures/e2e/happy
  agent-workbench new-run --repo-path /tmp/throwaway-repo --worktree-name smoke --idea-file ...
  agent-workbench shape <run-id> --init     # should materialize brief.md from fixture
  ```
