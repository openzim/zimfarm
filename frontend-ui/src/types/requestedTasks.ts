import type { ConfigWithOnlyOfflinerAndResources } from '@/types/base'
import type { ExpandedScheduleConfig, ScheduleNotification } from '@/types/schedule'

export interface BaseRequestedTask {
  id: string
  status: string
  timestamp: [string, string][] // [status, datetime] tuples
  requested_by: string
  priority: number
  schedule_name: string | null
  original_schedule_name: string
  worker_name: string | null
  updated_at: string
  context: string
}

export interface RequestedTaskLight extends BaseRequestedTask {
  config: ConfigWithOnlyOfflinerAndResources
  requested_by: string
}

export interface NewRequestedTaskSchemaResponse {
  requested: string[]
}

export interface RequestedTaskFullSchema {
  config: ExpandedScheduleConfig
  events: Record<string, unknown>[]
  upload: Record<string, unknown>
  notification: ScheduleNotification | null
  rank: number | null
  schedule_name: string | null
  version: string
  offliner: string
}
