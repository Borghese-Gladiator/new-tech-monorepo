export interface Task {
  id: string
  title: string
  isComplete: boolean
  createdAt: number
}

export type Filter = 'all' | 'active' | 'completed'
