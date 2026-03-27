# Quickstart: Task Tracker

## Prerequisites

- Node.js 18+ (LTS recommended)
- npm 9+ (ships with Node.js)

## Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The app opens at `http://localhost:5173` (Vite default).

## Usage

1. **Create a task**: Type a title in the input field and press Enter
   or click the Add button.
2. **Complete a task**: Click the checkbox next to a task. It toggles
   between active and completed.
3. **Filter tasks**: Use the filter controls (buttons on desktop,
   dropdown on mobile) to view All, Active, or Completed tasks.
4. **Edit a task**: Click the edit button on a task, modify the title,
   and press Enter to save or Escape to cancel.
5. **Delete a task**: Click the delete button on a task. It is removed
   immediately and a toast confirms the deletion.
6. **Persistence**: Close and reopen the browser tab — all tasks are
   preserved via localStorage.

## Running Tests

```bash
# Unit tests
npm test

# Unit tests in watch mode
npm run test:watch

# E2E tests (requires app to be running or uses Playwright's webServer config)
npm run test:e2e
```

## Build for Production

```bash
npm run build
npm run preview    # Preview the production build locally
```

## Project Structure

```
src/
├── components/       # React components (App, TaskForm, TaskList, etc.)
├── hooks/            # Custom hooks (useLocalStorage)
├── types.ts          # TypeScript type definitions
├── taskHelpers.ts    # Pure task logic functions
├── main.tsx          # Entry point
├── index.css         # Global styles
└── App.css           # Component styles

tests/
├── unit/             # Vitest unit tests
└── e2e/              # Playwright E2E tests
```

## Validation Checklist

After setup, verify these manually:

- [ ] App loads and shows empty task list
- [ ] Can create a task by typing + Enter
- [ ] Cannot create a task with empty title
- [ ] Can mark a task complete (checkbox)
- [ ] Can filter by All / Active / Completed
- [ ] Can edit a task title inline
- [ ] Can delete a task (toast appears)
- [ ] Tasks survive page refresh
- [ ] All interactions work via keyboard only
- [ ] Layout works at 320px viewport width
