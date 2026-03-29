import { describe, it, expect, beforeEach, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useLocalStorage } from '../../src/hooks/useLocalStorage'

beforeEach(() => {
  localStorage.clear()
})

describe('useLocalStorage', () => {
  it('returns initial value when storage is empty', () => {
    const { result } = renderHook(() =>
      useLocalStorage('test-key', []),
    )
    expect(result.current.value).toEqual([])
    expect(result.current.storageError).toBe(false)
  })

  it('reads existing value from storage', () => {
    localStorage.setItem('test-key', JSON.stringify([{ id: '1' }]))
    const { result } = renderHook(() =>
      useLocalStorage('test-key', []),
    )
    expect(result.current.value).toEqual([{ id: '1' }])
  })

  it('persists new value to storage', () => {
    const { result } = renderHook(() =>
      useLocalStorage<string[]>('test-key', []),
    )
    act(() => {
      result.current.setValue(['a', 'b'])
    })
    expect(result.current.value).toEqual(['a', 'b'])
    expect(JSON.parse(localStorage.getItem('test-key')!)).toEqual([
      'a',
      'b',
    ])
  })

  it('accepts a function updater', () => {
    const { result } = renderHook(() =>
      useLocalStorage<number[]>('test-key', [1]),
    )
    act(() => {
      result.current.setValue((prev) => [...prev, 2])
    })
    expect(result.current.value).toEqual([1, 2])
  })

  it('recovers from corrupt JSON by returning initial value', () => {
    localStorage.setItem('test-key', 'not-json!!!')
    const { result } = renderHook(() =>
      useLocalStorage('test-key', []),
    )
    expect(result.current.value).toEqual([])
  })

  it('recovers when stored value is wrong type (non-array)', () => {
    localStorage.setItem('test-key', '"a string"')
    const { result } = renderHook(() =>
      useLocalStorage<string[]>('test-key', []),
    )
    expect(result.current.value).toEqual([])
  })

  it('sets storageError when setItem throws QuotaExceededError', () => {
    const { result } = renderHook(() =>
      useLocalStorage<string[]>('test-key', []),
    )
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new DOMException('quota exceeded', 'QuotaExceededError')
    })
    act(() => {
      result.current.setValue(['overflow'])
    })
    expect(result.current.storageError).toBe(true)
    expect(result.current.value).toEqual(['overflow'])
    vi.restoreAllMocks()
  })
})
