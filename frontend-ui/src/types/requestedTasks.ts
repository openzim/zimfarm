import type { BaseTask, ConfigWithOnlyOfflinerAndResources } from '@/types/base'
import type { ExpandedRecipeConfig, RecipeNotification } from '@/types/recipe'

export interface RequestedTaskLight extends BaseTask {
  config: ConfigWithOnlyOfflinerAndResources
  requested_by: string
}

export interface NewRequestedTaskSchemaResponse {
  requested: string[]
}

export interface RequestedTaskFullSchema {
  config: ExpandedRecipeConfig
  events: Record<string, unknown>[]
  upload: Record<string, unknown>
  notification: RecipeNotification | null
  rank: number | null
  recipe_name: string | null
  version: string
  offliner: string
}
