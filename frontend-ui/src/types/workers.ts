import type { Resources, ScheduleDuration } from '@/types/base'
import type { ExpandedScheduleConfig } from '@/types/schedule'
import type { TaskLight } from '@/types/tasks'

export interface Worker {
  name: string
  status: 'online' | 'offline'
  last_seen: string
  last_ip: string | null
  resources: Resources
  tasks: TaskLight[] // Will be populated with running tasks
  offliners: string[]
  username: string
  contexts: string[]
}

export interface RunningTask {
  id: string
  config: ExpandedScheduleConfig
  schedule_name: string | null
  updated_at: string
  timestamp: [string, string][]
  worker_name: string
  duration: ScheduleDuration
  remaining: number
  eta: string
}

export interface WorkerMetrics {
  name: string
  status: 'online' | 'offline'
  last_seen: string | null
  last_ip: string | null
  resources: Resources
  offliners: string[]
  username: string
  contexts: string[]
  running_tasks: RunningTask[]
  nb_tasks_total: number
  nb_tasks_completed: number
  nb_tasks_succeeded: number
  nb_tasks_failed: number
  current_usage: Resources
}

export interface WorkerUpdateSchema {
  contexts: string[]
}
