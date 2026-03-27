import type { Resources, RecipeDuration } from '@/types/base'
import type { ExpandedRecipeConfig } from '@/types/recipe'
import type { TaskLight } from '@/types/tasks'

export interface DockerImageVersion {
  hash: string
  created_at: string
}

interface BaseWorker {
  name: string
  offliners: string[]
  last_seen: string
  cordoned: boolean
  admin_disabled: boolean
  contexts: Record<string, string | null>
  last_ip?: string
  ip_changed: boolean
  selfish: boolean
  docker_image: DockerImageVersion | null
}

export interface Worker extends BaseWorker {
  status: 'online' | 'offline'
  resources: Resources
  tasks: TaskLight[] // Will be populated with running tasks
  user_id: string
  display_name: string
}

export interface RunningTask {
  id: string
  config: ExpandedRecipeConfig
  recipe_name: string | null
  updated_at: string
  status: string
  timestamp: [string, string][]
  worker_name: string
  duration: RecipeDuration
  remaining: number
  eta: string
}

export interface WorkerMetrics extends BaseWorker {
  status: 'online' | 'offline'
  resources: Resources
  user_id: string
  display_name: string
  running_tasks: RunningTask[]
  nb_tasks_total: number
  nb_tasks_completed: number
  nb_tasks_succeeded: number
  nb_tasks_failed: number
  current_usage: Resources
}

export interface WorkerUpdateSchema {
  contexts: Record<string, string | null>
  admin_disabled: boolean | null
}
