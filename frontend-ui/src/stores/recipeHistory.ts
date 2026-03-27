import { useAuthStore } from '@/stores/auth'
import type { ListResponse, Paginator } from '@/types/base'
import type { ErrorResponse } from '@/types/errors'
import type { RecipeHistorySchema } from '@/types/recipe'
import { translateErrors } from '@/utils/errors'
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useRecipeHistoryStore = defineStore('recipeHistory', () => {
  const history = ref<RecipeHistorySchema[]>([])
  const errors = ref<string[]>([])
  const paginator = ref<Paginator>({
    page: 1,
    page_size: 20,
    skip: 0,
    limit: 20,
    count: 0,
  })

  const authStore = useAuthStore()

  const fetchHistory = async (recipeName: string, limit: number, skip: number) => {
    const service = await authStore.getApiService('recipes')
    try {
      const response = await service.get<null, ListResponse<RecipeHistorySchema>>(
        `/${recipeName}/history`,
        { params: { limit, skip } },
      )
      // Add the items to the history if they are not already in it
      const existingIds = new Set(history.value.map((h) => h.id))
      history.value = [
        ...history.value,
        ...response.items.filter((item) => !existingIds.has(item.id)),
      ].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      paginator.value = response.meta
      errors.value = []
      return history.value
    } catch (_error) {
      console.error('Failed to fetch recipe history', _error)
      errors.value = translateErrors(_error as ErrorResponse)
      return null
    }
  }

  const fetchHistoryEntry = async (recipeName: string, historyId: string) => {
    const service = await authStore.getApiService('recipes')
    try {
      const response = await service.get<null, RecipeHistorySchema>(
        `/${recipeName}/history/${historyId}`,
      )
      // Add the item to the history if it's not already in it
      const existingIds = new Set(history.value.map((h) => h.id))
      if (!existingIds.has(response.id)) {
        history.value = [...history.value, response].sort(
          (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
        )
      }
      errors.value = []
      return response
    } catch (_error) {
      console.error('Failed to fetch recipe history entry', _error)
      errors.value = translateErrors(_error as ErrorResponse)
      return null
    }
  }

  const revertToHistory = async (recipeName: string, historyId: string, comment?: string) => {
    const service = await authStore.getApiService('recipes')
    try {
      const data = { comment: comment ? comment : null }
      await service.patch<{ comment?: string } | null, { message: string }>(
        `/${recipeName}/revert/${historyId}`,
        data,
      )
      errors.value = []
      return true
    } catch (_error) {
      console.error(`Failed to revert to recipe history entry ${historyId}`, _error)
      errors.value = translateErrors(_error as ErrorResponse)
      return false
    }
  }

  const clearHistory = () => {
    history.value = []
    errors.value = []
    paginator.value = {
      page: 1,
      page_size: 20,
      skip: 0,
      limit: 20,
      count: 0,
    }
  }

  return {
    // State
    history,
    paginator,
    errors,
    // Actions
    fetchHistory,
    fetchHistoryEntry,
    clearHistory,
    revertToHistory,
  }
})
