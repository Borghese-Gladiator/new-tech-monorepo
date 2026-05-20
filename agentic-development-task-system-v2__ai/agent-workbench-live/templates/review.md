# Review

<!--
Adversarial self-review against brief.md + plan.md.
The reviewer is not the builder.
-->

## Decision

<!-- One of: approve, request_changes, block. -->

## Did the implementation satisfy the brief?

## Did it accidentally expand scope?

## Are there fragile assumptions?

## Are there missing tests?

## Are there security / data loss / migration risks?

## What should the human review first?

## Blast radius

<!--
TODO §1g. Trace what this change touches, up to depth 3, using git commands
from inside the worktree. Stop expanding at depth 3.

Recipe:

  git diff --name-only <base_ref>...HEAD       # depth-1: changed files
  # For each touched file, identify the top-level symbols you modified
  # (functions, classes, exports). For each symbol:
  git grep -n <symbol>                          # depth-2: callers
  # Then repeat for the callers of those callers; STOP AT DEPTH 3.

Render the result as a small tree:

  depth 1 (changed files):
    src/foo.py
    src/bar.py

  depth 2 (callers of changed symbols):
    src/foo.py:fn_x  -> src/baz.py, src/quux.py
    src/bar.py:Bar   -> src/baz.py

  depth 3 (callers of those callers):
    src/baz.py:fn_y  -> tests/test_e2e.py

Call out anything in depth 2/3 that lives OUTSIDE the brief's expected scope
as a scope-creep risk. The CLI handles depth-1 scope creep automatically
(see "Scope creep check" below if it appears); your job is the deeper reach.
-->

## Findings

### F-001
- **Severity**: blocking | major | minor
- **Where**:
- **Issue**:
- **Suggested fix**:
