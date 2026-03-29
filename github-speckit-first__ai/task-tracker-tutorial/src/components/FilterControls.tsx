import type { Filter } from '../types'

interface FilterControlsProps {
  currentFilter: Filter
  onFilterChange: (filter: Filter) => void
}

const FILTERS: { value: Filter; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'active', label: 'Active' },
  { value: 'completed', label: 'Completed' },
]

export function FilterControls({
  currentFilter,
  onFilterChange,
}: FilterControlsProps) {
  return (
    <div className="filter-controls">
      <div className="filter-buttons" aria-label="Filter tasks">
        {FILTERS.map(({ value, label }) => (
          <button
            key={value}
            onClick={() => onFilterChange(value)}
            aria-pressed={currentFilter === value}
            className={currentFilter === value ? 'filter-active' : ''}
          >
            {label}
          </button>
        ))}
      </div>
      <label htmlFor="filter-select" className="sr-only">
        Filter tasks
      </label>
      <select
        id="filter-select"
        className="filter-select"
        value={currentFilter}
        onChange={(e) => onFilterChange(e.target.value as Filter)}
      >
        {FILTERS.map(({ value, label }) => (
          <option key={value} value={value}>
            {label}
          </option>
        ))}
      </select>
    </div>
  )
}
