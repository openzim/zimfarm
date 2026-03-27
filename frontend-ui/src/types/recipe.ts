import type {
  ConfigWithOnlyOffliner,
  DockerImage,
  MostRecentTask,
  Resources,
  RecipeDuration,
} from '@/types/base'
import type { Language } from '@/types/language'

export interface OfflinerFlags {
  offliner_id: string
  [key: string]: unknown
}

export interface RecipeConfig {
  platform?: string
  warehouse_path: string
  artifacts_globs?: string[]
  artifacts_globs_str?: string // generated field
  monitor: boolean
  image: DockerImage
  resources: Resources
  offliner: OfflinerFlags
}

export interface BaseRecipeHistorySchema {
  config: Record<string, unknown>
  name: string
  category: string
  enabled: boolean
  language_code: string
  tags: string[]
  periodicity: string
  context: string
  archived: boolean
  offliner_definition_version?: string
  notification: RecipeNotification | null
}

export interface RecipeHistorySchema extends BaseRecipeHistorySchema {
  id: string
  author: string
  created_at: string
  comment: string | null
}

export interface Recipe {
  language: Language
  duration: RecipeDuration
  name: string
  category: string
  config: ExpandedRecipeConfig
  enabled: boolean
  tags: string[]
  periodicity: string
  notification: RecipeNotification | null
  most_recent_task: MostRecentTask | null
  is_requested: boolean
  archived: boolean
  is_valid: boolean
  context: string
  version: string
  offliner: string
}

export interface RecipeLight {
  name: string
  category: string
  most_recent_task: MostRecentTask | null
  config: ConfigWithOnlyOffliner
  language: Language
  enabled: boolean
  is_requested: boolean
  archived: boolean
  context: string
}

export interface RecipeUpdateSchema {
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
  notification: RecipeNotification | null
  version: string
}

export interface EventNotification {
  mailgun: string[] | null
  webhook: string[] | null
  slack: string[] | null
}

export interface RecipeNotification {
  requested: EventNotification | null
  started: EventNotification | null
  ended: EventNotification | null
}

export interface ExpandedRecipeDockerImage {
  name: string
  tag: string
}

export interface ExpandedRecipeConfig extends RecipeConfig {
  image: ExpandedRecipeDockerImage
  mount_point: string
  command: string[]
  str_command: string
}
