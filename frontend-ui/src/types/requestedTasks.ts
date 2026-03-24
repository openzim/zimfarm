import type { BaseTask, ConfigWithOnlyOfflinerAndResources } from '@/types/base'
import type { ExpandedRecipeConfig, RecipeNotification } from '@/types/recipe'

export interface BaseRequestedTask {
  id: string
  status: string
  timestamp: [string, string][] // [status, datetime] tuples
  requested_by: string
  priority: number
  recipe_name: string | null
  original_recipe_name: string
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
  config: ExpandedRecipeConfig
  events: Record<string, unknown>[]
  upload: Record<string, unknown>
  notification: RecipeNotification | null
  rank: number | null
  recipe_name: string | null
  version: string
  offliner: string
}
