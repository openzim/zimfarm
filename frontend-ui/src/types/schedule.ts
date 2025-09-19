import type {
  ConfigWithOnlyOffliner,
  DockerImage,
  MostRecentTask,
  Resources,
  ScheduleDuration,
} from '@/types/base'
import type { Language } from '@/types/language'

export interface OfflinerFlags {
  offliner_id: string
  [key: string]: unknown
}

export interface ScheduleConfig {
  platform?: string
  warehouse_path: string
  artifacts_globs?: string[]
  artifacts_globs_str?: string // generated field
  monitor: boolean
  image: DockerImage
  resources: Resources
  offliner: OfflinerFlags
}

export interface BaseScheduleHistorySchema {
  config: Record<string, unknown>
  name: string
  category: string
  enabled: boolean
  language_code: string
  tags: string[]
  periodicity: string
  context: string
}

export interface ScheduleHistorySchema extends BaseScheduleHistorySchema {
  id: string
  author: string
  created_at: string
  comment: string | null
}

export interface Schedule {
  language: Language
  duration: ScheduleDuration
  name: string
  category: string
  config: ExpandedScheduleConfig
  enabled: boolean
  tags: string[]
  periodicity: string
  notification: ScheduleNotification | null
  most_recent_task: MostRecentTask | null
  is_requested: boolean
  is_valid: boolean
  context: string
  version: string
  offliner: string
}

export interface ScheduleLight {
  name: string
  category: string
  most_recent_task: MostRecentTask | null
  config: ConfigWithOnlyOffliner
  language: Language
  enabled: boolean
  is_requested: boolean
  context: string
}

export interface ScheduleUpdateSchema {
  name: string | null
  language: string | null
  category: string | null
  periodicity: string | null
  tags: string[] | null
  enabled: boolean | null
  offliner: string | null
  warehouse_path: string | null
  image: DockerImage | null
  platform: string | null
  resources: Resources | null
  monitor: boolean | null
  flags: Record<string, unknown> | null
  artifacts_globs: string[] | null
  context: string | null
  comment: string | null
  version: string
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

export interface ExpandedScheduleDockerImage {
  name: string
  tag: string
}

export interface ExpandedScheduleConfig extends ScheduleConfig {
  image: ExpandedScheduleDockerImage
  mount_point: string
  command: string[]
  str_command: string
}
