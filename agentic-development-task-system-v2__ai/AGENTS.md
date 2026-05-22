# AGENTS.md

You are an AI agent (Claude Code, Codex, Cursor, anything similar) opening this repo to **work on the workbench itself** — fix bugs, ship features, refactor, write docs. This file tells you how to leave the project files in a coherent state when you finish.

If you are instead **driving a run** inside the workbench (`/shape`, `/plan`, `/validate`, …), the file you want is `agent-workbench-live/AGENTS.md` — that one is about lifecycle discipline. This one is about repo-level hygiene.

---

## The two-file contract

Every change that touches the actual infrastructure — `agent-workbench-live/`, the schemas, the slash commands, the CLI, the test suite, configuration — leaves two project files out of sync if you don't update them:

- `docs/TODO.md` — what's still to do. Sections are numbered. Each open item is a `- [ ]` bullet.
- `docs/LOG.md` — chronological diary of what happened. Sections are dated (`## YYYY-MM-DD`).

**When you ship infrastructure work, you MUST update both:**

1. **Delete the item from `docs/TODO.md`.** If a whole section (`## N. …`) is done, delete the section and renumber the sections that follow. Move a one-line ✅ summary up to the "Completed work" block at the top of the file. Include the commit SHA(s) and a one-line "what changed + why it mattered" so the summary is enough on its own — readers shouldn't have to dig through git log.
2. **Add a `docs/LOG.md` entry under today's date.** If today's date section doesn't exist yet, create it (`## YYYY-MM-DD`). Write 1-3 paragraphs of prose, not a bullet list of file paths. Cover: what shipped, why it mattered, the commit SHA(s), test counts before/after, and any surprises that came out of the work (especially anything a future reader would want to know that isn't obvious from the diff). Match the existing entries' tone — narrative, specific, mildly self-critical.

This is not optional. A TODO whose item is "done" but still rendered as `- [ ]` is misinformation. A LOG.md that skips a feature shipped today is amnesia. Both compound: the next session, looking at TODO.md to pick its next task, will work on something that's already done; the next session, looking at LOG.md to understand "how did we get here", will think a whole feature never happened.

## What counts as "infrastructure work"

If the change touches any of these, the contract applies:

- `agent-workbench-live/` — anything under it: `bin/`, `lib/`, `tests/`, `templates/`, `schemas/`, `.claude/commands/`, `requirements-board.txt`, `AGENTS.md`, `README.md`.
- `docs/` — `lifecycle.md`, `LOG.md`, `TODO.md`, `architecture.md` (and any new doc).
- Repo-level scaffolding — this file, top-level `README.md`, root-level scripts.

What does NOT trigger the contract:

- Editing artifacts inside a specific `runs/<id>/` directory (those are run history, not infrastructure).
- Scratch files like `plan.md` at the repo root (workflow ephemera; the convention is they ride alongside feature commits but aren't required to).
- A pure dogfood run that doesn't change any code — the `runs/<id>/` tree gets committed but TODO + LOG don't need entries because nothing about the workbench itself changed.

When in doubt, ask: *would a future session need to know this happened to do their work?* If yes, log it.

## Order of operations

Do this in the same session, ideally in one commit (or two if the code change and the docs are large):

1. Make the code change. Land tests. Run the suite.
2. Update `docs/TODO.md` — strike through / delete completed bullets; collapse finished sections into the "Completed work" summary; renumber if needed; update the "Order reflects priority" line near the top.
3. Update `docs/LOG.md` — add the dated entry. Include commit SHAs (you'll have them from `git log` after the code commit; if you're committing docs together, write the message + SHA in afterwards or amend).
4. Commit.

If the code-side commit and the docs-side commit are separate, the docs commit comes immediately after — never let a session end with the docs un-reconciled.

## Examples to imitate

- `docs/LOG.md`'s 2026-05-20 entry — four-bullet structure breaking down a multi-pass feature, naming commit SHAs, ending with the test count and the next item's name.
- `docs/LOG.md`'s 2026-05-22 entry — narrative paragraphs for two TODO sections shipped same day, including a "what we learned" beat about regression-test discipline. That beat exists because a real bug surfaced from dogfood and a follow-up review caught that no regression test had been added; the lesson is now part of the project's institutional memory instead of evaporating.
- `docs/TODO.md`'s "Completed work" block — one line per finished section, with commit SHA(s) and a short summary. The full detail lives in LOG.md; the TODO summary just confirms it's done and points at the SHAs.

## When you're tempted to skip this

You might not be. Two failure modes I've seen:

- **"The diff speaks for itself."** It doesn't. Six weeks from now, nobody is reading the diff — they're reading LOG.md. Make it findable.
- **"This was a tiny fix, not worth a LOG entry."** Then it's a one-sentence LOG entry. The cost of the sentence is cheap; the cost of next session re-discovering the same thing because there was no record is not.

The only reason to skip is if the change genuinely doesn't touch infrastructure (see the "does NOT trigger" list above). Otherwise: update both, every time.

## Related conventions

- `~/.claude/CLAUDE.md` (user global): write a `plan.md` at the repo root before any non-trivial change. That's a session-local scratch file — separate from this LOG/TODO contract. Both apply.
- `agent-workbench-live/AGENTS.md`: governs in-run behavior (the lifecycle rules, only-`draft`-asks-questions, only-`transitions.transition`-writes-status). That file is what you read if you're inside a `/shape` / `/plan` / `/validate` invocation.
