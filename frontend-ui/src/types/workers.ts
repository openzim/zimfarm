import type { Resources, RecipeDuration } from '@/types/base'
import type { ExpandedRecipeConfig } from '@/types/recipe'
import type { TaskLight } from '@/types/tasks'

export interface DockerImageVersion {
  hash: string
  created_at: string
}

export interface Worker {
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
  resources: Resources
  tasks: TaskLight[] // Will be populated with running tasks
  account_id: string
  display_name: string
  status: 'online' | 'offline'
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

export interface WorkerMetrics extends Worker {
  running_tasks: RunningTask[]
  nb_tasks_total: number
  nb_tasks_completed: number
  nb_tasks_succeeded: number
  nb_tasks_failed: number
  current_usage: Resources
  ssh_keys: SshKeyRead[]
}

export interface WorkerUpdateSchema {
  contexts: Record<string, string | null>
  admin_disabled: boolean | null
}

export interface WorkerCreateSchema {
  name: string
  ssh_key: {
    key: string
  }
}

export interface BaseSshKey {
  key: string
  name: string
  type: string
}

export interface SshKeyRead extends BaseSshKey {
  added: string
  fingerprint: string
}
