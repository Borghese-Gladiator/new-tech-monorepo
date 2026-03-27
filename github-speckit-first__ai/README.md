Here's a **copy-pasteable tutorial flow** for making a small Spec Kit project, plus what "constitution" means.

## What "constitution" means

In Spec Kit, the **constitution** is the project's permanent rulebook: the non-negotiable principles that every future spec, plan, and implementation should follow. The official constitution command updates `.specify/memory/constitution.md`, filling in the template and propagating its rules into dependent templates. GitHub's docs describe it as the place for project principles like code quality, testing standards, UX consistency, and performance requirements. ([GitHub][1])

Think of it as:
**"Before we build anything, what rules will this project always obey?"**

Examples:

* test-first or not
* accessibility requirements
* performance budgets
* API design rules
* simplicity over dependencies
* no auth for demo apps
* mobile-first UI

## Exact tutorial project commands

I'll use a **small task tracker web app** as the tutorial project.

### 1. Install Spec Kit

Spec Kit's docs recommend a persistent install with `uv tool install`, pinning a specific release tag for stability. The docs also say Python 3.11+ is required, and the current latest release page shows `0.4.1` as latest. ([GitHub][2])

```bash
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@v0.4.1
specify check
```

### 2. Create the tutorial project

For Claude/Copilot-style slash commands, initialize like this: ([GitHub][2])

```bash
specify init task-tracker-tutorial --ai claude
cd task-tracker-tutorial
```

If you are using **Codex CLI**, Spec Kit's README says to use `--ai codex --ai-skills`, and then invoke commands as `$speckit-*` instead of `/speckit.*`. ([GitHub][3])

```bash
specify init task-tracker-tutorial --ai codex --ai-skills
cd task-tracker-tutorial
```

## Exact prompts to build

For most agents, use these in the agent chat as slash commands. The official flow is constitution → specify → clarify → plan → tasks → implement, with optional analyze before implement. ([GitHub][4])

### 3. Constitution prompt

Sets up 6 core principles: Simplicity, Minimal Dependencies, Testing Discipline, Accessibility, Performance, and Code Clarity. Creates `.specify/memory/constitution.md` v1.0.0.

```text
/speckit.constitution This is a small tutorial web app. Keep the architecture simple and easy to read. Prefer minimal dependencies. All features must include basic happy-path and failure-path testing. Accessibility is required for core flows. The app should feel fast on first load and work well on mobile screens. Use clear naming and small functions.
```

For Codex skills mode:

```text
$speckit-constitution This is a small tutorial web app. Keep the architecture simple and easy to read. Prefer minimal dependencies. All features must include basic happy-path and failure-path testing. Accessibility is required for core flows. The app should feel fast on first load and work well on mobile screens. Use clear naming and small functions.
```

**Output**: `.specify/memory/constitution.md` with 6 principles, Technology Constraints, Development Workflow, and Governance sections.

### 4. Specification prompt

Creates the feature branch `001-task-tracker` and generates a spec with 4 user stories (P1: Create & View, P2: Complete & Filter, P2: Persistence, P3: Edit & Delete), 15 functional requirements, 5 success criteria, and edge cases.

```text
/speckit.specify Build a small task tracker for one user. The user can create tasks, edit tasks, mark tasks complete, delete tasks, and filter tasks by all, active, and completed. The app should save tasks so they remain after refresh. The main goal is to demonstrate a complete spec-driven workflow on a simple project.
```

Codex version:

```text
$speckit-specify Build a small task tracker for one user. The user can create tasks, edit tasks, mark tasks complete, delete tasks, and filter tasks by all, active, and completed. The app should save tasks so they remain after refresh. The main goal is to demonstrate a complete spec-driven workflow on a simple project.
```

**Output**: `specs/001-task-tracker/spec.md` + `specs/001-task-tracker/checklists/requirements.md`

### 5. Clarify prompt

Interactive Q&A session (up to 5 questions) that resolved: delete confirmation (immediate + toast), storage quota handling (toast warning, in-memory fallback), focus management after CRUD, mobile filter controls (dropdown <480px), and toast ARIA accessibility.

```text
/speckit.clarify Focus on edge cases, persistence behavior, accessibility expectations, and mobile layout.
```

Codex:

```text
$speckit-clarify Focus on edge cases, persistence behavior, accessibility expectations, and mobile layout.
```

**Output**: Updated `spec.md` with 5 new FRs (FR-012 through FR-015) and a Clarifications section recording all Q&A decisions.

### 6. Plan prompt

Generates the implementation plan with tech stack decisions, constitution compliance check, project structure, and Phase 0/1 design artifacts.

```text
/speckit.plan Use Vite for a small frontend app. Use React and TypeScript. Keep dependencies minimal. Store data in browser localStorage. No backend is needed. Use simple component structure and straightforward state management. Add unit tests for task logic and a small end-to-end test for the main user flow.
```

Codex:

```text
$speckit-plan Use Vite for a small frontend app. Use React and TypeScript. Keep dependencies minimal. Store data in browser localStorage. No backend is needed. Use simple component structure and straightforward state management. Add unit tests for task logic and a small end-to-end test for the main user flow.
```

**Output**:
- `specs/001-task-tracker/plan.md` — tech context, constitution check (all 6 pass), project structure
- `specs/001-task-tracker/research.md` — 7 research decisions (state mgmt, localStorage, toast, filters, CSS, testing, quota)
- `specs/001-task-tracker/data-model.md` — Task entity, Filter type, storage schema
- `specs/001-task-tracker/contracts/ui-contracts.md` — component props/behavior for 6 components + pure helper signatures
- `specs/001-task-tracker/quickstart.md` — setup, usage, test commands, manual validation checklist
- `CLAUDE.md` — agent context updated with TypeScript/React/localStorage stack

### 7. Tasks prompt

Generates 32 tasks across 7 phases, organized by user story with parallel markers and dependency graph.

```text
/speckit.tasks
```

Codex:

```text
$speckit-tasks
```

**Output**: `specs/001-task-tracker/tasks.md` with:
- Phase 1: Setup (5 tasks)
- Phase 2: Foundational (5 tasks, includes unit tests)
- Phase 3: US1 — Create & View (6 tasks, MVP)
- Phase 4: US2 — Complete & Filter (4 tasks)
- Phase 5: US3 — Edit & Delete (4 tasks)
- Phase 6: US4 — Persistence (3 tasks, includes E2E)
- Phase 7: Polish (5 tasks)

### 8. Analyze step

Cross-artifact consistency check that found 0 critical issues. Identified 3 minor improvements (FR renumbering, task description clarity) which were applied.

```text
/speckit.analyze
```

Codex:

```text
$speckit-analyze
```

**Output**: Analysis report with 100% requirement coverage (15/15 FRs mapped to tasks), 0 critical issues, and 3 remediation edits applied.

### 9. Implement prompt

```text
/speckit.implement
```

Codex:

```text
$speckit-implement
```

## What to test at the end

At minimum, test these behaviors against the final app:

1. **Create task**
   Add a task and confirm it appears immediately.

2. **Edit task**
   Rename a task and confirm the new text persists.

3. **Complete task**
   Mark a task complete and confirm its state updates visually and functionally.

4. **Delete task**
   Remove a task and confirm it disappears (with toast notification) and stays gone after refresh.

5. **Filtering**
   Verify All / Active / Completed each show the correct subset. On mobile (<480px), filters should render as a dropdown.

6. **Persistence**
   Refresh the browser and confirm tasks are restored from local storage.

7. **Accessibility basics**
   Confirm keyboard access works for create, toggle, edit, delete, and filter actions; confirm inputs/buttons are labeled clearly; confirm toasts are announced by screen readers (ARIA live region).

8. **Mobile layout**
   Check a narrow viewport (320px) and make sure the core flow is still usable with no horizontal scrolling.

9. **Failure-path behavior**
   Try blank task creation and confirm validation prevents bad input with a clear message.

Those tests line up with Spec Kit's emphasis on clarifying requirements first, then translating them into plans and taskable implementation work with testing discipline baked in. ([GitHub][4])

## Fastest possible version

If you just want the shortest possible happy path for a tutorial:

```bash
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@v0.4.1
specify init task-tracker-tutorial --ai claude
cd task-tracker-tutorial
```

Then in your agent:

```text
/speckit.constitution Keep this project simple, readable, accessible, and lightly tested.
/speckit.specify Build a one-user task tracker with create, edit, complete, delete, filter, and persistence after refresh.
/speckit.clarify Focus on edge cases and accessibility.
/speckit.plan Use Vite, React, TypeScript, and localStorage. Keep dependencies minimal.
/speckit.tasks
/speckit.analyze
/speckit.implement
```

## Generated artifacts summary

After running steps 3–8, the project contains:

```
task-tracker-tutorial/
├── .specify/
│   └── memory/
│       └── constitution.md          # 6 principles, v1.0.0
├── CLAUDE.md                        # Agent context (auto-generated)
├── specs/
│   └── 001-task-tracker/
│       ├── spec.md                  # 4 user stories, 15 FRs, 5 SCs
│       ├── plan.md                  # Tech stack, structure, constitution check
│       ├── research.md              # 7 research decisions
│       ├── data-model.md            # Task entity, Filter type, storage schema
│       ├── quickstart.md            # Setup + manual validation checklist
│       ├── tasks.md                 # 32 tasks across 7 phases
│       ├── checklists/
│       │   └── requirements.md      # Spec quality checklist (all pass)
│       └── contracts/
│           └── ui-contracts.md      # Component interfaces + pure helpers
```

[1]: https://github.com/github/spec-kit/blob/main/templates/commands/constitution.md "spec-kit/templates/commands/constitution.md at main · github/spec-kit · GitHub"
[2]: https://github.com/github/spec-kit "GitHub - github/spec-kit:  Toolkit to help you get started with Spec-Driven Development · GitHub"
[3]: https://github.com/github/spec-kit/blob/main/README.md?utm_source=chatgpt.com "spec-kit/README.md at main · github/spec-kit · GitHub"
[4]: https://github.com/github/spec-kit/blob/main/docs/quickstart.md/ "spec-kit/docs/quickstart.md at main · github/spec-kit · GitHub"
