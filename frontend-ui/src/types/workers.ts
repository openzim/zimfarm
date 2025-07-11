import type { Resources } from '@/types/base'
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
}
