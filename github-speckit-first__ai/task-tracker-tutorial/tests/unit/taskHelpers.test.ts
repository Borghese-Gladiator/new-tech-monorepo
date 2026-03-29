import { describe, it, expect } from 'vitest'
import {
  createTask,
  toggleTask,
  editTask,
  deleteTask,
  filterTasks,
} from '../../src/taskHelpers'
import type { Task } from '../../src/types'

function makeTasks(): Task[] {
  return [
    { id: '1', title: 'Buy groceries', isComplete: false, createdAt: 1000 },
    { id: '2', title: 'Walk the dog', isComplete: true, createdAt: 2000 },
    { id: '3', title: 'Read a book', isComplete: false, createdAt: 3000 },
  ]
}

describe('createTask', () => {
  it('creates a task with trimmed title and default fields', () => {
    const task = createTask('  Buy milk  ')
    expect(task.title).toBe('Buy milk')
    expect(task.isComplete).toBe(false)
    expect(task.id).toBeTruthy()
    expect(task.createdAt).toBeGreaterThan(0)
  })

  it('throws when title is empty', () => {
    expect(() => createTask('')).toThrow('Task title cannot be empty')
  })

  it('throws when title is only whitespace', () => {
    expect(() => createTask('   ')).toThrow('Task title cannot be empty')
  })
})

describe('toggleTask', () => {
  it('toggles an active task to completed', () => {
    const tasks = makeTasks()
    const result = toggleTask(tasks, '1')
    expect(result.find((t) => t.id === '1')?.isComplete).toBe(true)
  })

  it('toggles a completed task back to active', () => {
    const tasks = makeTasks()
    const result = toggleTask(tasks, '2')
    expect(result.find((t) => t.id === '2')?.isComplete).toBe(false)
  })

  it('returns unchanged array when id does not exist', () => {
    const tasks = makeTasks()
    const result = toggleTask(tasks, 'nonexistent')
    expect(result).toEqual(tasks)
  })
})

describe('editTask', () => {
  it('updates the title of the matching task', () => {
    const tasks = makeTasks()
    const result = editTask(tasks, '1', 'Buy organic groceries')
    expect(result.find((t) => t.id === '1')?.title).toBe(
      'Buy organic groceries',
    )
  })

  it('trims the new title', () => {
    const tasks = makeTasks()
    const result = editTask(tasks, '1', '  Trimmed  ')
    expect(result.find((t) => t.id === '1')?.title).toBe('Trimmed')
  })

  it('throws when new title is empty', () => {
    const tasks = makeTasks()
    expect(() => editTask(tasks, '1', '')).toThrow(
      'Task title cannot be empty',
    )
  })

  it('throws when new title is only whitespace', () => {
    const tasks = makeTasks()
    expect(() => editTask(tasks, '1', '   ')).toThrow(
      'Task title cannot be empty',
    )
  })
})

describe('deleteTask', () => {
  it('removes the task with matching id', () => {
    const tasks = makeTasks()
    const result = deleteTask(tasks, '2')
    expect(result).toHaveLength(2)
    expect(result.find((t) => t.id === '2')).toBeUndefined()
  })

  it('returns unchanged array when id does not exist', () => {
    const tasks = makeTasks()
    const result = deleteTask(tasks, 'nonexistent')
    expect(result).toHaveLength(3)
  })
})

describe('filterTasks', () => {
  it('returns all tasks for "all" filter', () => {
    const tasks = makeTasks()
    expect(filterTasks(tasks, 'all')).toHaveLength(3)
  })

  it('returns only active tasks for "active" filter', () => {
    const tasks = makeTasks()
    const result = filterTasks(tasks, 'active')
    expect(result).toHaveLength(2)
    expect(result.every((t) => !t.isComplete)).toBe(true)
  })

  it('returns only completed tasks for "completed" filter', () => {
    const tasks = makeTasks()
    const result = filterTasks(tasks, 'completed')
    expect(result).toHaveLength(1)
    expect(result.every((t) => t.isComplete)).toBe(true)
  })
})
