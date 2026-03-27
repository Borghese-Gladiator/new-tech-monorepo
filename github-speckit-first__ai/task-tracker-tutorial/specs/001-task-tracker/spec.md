# Feature Specification: Task Tracker

**Feature Branch**: `001-task-tracker`
**Created**: 2026-03-27
**Status**: Draft
**Input**: User description: "Build a small task tracker for one user. The user can create tasks, edit tasks, mark tasks complete, delete tasks, and filter tasks by all, active, and completed. The app should save tasks so they remain after refresh."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create and View Tasks (Priority: P1)

A user opens the task tracker and creates a new task by typing a title
and submitting it. The task appears immediately in the task list. The
user can see all their tasks at a glance.

**Why this priority**: Without the ability to create and view tasks,
no other feature has value. This is the core interaction loop.

**Independent Test**: Can be fully tested by opening the app, typing
a task title, submitting it, and verifying it appears in the list.
Delivers the foundational value of capturing tasks.

**Acceptance Scenarios**:

1. **Given** the app is open with an empty task list, **When** the
   user types "Buy groceries" and submits, **Then** "Buy groceries"
   appears in the task list as an active (incomplete) task.
2. **Given** the app has existing tasks, **When** the user creates
   another task, **Then** the new task is added to the list without
   affecting existing tasks.
3. **Given** the user submits an empty title, **When** the form is
   submitted, **Then** no task is created and the user sees feedback
   that a title is required.

---

### User Story 2 - Mark Tasks Complete and Filter (Priority: P2)

A user marks a task as complete by toggling its status. The user can
filter the task list to show all tasks, only active tasks, or only
completed tasks.

**Why this priority**: Completing tasks is the primary purpose of a
task tracker. Filtering lets the user focus on what matters now.

**Independent Test**: Can be tested by creating a few tasks, marking
some complete, and switching between filter views to verify correct
filtering.

**Acceptance Scenarios**:

1. **Given** a task "Buy groceries" exists and is active, **When**
   the user marks it complete, **Then** the task shows a completed
   visual indicator (e.g., strikethrough or checkmark).
2. **Given** tasks exist in both active and completed states, **When**
   the user selects the "Active" filter, **Then** only active tasks
   are shown.
3. **Given** tasks exist in both active and completed states, **When**
   the user selects the "Completed" filter, **Then** only completed
   tasks are shown.
4. **Given** the user is viewing filtered tasks, **When** the user
   selects "All", **Then** all tasks are shown regardless of status.
5. **Given** a completed task, **When** the user toggles it again,
   **Then** the task returns to active status.

---

### User Story 3 - Edit and Delete Tasks (Priority: P3)

A user edits the title of an existing task. A user deletes a task
they no longer need. Both actions take effect immediately.

**Why this priority**: Editing and deleting are important but
secondary — a tracker is useful even without them. They improve
day-to-day usability.

**Independent Test**: Can be tested by creating a task, editing its
title to verify the change persists, and deleting a task to verify
it is removed from the list.

**Acceptance Scenarios**:

1. **Given** a task "Buy groceries" exists, **When** the user edits
   the title to "Buy organic groceries", **Then** the updated title
   is displayed in the task list.
2. **Given** a task exists, **When** the user presses the delete
   button, **Then** the task is immediately removed from the list and
   a brief toast notification confirms the deletion.
3. **Given** the user is editing a task, **When** they submit an
   empty title, **Then** the edit is rejected and the original title
   is preserved.
4. **Given** the user is editing a task, **When** they cancel the
   edit, **Then** the original title is preserved.

---

### User Story 4 - Data Persistence (Priority: P2)

Tasks survive a page refresh. When the user returns to the app,
all tasks (including their completion status) are exactly as they
were left.

**Why this priority**: Equal to P2 because a tracker that loses data
on refresh is not useful beyond a single session. This is a core
reliability expectation.

**Independent Test**: Can be tested by creating tasks, marking some
complete, refreshing the page, and verifying all tasks and their
statuses are preserved.

**Acceptance Scenarios**:

1. **Given** the user has created tasks and marked some complete,
   **When** the user refreshes the page, **Then** all tasks appear
   with their correct completion status.
2. **Given** the user edits a task title, **When** the page is
   refreshed, **Then** the edited title is preserved.
3. **Given** the user deletes a task, **When** the page is refreshed,
   **Then** the deleted task does not reappear.

---

### Edge Cases

- What happens when the user creates a task with very long text
  (e.g., 500+ characters)? The title MUST be accepted but the UI
  MUST handle overflow gracefully without breaking layout.
- What happens when saved data becomes corrupted or unreadable? The
  app MUST recover gracefully — starting with an empty list rather
  than crashing.
- What happens when the user tries to create a duplicate task title?
  Duplicates are allowed — task identity is not based on title.
- What happens when the user has many tasks (e.g., 100+)? The list
  MUST remain scrollable and responsive without noticeable lag.
- What happens when local storage is full? The app MUST display a
  toast warning that storage is full. Tasks continue to function
  in-memory for the current session but may not persist on refresh.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow the user to create a task by
  providing a non-empty title
- **FR-002**: System MUST display all tasks in a visible list
- **FR-003**: System MUST allow the user to toggle a task between
  active and completed states
- **FR-004**: System MUST allow the user to filter the list by All,
  Active, or Completed
- **FR-005**: System MUST allow the user to edit the title of an
  existing task
- **FR-006**: System MUST allow the user to delete a task immediately
  (no confirmation dialog) and display a brief toast notification
  confirming the deletion
- **FR-007**: System MUST persist all task data (titles, completion
  status) across page refreshes using local browser storage
- **FR-008**: System MUST prevent creation or saving of tasks with
  empty titles
- **FR-009**: System MUST recover gracefully if persisted data is
  corrupt, falling back to an empty task list
- **FR-010**: All interactive elements MUST be keyboard-accessible
- **FR-011**: The active filter MUST be visually indicated so the
  user knows which view they are in
- **FR-012**: System MUST display a toast warning when local storage
  is full; tasks MUST continue to function in-memory for the current
  session
- **FR-013**: After creating a task, focus MUST move to the newly
  created task. After deleting a task, focus MUST move to the next
  task in the list (or the input field if the list is empty)
- **FR-014**: On screens narrower than 480px, filter controls MUST
  be presented as a dropdown/select menu to conserve horizontal space
- **FR-015**: Toast notifications MUST use an ARIA live region
  (`role="status"` / `aria-live="polite"`) so screen readers
  announce them without interrupting the user's current action

### Key Entities

- **Task**: Represents a single to-do item. Attributes: unique
  identifier, title (non-empty string), completion status (active
  or completed), creation timestamp.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can create a task, mark it complete, and verify
  persistence in under 30 seconds on first use
- **SC-002**: The app loads and displays the task list within 2
  seconds on a standard mobile connection
- **SC-003**: All core flows (create, complete, filter) are
  completable using keyboard alone
- **SC-004**: The app is usable on screens as narrow as 320px with
  no horizontal scrolling
- **SC-005**: 100% of tasks survive a page refresh with correct
  status

## Assumptions

- This is a single-user app — no authentication, accounts, or
  multi-device sync is needed
- Data is stored locally in the browser; no server or backend is
  required
- The app targets modern evergreen browsers (Chrome, Firefox,
  Safari, Edge — latest 2 versions)
- There is no limit on the number of tasks a user can create, but
  performance expectations assume typical usage under 500 tasks
- No due dates, priorities, categories, or other task metadata
  beyond title and completion status
- No undo/redo functionality is required
- No drag-and-drop reordering is required

## Clarifications

### Session 2026-03-27

- Q: Should task deletion require confirmation? → A: No confirmation dialog; delete is immediate with a brief toast notification.
- Q: What happens when local storage is full? → A: Show a toast warning; tasks continue in-memory for the session.
- Q: Where does focus move after CRUD actions? → A: To the affected task (new task after create, next task after delete, input if list empty).
- Q: How should filter controls display on narrow mobile screens? → A: Dropdown/select menu on screens narrower than 480px.
- Q: How should toast notifications be accessible to screen readers? → A: Use ARIA live region (`role="status"` / `aria-live="polite"`).
