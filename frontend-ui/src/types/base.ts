export interface Paginator {
  count: number
  skip: number
  limit: number
  page_size: number
  page: number
}

export interface ListResponse<T> {
  meta: Paginator
  items: T[]
}

export interface Resources {
  cpu: number
  memory: number
  disk: number
  shm?: number
}

export interface ConfigWithOnlyResources {
  resources: Resources
}

export interface ConfigWithOnlyOfflinerAndResources extends ConfigWithOnlyResources {
  offliner: string
}

export interface DockerImage {
  name: string
  tag: string
}

export interface ScheduleDuration {
  value: number
  on: string
  worker_name: string | null
  default: boolean
}


export interface EventNotification {
  mailgun: string[] | null
  webhook: string[] | null
  slack: string[] | null
}

export interface ScheduleNotification {
  requested: EventNotification | null
  started: EventNotification | null
  ended: EventNotification | null
}

export interface MostRecentTask {
  id: string
  status: string
  updated_at: string
}

export interface BaseTask {
  id: string
  status: string
  timestamp: Record<string, unknown>
  schedule_name: string
  worker_name: string
  updated_at: string
  original_schedule_name: string
  duration?: string
}
