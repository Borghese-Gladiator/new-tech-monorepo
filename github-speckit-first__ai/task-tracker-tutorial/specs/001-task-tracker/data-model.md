# Data Model: Task Tracker

## Entities

### Task

| Field       | Type    | Constraints                          |
|-------------|---------|--------------------------------------|
| id          | string  | Unique, generated (crypto.randomUUID or fallback) |
| title       | string  | Non-empty, whitespace-trimmed        |
| isComplete  | boolean | Default: false                       |
| createdAt   | number  | Unix timestamp (Date.now()), immutable after creation |

**Identity**: Tasks are identified by `id`. Duplicate titles are
allowed (per spec edge case).

**State transitions**:
- Created → active (`isComplete: false`)
- Active ↔ Completed (toggle `isComplete`)
- Any state → Deleted (removed from array)

**Validation rules**:
- `title` MUST be trimmed and non-empty after trimming (FR-008)
- `id` MUST be unique within the task list
- `createdAt` is set once at creation and never modified

### Filter

| Value       | Behavior                              |
|-------------|---------------------------------------|
| "all"       | Show all tasks                        |
| "active"    | Show tasks where isComplete === false |
| "completed" | Show tasks where isComplete === true  |

**Type**: String union `"all" | "active" | "completed"`
**Default**: `"all"`
**Persistence**: Filter state is NOT persisted (resets to "all" on
page load).

## Storage Schema

**Key**: `"task-tracker-tasks"`
**Value**: JSON-serialized `Task[]`

```typescript
// Stored as:
// localStorage.getItem("task-tracker-tasks")
// → '[{"id":"abc","title":"Buy groceries","isComplete":false,"createdAt":1711500000000}]'
```

**Recovery**: If `JSON.parse` throws or the result is not an array,
discard the value and return `[]` (FR-009).

**Quota**: If `localStorage.setItem` throws `QuotaExceededError`,
surface a toast warning (FR-012). Tasks remain functional in-memory.
