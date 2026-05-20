# Build report

<!--
Single file produced by the builder during `building`. Replaces the older
implementation-summary.md + diff-summary.md pair for staged runs (TODO §1b).
The transition engine moves this file to stages/building/build.md when the
stage closes.
-->

## What changed

<!-- 1–3 sentence narrative: what was actually implemented and why. -->

## Files changed

<!--
Inventory of files added / modified / deleted. One bullet per file. Don't
duplicate the diff; capture intent.
-->

## Reviewer reading order

<!--
3–7 files in the order a reviewer should read them. Each line includes a
one-line "what to look for here". Without this section the Files changed list
is just an inventory.
-->

## Acceptance criteria coverage

<!--
Every AC from the brief mapped to a test path or an explicit "not tested —
because …" justification. Transition out of building rejects when a row is
missing either side. (Strict enforcement lands in TODO §1d/1e; for this pass
the section is conventional.)
-->

| AC | Test or justification |
|----|-----------------------|
|    |                       |

## Deviations from plan

<!-- Anything we did differently from plan.md, with one-line reasoning. -->

## Known issues

<!-- Bugs / rough edges left for the reviewer. Empty if none. -->

## Commands run

<!-- Notable build/test commands the builder ran. Helps the reviewer reproduce. -->
