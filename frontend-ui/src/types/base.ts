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
  cap_add: string[]
  cap_drop: string[]
}

export interface ConfigWithOnlyResources {
  resources: Resources
}

export interface ConfigWithOnlyOffliner {
  offliner: string
}

export interface ConfigWithOnlyOfflinerAndResources
  extends ConfigWithOnlyResources,
    ConfigWithOnlyOffliner {}

export interface DockerImage {
  name: string
  tag: string
}

export interface WorkerScheduleDuration {
  value: number
  on: string
  worker_name: string | undefined
  default: boolean
}

export interface ScheduleDuration {
  available: boolean
  default: WorkerScheduleDuration | null
  workers: Record<string, WorkerScheduleDuration> | null
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
  timestamp: [string, string][] // [status, datetime] tuples
}
export enum TaskStatus {
  requested = 'requested',
  reserved = 'reserved',
  started = 'started',
  scraper_started = 'scraper_started',
  scraper_running = 'scraper_running',
  scraper_completed = 'scraper_completed',
  scraper_killed = 'scraper_killed',
  failed = 'failed',
  cancel_requested = 'cancel_requested',
  canceled = 'canceled',
  succeeded = 'succeeded',
  update = 'update',
  created_file = 'created_file',
  uploaded_file = 'uploaded_file',
  failed_file = 'failed_file',
  checked_file = 'checked_file',
}

export interface BaseTask {
  id: string
  status: string
  timestamp: [string, string][] // [status, datetime] tuples
  schedule_name: string | null
  worker_name: string
  updated_at: string
  requested_by: string
  original_schedule_name: string
  context: string
  priority: number
}
