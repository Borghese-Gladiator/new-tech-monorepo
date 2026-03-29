import { useState, useCallback } from 'react'

interface UseLocalStorageResult<T> {
  value: T
  setValue: (newValue: T | ((prev: T) => T)) => void
  storageError: boolean
}

export function useLocalStorage<T>(
  key: string,
  initialValue: T,
): UseLocalStorageResult<T> {
  const [storageError, setStorageError] = useState(false)

  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = localStorage.getItem(key)
      if (item === null) return initialValue
      const parsed = JSON.parse(item)
      if (!Array.isArray(parsed) && Array.isArray(initialValue)) {
        localStorage.removeItem(key)
        return initialValue
      }
      return parsed as T
    } catch {
      try {
        localStorage.removeItem(key)
      } catch {
        // storage may be completely unavailable
      }
      return initialValue
    }
  })

  const setValue = useCallback(
    (newValue: T | ((prev: T) => T)) => {
      setStoredValue((prev) => {
        const resolved =
          newValue instanceof Function ? newValue(prev) : newValue
        try {
          localStorage.setItem(key, JSON.stringify(resolved))
          setStorageError(false)
        } catch {
          setStorageError(true)
        }
        return resolved
      })
    },
    [key],
  )

  return { value: storedValue, setValue, storageError }
}
