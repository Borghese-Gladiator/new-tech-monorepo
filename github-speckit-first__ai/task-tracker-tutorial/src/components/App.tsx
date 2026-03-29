import { useState, useRef, useCallback, useEffect } from 'react'
import type { Task, Filter } from '../types'
import { useLocalStorage } from '../hooks/useLocalStorage'
import {
  createTask,
  toggleTask,
  editTask,
  deleteTask,
  filterTasks,
} from '../taskHelpers'
import { TaskForm } from './TaskForm'
import { TaskList } from './TaskList'
import { FilterControls } from './FilterControls'
import { Toast } from './Toast'
import '../App.css'

export function App() {
  const { value: tasks, setValue: setTasks, storageError } =
    useLocalStorage<Task[]>('task-tracker-tasks', [])
  const [filter, setFilter] = useState<Filter>('all')
  const [toast, setToast] = useState({ message: '', visible: false })
  const taskListRef = useRef<HTMLDivElement>(null)
  const lastAddedIdRef = useRef<string | null>(null)
  const deletedIndexRef = useRef<number>(-1)

  function showToast(message: string) {
    setToast({ message, visible: true })
  }

  const dismissToast = useCallback(() => {
    setToast({ message: '', visible: false })
  }, [])

  function handleAddTask(title: string) {
    const newTask = createTask(title)
    lastAddedIdRef.current = newTask.id
    setTasks((prev) => [...prev, newTask])
  }

  function handleToggle(id: string) {
    setTasks((prev) => toggleTask(prev, id))
  }

  function handleEdit(id: string, newTitle: string) {
    try {
      setTasks((prev) => editTask(prev, id, newTitle))
    } catch {
      // empty title — TaskItem already handles this gracefully
    }
  }

  function handleDelete(id: string) {
    const index = tasks.findIndex((t) => t.id === id)
    deletedIndexRef.current = index
    const taskTitle = tasks.find((t) => t.id === id)?.title ?? 'Task'
    setTasks((prev) => deleteTask(prev, id))
    showToast(`"${taskTitle}" deleted`)
  }

  // Focus management after add/delete
  useEffect(() => {
    if (lastAddedIdRef.current) {
      const id = lastAddedIdRef.current
      lastAddedIdRef.current = null
      requestAnimationFrame(() => {
        const el = taskListRef.current?.querySelector(
          `[data-task-id="${id}"]`,
        ) as HTMLElement | null
        el?.focus()
      })
    }
  }, [tasks])

  useEffect(() => {
    if (deletedIndexRef.current >= 0) {
      const idx = deletedIndexRef.current
      deletedIndexRef.current = -1
      requestAnimationFrame(() => {
        const items = taskListRef.current?.querySelectorAll('.task-item')
        if (!items || items.length === 0) {
          document.getElementById('new-task')?.focus()
          return
        }
        const target = items[Math.min(idx, items.length - 1)] as HTMLElement
        target?.querySelector('input[type="checkbox"]')
          ? (target.querySelector('input[type="checkbox"]') as HTMLElement).focus()
          : target.focus()
      })
    }
  }, [tasks])

  // Storage error toast
  useEffect(() => {
    if (storageError) {
      showToast('Storage is full. Tasks may not persist after refresh.')
    }
  }, [storageError])

  const visibleTasks = filterTasks(tasks, filter)

  return (
    <div className="app">
      <h1>Task Tracker</h1>
      <TaskForm onAddTask={handleAddTask} />
      <FilterControls currentFilter={filter} onFilterChange={setFilter} />
      <div ref={taskListRef}>
        <TaskList
          tasks={visibleTasks}
          onToggle={handleToggle}
          onEdit={handleEdit}
          onDelete={handleDelete}
        />
      </div>
      <Toast
        message={toast.message}
        visible={toast.visible}
        onDismiss={dismissToast}
      />
    </div>
  )
}
