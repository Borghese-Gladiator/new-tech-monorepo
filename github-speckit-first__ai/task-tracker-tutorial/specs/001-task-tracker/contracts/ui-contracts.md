# UI Contracts: Task Tracker

## Component Interface Contracts

### App (root)

**State owned**:
- `tasks: Task[]` — via `useLocalStorage("task-tracker-tasks", [])`
- `filter: Filter` — via `useState<Filter>("all")`
- `toast: { message: string; visible: boolean }` — via `useState`

**Renders**: TaskForm, FilterControls, TaskList, Toast

### TaskForm

**Props**:
- `onAddTask: (title: string) => void`

**Behavior**:
- Renders a text input and submit button
- Trims input; rejects empty strings (shows inline validation)
- Clears input on successful submit
- Submit via Enter key or button click

**Accessibility**:
- Input has `<label>` or `aria-label`
- Submit button is keyboard-focusable

### TaskList

**Props**:
- `tasks: Task[]` — already filtered by parent
- `onToggle: (id: string) => void`
- `onEdit: (id: string, newTitle: string) => void`
- `onDelete: (id: string) => void`

**Behavior**:
- Renders a `<ul>` of TaskItem components
- Shows empty state message when `tasks.length === 0`

**Accessibility**:
- Uses `<ul>` / `<li>` semantic list markup

### TaskItem

**Props**:
- `task: Task`
- `onToggle: (id: string) => void`
- `onEdit: (id: string, newTitle: string) => void`
- `onDelete: (id: string) => void`

**Behavior**:
- Displays task title with completed visual indicator (strikethrough
  when `isComplete`)
- Checkbox toggles completion
- Edit button enters inline edit mode (text input replaces title)
- Delete button removes task immediately, triggers toast
- Edit mode: save on Enter/blur, cancel on Escape
- Edit rejects empty titles (preserves original)

**Accessibility**:
- Checkbox has accessible label (task title)
- Edit/delete buttons have `aria-label` describing the action + task
- Focus moves to new task after create, next task after delete
  (managed by parent via ref)

### FilterControls

**Props**:
- `currentFilter: Filter`
- `onFilterChange: (filter: Filter) => void`

**Behavior**:
- Desktop (≥480px): Renders three buttons (All, Active, Completed)
  with active state styling on the selected filter
- Mobile (<480px): Renders a native `<select>` dropdown
- Both variants control the same filter state

**Accessibility**:
- Buttons have `aria-pressed` or equivalent active indication
- Select has associated `<label>`

### Toast

**Props**:
- `message: string`
- `visible: boolean`

**Behavior**:
- Renders message text when `visible` is true
- Auto-dismisses after 3 seconds

**Accessibility**:
- Container has `role="status"` and `aria-live="polite"`
- Content is announced by screen readers without interruption

## Type Definitions

```typescript
interface Task {
  id: string;
  title: string;
  isComplete: boolean;
  createdAt: number;
}

type Filter = "all" | "active" | "completed";
```

## Pure Helper Functions (taskHelpers.ts)

```typescript
createTask(title: string): Task
toggleTask(tasks: Task[], id: string): Task[]
editTask(tasks: Task[], id: string, newTitle: string): Task[]
deleteTask(tasks: Task[], id: string): Task[]
filterTasks(tasks: Task[], filter: Filter): Task[]
```

Each function is pure (no side effects), takes immutable input,
returns a new array/object. This enables straightforward unit testing.
