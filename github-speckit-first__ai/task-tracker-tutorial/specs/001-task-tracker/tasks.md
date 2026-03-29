# Tasks: Task Tracker

**Input**: Design documents from `/specs/001-task-tracker/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Included — unit tests for task logic and localStorage hook, plus E2E test for main user flow (per plan.md testing strategy).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Project initialization and Vite + React + TypeScript scaffold

- [x] T001 Initialize Vite project with React + TypeScript template, configure package.json scripts (dev, build, preview, test, test:e2e)
- [x] T002 [P] Define Task interface and Filter type in src/types.ts
- [x] T003 [P] Create global CSS with custom properties, reset, and responsive breakpoints in src/index.css
- [x] T004 [P] Configure Vitest in vite.config.ts (or vitest.config.ts) with jsdom environment
- [x] T005 [P] Install and configure Playwright for E2E tests with webServer config in playwright.config.ts

**Checkpoint**: Project builds, dev server runs, test runners execute with zero tests.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [x] T006 Implement all pure helper functions in src/taskHelpers.ts: createTask, toggleTask, editTask, deleteTask, filterTasks (per contracts/ui-contracts.md signatures)
- [x] T007 Implement useLocalStorage hook in src/hooks/useLocalStorage.ts with JSON parse/stringify, corrupt data recovery (FR-009), and QuotaExceededError handling (FR-012)
- [x] T008 [P] Write unit tests for taskHelpers in tests/unit/taskHelpers.test.ts: happy-path tests for each function (create, toggle, edit, delete, filter) and failure-path tests (empty title, missing id, invalid filter)
- [x] T009 [P] Write unit tests for useLocalStorage in tests/unit/useLocalStorage.test.ts: happy-path (read/write round-trip) and failure-path (corrupt JSON recovery, QuotaExceededError handling)
- [x] T010 Implement Toast component in src/components/Toast.tsx with role="status", aria-live="polite", auto-dismiss after 3s (FR-015)

**Checkpoint**: Foundation ready — all pure logic tested, storage hook tested, toast available. Unit tests pass.

---

## Phase 3: User Story 1 - Create and View Tasks (Priority: P1) MVP

**Goal**: User can create tasks with a title and see them in a list. Empty titles are rejected.

**Independent Test**: Open app, type a task title, submit, verify it appears in the list.

### Implementation for User Story 1

- [x] T011 [US1] Implement TaskForm component in src/components/TaskForm.tsx: text input with label, submit button, empty-title validation with inline feedback, clears on success (per contracts)
- [x] T012 [US1] Implement TaskList component in src/components/TaskList.tsx: renders <ul> of TaskItem components, shows empty state message when no tasks
- [x] T013 [US1] Implement TaskItem component in src/components/TaskItem.tsx: displays task title, renders checkbox and edit/delete buttons with noop placeholder callbacks (actual toggle handler added in T017/US2, edit/delete handlers in T021-T023/US3)
- [x] T014 [US1] Implement App component in src/components/App.tsx: owns tasks state via useLocalStorage, owns toast state, renders TaskForm and TaskList, handles addTask callback with focus management to new task (FR-013)
- [x] T015 [US1] Wire main.tsx entry point to render App, import index.css
- [x] T016 [US1] Add component layout styles in src/App.css: task list layout, form styling, empty state, long-title overflow handling (word-break)

**Checkpoint**: User can create tasks and see them in a list. Empty titles rejected. Tasks persist on refresh (via useLocalStorage from Phase 2). App runs in browser.

---

## Phase 4: User Story 2 - Mark Tasks Complete and Filter (Priority: P2)

**Goal**: User can toggle task completion and filter the list by All, Active, Completed.

**Independent Test**: Create tasks, mark some complete, switch filter views, verify correct filtering.

### Implementation for User Story 2

- [x] T017 [US2] Add toggle completion behavior to TaskItem in src/components/TaskItem.tsx: checkbox onChange calls onToggle, completed tasks show strikethrough styling
- [x] T018 [US2] Implement FilterControls component in src/components/FilterControls.tsx: button group (desktop ≥480px) + native select (mobile <480px), aria-pressed on active button, label on select (FR-011, FR-014)
- [x] T019 [US2] Update App component in src/components/App.tsx: add filter state (useState<Filter>("all")), pass filtered tasks to TaskList using filterTasks helper, render FilterControls
- [x] T020 [US2] Add responsive filter styles in src/App.css: media query at 480px to show/hide button group vs select dropdown, active filter button styling

**Checkpoint**: User can toggle tasks complete/active. Filter controls switch views correctly. Desktop shows buttons, mobile shows dropdown.

---

## Phase 5: User Story 3 - Edit and Delete Tasks (Priority: P3)

**Goal**: User can edit a task title inline and delete tasks with toast confirmation.

**Independent Test**: Create a task, edit its title, verify change. Delete a task, verify removal and toast.

### Implementation for User Story 3

- [x] T021 [US3] Add inline edit mode to TaskItem in src/components/TaskItem.tsx: edit button toggles input, save on Enter/blur, cancel on Escape, reject empty titles (FR-005, FR-008)
- [x] T022 [US3] Add delete behavior to TaskItem in src/components/TaskItem.tsx: delete button calls onDelete, parent shows toast (FR-006)
- [x] T023 [US3] Update App component in src/components/App.tsx: add handleEdit and handleDelete callbacks using editTask/deleteTask helpers, trigger toast on delete, manage focus to next task after delete (FR-013)
- [x] T024 [US3] Add edit mode styles in src/App.css: inline edit input styling, delete button styling, toast positioning

**Checkpoint**: User can edit task titles inline (save/cancel/reject empty). User can delete tasks with toast feedback. Focus moves correctly after delete.

---

## Phase 6: User Story 4 - Data Persistence (Priority: P2)

**Goal**: All task data survives page refresh. Corrupt data and storage-full scenarios handled gracefully.

**Independent Test**: Create tasks, mark some complete, refresh page, verify all tasks and statuses preserved.

### Implementation for User Story 4

- [x] T025 [US4] Code review persistence wiring in App: confirm useLocalStorage setter is called on every task mutation (create, toggle, edit, delete) — no new tests needed here; E2E coverage is in T027
- [x] T026 [US4] Add storage-full toast trigger in App: when useLocalStorage reports quota error, show toast warning via existing Toast component (FR-012)
- [x] T027 [US4] Write E2E test in tests/e2e/taskTracker.spec.ts: create task → mark complete → filter Active (task hidden) → filter All (task visible) → refresh page → verify task still complete and visible

**Checkpoint**: All persistence scenarios verified. E2E test passes the full create → complete → filter → refresh flow.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Accessibility hardening, responsive refinement, edge cases

- [x] T028 [P] Add keyboard navigation audit: verify all interactive elements are reachable via Tab, Enter, Escape across all components (FR-010)
- [x] T029 [P] Add aria-labels to edit/delete buttons in TaskItem (e.g., "Edit Buy groceries", "Delete Buy groceries") for screen reader context
- [x] T030 [P] Test responsive layout at 320px viewport: verify no horizontal scroll, touch targets ≥44x44px, filter dropdown renders (SC-004)
- [x] T031 [P] Handle long task titles: verify word-break CSS works for 500+ character titles without layout break
- [x] T032 Run quickstart.md manual validation checklist end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on T001 (project init) and T002 (types) from Setup — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Phase 2 completion
- **User Story 2 (Phase 4)**: Depends on Phase 3 (needs TaskItem and App from US1)
- **User Story 3 (Phase 5)**: Depends on Phase 3 (needs TaskItem and App from US1)
- **User Story 4 (Phase 6)**: Depends on Phases 3–5 (verifies persistence across all operations)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 (needs existing TaskItem and App components to extend)
- **User Story 3 (P3)**: Depends on US1 (needs existing TaskItem and App components to extend)
- **User Story 4 (P2)**: Depends on US1–3 (E2E test covers full flow)
- **Note**: US2 and US3 can run in parallel after US1 is complete (they modify different parts of TaskItem)

### Within Each User Story

- Models/types before components
- Components before integration in App
- Styles alongside or after component implementation
- Tests after the code they cover is functional

### Parallel Opportunities

- **Phase 1**: T002, T003, T004, T005 can all run in parallel after T001
- **Phase 2**: T008 and T009 can run in parallel (different test files); T010 is independent
- **Phase 4 & 5**: US2 and US3 can run in parallel after US1 checkpoint
- **Phase 7**: T028, T029, T030, T031 can all run in parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Create a task, verify it appears, refresh, verify persistence
5. Deploy/demo if ready — this is a usable task creator

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → MVP!
3. Add User Story 2 + 3 (parallel) → Toggle, filter, edit, delete
4. Add User Story 4 → E2E verification of persistence
5. Polish → Accessibility + responsive hardening

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify unit tests pass after Phase 2 before moving to user stories
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
