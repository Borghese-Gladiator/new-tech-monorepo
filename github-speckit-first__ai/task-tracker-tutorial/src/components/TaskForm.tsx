import { useState } from 'react'

interface TaskFormProps {
  onAddTask: (title: string) => void
}

export function TaskForm({ onAddTask }: TaskFormProps) {
  const [title, setTitle] = useState('')
  const [error, setError] = useState('')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const trimmed = title.trim()
    if (!trimmed) {
      setError('Please enter a task title')
      return
    }
    onAddTask(trimmed)
    setTitle('')
    setError('')
  }

  return (
    <form className="task-form" onSubmit={handleSubmit}>
      <label htmlFor="new-task" className="sr-only">
        New task title
      </label>
      <input
        id="new-task"
        type="text"
        value={title}
        onChange={(e) => {
          setTitle(e.target.value)
          if (error) setError('')
        }}
        placeholder="What needs to be done?"
        aria-invalid={!!error}
        aria-describedby={error ? 'task-form-error' : undefined}
      />
      <button type="submit">Add</button>
      {error && (
        <p id="task-form-error" className="form-error" role="alert">
          {error}
        </p>
      )}
    </form>
  )
}
