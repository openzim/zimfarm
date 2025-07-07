import type { ConfigWithOnlyOffliner, DockerImage, MostRecentTask, Resources, ScheduleDuration, ScheduleNotification } from '@/types/base'
import type { Language } from '@/types/language'

export interface ScheduleConfig {
  platform?: string
  warehouse_path: string
  artifacts_globs?: string[]
  monitor: boolean
  image: DockerImage
  resources: Resources
  offliner: Record<string, unknown>
}

export interface Schedule {
  language: Language
  durations: ScheduleDuration[]
  name: string
  category: string
  config: ScheduleConfig
  enabled: boolean
  tags: string[]
  periodicity: string
  notification: ScheduleNotification | null
  most_recent_task: MostRecentTask | null
  is_requested: boolean
}

export interface ScheduleLight {
    name: string
    category: string
    most_recent_task: MostRecentTask | null
    config: ConfigWithOnlyOffliner
    language: Language
    enabled: boolean
    is_requested: boolean
}

