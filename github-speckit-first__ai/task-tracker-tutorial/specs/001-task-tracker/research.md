# Research: Task Tracker

## R1: State Management Approach

**Decision**: Use React's built-in `useState` in the root `App`
component. Pass state and callbacks down via props.

**Rationale**: The app has a single screen with ~5 components and one
data type (Task[]). useState is sufficient — useReducer or external
state libraries add complexity with no benefit at this scale.

**Alternatives considered**:
- `useReducer`: Viable but adds indirection for simple CRUD. Would
  be appropriate if state transitions were more complex.
- Zustand/Jotai: Violates constitution principle II (Minimal
  Dependencies) — an extra library for trivial state.
- Context API: Unnecessary when prop depth is at most 2 levels.

## R2: localStorage Persistence Strategy

**Decision**: Custom `useLocalStorage` hook that wraps
`useState` + `localStorage.setItem`/`getItem`. On load, read and
parse JSON from localStorage. On every state change, write back.
Wrap reads in try/catch — if parsing fails, return empty array and
clear the corrupt key.

**Rationale**: Direct localStorage access is simple and synchronous.
A custom hook keeps persistence logic isolated and testable. The
try/catch with fallback satisfies FR-009 (corrupt data recovery).

**Alternatives considered**:
- `useEffect` sync: Writing in a useEffect after state change is
  also valid but introduces a render gap. Keeping write in the
  setter callback is more predictable.
- IndexedDB: Overkill for <500 small JSON objects. Adds async
  complexity.
- Third-party storage lib (localforage): Violates principle II.

## R3: Storage Quota Handling

**Decision**: Wrap `localStorage.setItem` in try/catch. If a
`QuotaExceededError` is thrown, set a `storageWarning` state flag
that triggers a toast. Tasks continue in-memory.

**Rationale**: localStorage throws `QuotaExceededError` when full
(~5MB limit). Catching this specific error and showing a toast
satisfies FR-012.

## R4: Toast Notification Pattern

**Decision**: Simple `Toast` component that renders into an ARIA
live region (`role="status"`, `aria-live="polite"`). Show/hide
controlled by a `toast` state object in App (`{message, visible}`).
Auto-dismiss after 3 seconds via `setTimeout`.

**Rationale**: No toast library needed — the component is ~20 lines.
The ARIA live region satisfies FR-015. Auto-dismiss keeps the UI
clean without user interaction.

**Alternatives considered**:
- react-hot-toast / react-toastify: Violates principle II.
- Browser alert(): Blocks the UI, poor UX.

## R5: Responsive Filter Controls

**Decision**: Render filter as a horizontal button group on screens
≥480px. On screens <480px, render a native `<select>` dropdown.
Use a CSS media query to toggle visibility of the two variants,
or a `useMediaQuery`-style check.

**Rationale**: Native `<select>` is accessible by default (keyboard
+ screen reader), uses minimal space, and requires no custom
dropdown implementation. Satisfies FR-014.

**Alternatives considered**:
- CSS-only approach (hide/show with media queries on two elements):
  Simpler, no JS needed for the switch. Preferred.
- Single responsive component with custom dropdown: More complex,
  accessibility harder to get right.

**Final approach**: CSS-only — render both a button group and a
select, use `display: none` via media query to show the appropriate
one. Both are wired to the same filter state.

## R6: Testing Strategy

**Decision**:
- **Unit tests** (Vitest): Test `taskHelpers.ts` pure functions
  (createTask, toggleTask, editTask, deleteTask, filterTasks) and
  `useLocalStorage` hook. Cover happy + failure paths per
  constitution principle III.
- **E2E test** (Playwright): One test covering the main user flow:
  create task → mark complete → filter → refresh → verify persistence.

**Rationale**: Pure logic in `taskHelpers.ts` is easy to test without
DOM. The E2E test validates the integrated experience including
persistence. Vitest is zero-config with Vite. Playwright is the
standard E2E tool with good a11y support.

**Alternatives considered**:
- Jest: Would require extra config to work with Vite/TypeScript.
  Vitest is drop-in.
- Cypress: Heavier install footprint than Playwright.
- React Testing Library for component tests: Could add later but
  pure logic unit tests + E2E cover the spec requirements.

## R7: CSS Approach

**Decision**: Plain CSS files. `index.css` for global styles,
resets, and responsive breakpoints. `App.css` for component layout.
Use CSS custom properties for consistent spacing/colors.

**Rationale**: No CSS framework or CSS-in-JS needed for a small app.
Plain CSS is the simplest approach (principle I), zero dependencies
(principle II), and readable by tutorial users.

**Alternatives considered**:
- Tailwind: Adds dependency + build config. Overkill for ~100 lines
  of CSS.
- CSS Modules: Slight benefit for scoping but adds build complexity
  for this scale.
- Styled-components: Dependency, runtime overhead, unfamiliar to
  beginners.
