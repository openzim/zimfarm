import { useAuthStore } from '@/stores/auth'
import type { ListResponse, Paginator } from '@/types/base'
import type { ErrorResponse } from '@/types/errors'
import type { Recipe, RecipeLight, RecipeUpdateSchema } from '@/types/recipe'
import { translateErrors } from '@/utils/errors'
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useRecipeStore = defineStore('recipe', () => {
  const recipe = ref<Recipe | null>(null)
  const errors = ref<string[]>([])
  const recipes = ref<RecipeLight[]>([])
  const defaultLimit = ref<number>(Number(localStorage.getItem('recipes-table-limit') || 20))
  const paginator = ref<Paginator>({
    page: 1,
    page_size: defaultLimit.value,
    skip: 0,
    limit: defaultLimit.value,
    count: 0,
  })
  const authStore = useAuthStore()

  const fetchRecipe = async (
    recipeName: string,
    forceReload: boolean = false,
    hideSecrets: boolean = false,
  ) => {
    const service = await authStore.getApiService('recipes')
    // Check if we already have the recipe and don't need to force reload
    if (!forceReload && recipe.value && recipe.value.name === recipeName) {
      return recipe.value
    }

    try {
      errors.value = []
      // Clear current recipe until we receive the right one
      recipe.value = null

      const response = await service.get<null, Recipe>(`/${recipeName}`, {
        params: { hide_secrets: hideSecrets },
      })
      recipe.value = response
      // generate artifacts_globs_str
      recipe.value.config.artifacts_globs_str = recipe.value.config.artifacts_globs?.join('\n')
    } catch (_error) {
      console.error('Failed to load recipe', _error)
      errors.value = translateErrors(_error as ErrorResponse)
    }
    return recipe.value
  }

  const fetchRecipes = async (
    limit: number,
    skip: number,
    category: string[] | undefined,
    lang: string[] | undefined,
    tag: string[] | undefined,
    name: string | undefined,
    archived: boolean | undefined,
    offliner: string[] | undefined,
  ) => {
    const service = await authStore.getApiService('recipes')
    // filter out undefined values from params
    const cleanedParams = Object.fromEntries(
      Object.entries({
        limit,
        skip,
        category,
        lang,
        tag,
        name,
        archived,
        offliner,
      }).filter(([, value]) => !!value),
    )
    try {
      const response = await service.get<null, ListResponse<RecipeLight>>('', {
        params: cleanedParams,
      })
      recipes.value = response.items
      paginator.value = response.meta
      errors.value = []
      return recipes.value
    } catch (_error) {
      console.error('Failed to fetch recipes', _error)
      errors.value = translateErrors(_error as ErrorResponse)
      return null
    }
  }

  const fetchSimilarRecipes = async (
    recipeName: string,
    params: {
      limit: number
      skip: number
      category?: string[]
      lang?: string[]
      tag?: string[]
      name?: string
      archived?: boolean
    },
  ) => {
    const service = await authStore.getApiService('recipes')
    const cleanedParams = Object.fromEntries(
      Object.entries(params).filter(([, value]) => value !== undefined && value !== null),
    )
    try {
      const response = await service.get<null, ListResponse<RecipeLight>>(
        `/${recipeName}/similar`,
        {
          params: cleanedParams,
        },
      )
      errors.value = []
      return response
    } catch (_error) {
      console.error('Failed to fetch similar recipes', _error)
      errors.value = translateErrors(_error as ErrorResponse)
      return null
    }
  }

  const clearRecipe = () => {
    recipe.value = null
    errors.value = []
  }

  const cloneRecipe = async (recipeName: string, newRecipeName: string) => {
    const service = await authStore.getApiService('recipes')
    try {
      const response = await service.post<{ name: string }, { id: string }>(
        `/${recipeName}/clone`,
        {
          name: newRecipeName,
        },
      )
      return response
    } catch (_error) {
      console.error('Failed to clone recipe', _error)
      errors.value = translateErrors(_error as ErrorResponse)
      return null
    }
  }

  const fetchRecipeImageTags = async (recipeName: string, params: { hubName: string }) => {
    const service = await authStore.getApiService('recipes')
    try {
      const response = await service.get<null, ListResponse<string>>(`/${recipeName}/image-names`, {
        params: { hub_name: params.hubName },
      })
      return response.items
    } catch (_error) {
      console.error('Failed to fetch image tags', _error)
      errors.value = translateErrors(_error as ErrorResponse)
      return null
    }
  }

  const updateRecipe = async (recipeName: string, recipe: RecipeUpdateSchema) => {
    const service = await authStore.getApiService('recipes')
    try {
      const response = await service.patch<RecipeUpdateSchema, Recipe>(`/${recipeName}`, recipe)
      return response
    } catch (_error) {
      console.error('Failed to update recipe', _error)
      errors.value = translateErrors(_error as ErrorResponse)
      return null
    }
  }

  const deleteRecipe = async (recipeName: string) => {
    const service = await authStore.getApiService('recipes')
    try {
      await service.delete<null, null>(`/${recipeName}`)
      return true
    } catch (_error) {
      console.error('Failed to delete recipe', _error)
      errors.value = translateErrors(_error as ErrorResponse)
      return false
    }
  }

  const archiveRecipe = async (recipeName: string, comment?: string) => {
    const service = await authStore.getApiService('recipes')
    try {
      await service.patch<{ comment?: string }, { message: string }>(`/${recipeName}/archive`, {
        comment,
      })
      return true
    } catch (_error) {
      console.error('Failed to archive recipe', _error)
      errors.value = translateErrors(_error as ErrorResponse)
      return false
    }
  }

  const restoreRecipe = async (recipeName: string, comment?: string) => {
    const service = await authStore.getApiService('recipes')
    try {
      await service.patch<{ comment?: string }, { message: string }>(`/${recipeName}/restore`, {
        comment,
      })
      return true
    } catch (_error) {
      console.error('Failed to restore recipe', _error)
      errors.value = translateErrors(_error as ErrorResponse)
      return false
    }
  }

  const restoreRecipes = async (recipeNames: string[], comment?: string) => {
    const service = await authStore.getApiService('recipes')
    try {
      await service.post<{ recipe_names: string[]; comment?: string }, null>('/restore', {
        recipe_names: recipeNames,
        comment,
      })
      return true
    } catch (_error) {
      console.error('Failed to restore recipes', _error)
      errors.value = translateErrors(_error as ErrorResponse)
      return false
    }
  }

  const validateRecipe = async (recipeName: string) => {
    const service = await authStore.getApiService('recipes')
    errors.value = []
    try {
      await service.get<null, null>(`/${recipeName}/validate`)
      return true
    } catch (_error) {
      console.error('Failed to validate recipe', _error)
      errors.value = translateErrors(_error as ErrorResponse)
      return false
    }
  }

  const savePaginatorLimit = (limit: number) => {
    localStorage.setItem('recipes-table-limit', limit.toString())
  }

  return {
    // State
    defaultLimit,
    recipe,
    recipes,
    paginator,
    errors,
    history,
    // Actions
    fetchRecipe,
    fetchRecipes,
    fetchSimilarRecipes,
    clearRecipe,
    cloneRecipe,
    fetchRecipeImageTags,
    updateRecipe,
    deleteRecipe,
    archiveRecipe,
    restoreRecipe,
    restoreRecipes,
    validateRecipe,
    savePaginatorLimit,
  }
})
