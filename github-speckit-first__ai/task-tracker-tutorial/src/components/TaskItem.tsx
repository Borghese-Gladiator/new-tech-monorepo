import { useState, useRef, useEffect } from 'react'
import type { Task } from '../types'

interface TaskItemProps {
  task: Task
  onToggle: (id: string) => void
  onEdit: (id: string, newTitle: string) => void
  onDelete: (id: string) => void
}

export function TaskItem({ task, onToggle, onEdit, onDelete }: TaskItemProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editTitle, setEditTitle] = useState(task.title)
  const editInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (isEditing) {
      editInputRef.current?.focus()
    }
  }, [isEditing])

  function handleSave() {
    const trimmed = editTitle.trim()
    if (!trimmed) {
      setEditTitle(task.title)
      setIsEditing(false)
      return
    }
    onEdit(task.id, trimmed)
    setIsEditing(false)
  }

  function handleCancel() {
    setEditTitle(task.title)
    setIsEditing(false)
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter') handleSave()
    if (e.key === 'Escape') handleCancel()
  }

  return (
    <li className={`task-item ${task.isComplete ? 'task-completed' : ''}`} data-task-id={task.id}>
      <input
        type="checkbox"
        checked={task.isComplete}
        onChange={() => onToggle(task.id)}
        aria-label={`Mark "${task.title}" as ${task.isComplete ? 'active' : 'complete'}`}
      />
      {isEditing ? (
        <input
          ref={editInputRef}
          type="text"
          className="edit-input"
          value={editTitle}
          onChange={(e) => setEditTitle(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={handleSave}
          aria-label={`Edit title for "${task.title}"`}
        />
      ) : (
        <span className="task-title">{task.title}</span>
      )}
      <div className="task-actions">
        {!isEditing && (
          <button
            onClick={() => {
              setEditTitle(task.title)
              setIsEditing(true)
            }}
            aria-label={`Edit "${task.title}"`}
          >
            Edit
          </button>
        )}
        <button
          onClick={() => onDelete(task.id)}
          className="btn-danger"
          aria-label={`Delete "${task.title}"`}
        >
          Delete
        </button>
      </div>
    </li>
  )
}
