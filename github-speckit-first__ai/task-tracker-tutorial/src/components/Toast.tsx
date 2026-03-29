import { useEffect } from 'react'

interface ToastProps {
  message: string
  visible: boolean
  onDismiss: () => void
}

export function Toast({ message, visible, onDismiss }: ToastProps) {
  useEffect(() => {
    if (!visible) return
    const timer = setTimeout(onDismiss, 3000)
    return () => clearTimeout(timer)
  }, [visible, onDismiss])

  return (
    <div
      role="status"
      aria-live="polite"
      className="toast"
      style={{ opacity: visible ? 1 : 0, pointerEvents: visible ? 'auto' : 'none' }}
    >
      {visible ? message : ''}
    </div>
  )
}
