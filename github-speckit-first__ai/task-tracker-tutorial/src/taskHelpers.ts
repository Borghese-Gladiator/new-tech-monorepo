import type { Task, Filter } from './types'

export function createTask(title: string): Task {
  const trimmed = title.trim()
  if (!trimmed) {
    throw new Error('Task title cannot be empty')
  }
  return {
    id: crypto.randomUUID(),
    title: trimmed,
    isComplete: false,
    createdAt: Date.now(),
  }
}

export function toggleTask(tasks: Task[], id: string): Task[] {
  return tasks.map((task) =>
    task.id === id ? { ...task, isComplete: !task.isComplete } : task,
  )
}

export function editTask(
  tasks: Task[],
  id: string,
  newTitle: string,
): Task[] {
  const trimmed = newTitle.trim()
  if (!trimmed) {
    throw new Error('Task title cannot be empty')
  }
  return tasks.map((task) =>
    task.id === id ? { ...task, title: trimmed } : task,
  )
}

export function deleteTask(tasks: Task[], id: string): Task[] {
  return tasks.filter((task) => task.id !== id)
}

export function filterTasks(tasks: Task[], filter: Filter): Task[] {
  switch (filter) {
    case 'active':
      return tasks.filter((task) => !task.isComplete)
    case 'completed':
      return tasks.filter((task) => task.isComplete)
    case 'all':
    default:
      return tasks
  }
}
