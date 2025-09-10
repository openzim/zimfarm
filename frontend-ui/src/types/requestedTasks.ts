import type { BaseTask, ConfigWithOnlyOfflinerAndResources } from '@/types/base'
import type { ExpandedScheduleConfig, ScheduleNotification } from '@/types/schedule'

export interface RequestedTaskLight extends BaseTask {
  config: ConfigWithOnlyOfflinerAndResources
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
}
