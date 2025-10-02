import type { BaseTask, ConfigWithOnlyResources, TaskStatus } from '@/types/base'
import type { ExpandedScheduleConfig, ScheduleNotification } from '@/types/schedule'

export interface TaskLight extends BaseTask {
  config: ConfigWithOnlyResources
}

export interface TaskEvent {
  code: TaskStatus
  timestamp: string
}

export interface TaskFileInfo {
  id: string
  counter: Record<string, number>
  article_count: number
  media_count: number
  size: number
  metadata: Record<string, string>
}

export interface TaskFile {
  name: string
  size: number
  created_timestamp: string
  uploaded_timestamp?: string
  check_timestamp?: string
  status: string
  check_result?: number
  check_details?: Record<string, unknown>
  info?: TaskFileInfo
}

export interface TaskContainer {
  command: string[]
  exit_code?: number
  stdout?: string
  stderr?: string
  log: string
  image: string
  artifacts?: string
  progress?: {
    overall: number
    done: number
    total: number
  } | null
  stats?: {
    memory?: {
      max_usage?: number | null
    }
  }
}

export interface TaskDebug {
  exception?: string
  traceback?: string
  log?: string
}

export interface UploadConfig {
  expiration: number
  upload_uri: string
}

export interface ZimUploadConfig extends UploadConfig {
  zimcheck: string
}

export interface TaskUpload {
  zim: ZimUploadConfig
  logs: UploadConfig
  artifacts?: UploadConfig
}

export interface Task extends BaseTask {
  config: ExpandedScheduleConfig
  events: TaskEvent[]
  debug: TaskDebug
  canceled_by: string | null
  container: TaskContainer
  notification: ScheduleNotification | null
  files: Record<string, TaskFile>
  upload: TaskUpload
  version: string
  offliner: string
}
