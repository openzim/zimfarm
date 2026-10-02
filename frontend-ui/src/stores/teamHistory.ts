import { useAuthStore } from '@/stores/auth'
import type { ListResponse, Paginator } from '@/types/base'
import type { ErrorResponse } from '@/types/errors'
import type { Team, TeamHistory } from '@/types/team'
import { translateErrors } from '@/utils/errors'
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useTeamHistoryStore = defineStore('teamHistory', () => {
  const history = ref<TeamHistory[]>([])
  const errors = ref<string[]>([])
  const paginator = ref<Paginator>({
    page: 1,
    page_size: 20,
    skip: 0,
    limit: 20,
    count: 0,
  })

  const authStore = useAuthStore()

  const fetchHistory = async (teamName: string, limit: number = 20, skip: number = 0) => {
    const service = await authStore.getApiService('teams')
    try {
      const response = await service.get<null, ListResponse<TeamHistory>>(`/${teamName}/history`, {
        params: { limit, skip },
      })
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
      console.error('Failed to fetch team history', _error)
      errors.value = translateErrors(_error as ErrorResponse)
      return null
    }
  }

  const fetchHistoryEntry = async (teamName: string, historyId: string) => {
    const service = await authStore.getApiService('teams')
    try {
      const response = await service.get<null, TeamHistory>(`/${teamName}/history/${historyId}`)
      const existingIds = new Set(history.value.map((h) => h.id))
      if (!existingIds.has(response.id)) {
        history.value = [...history.value, response].sort(
          (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
        )
      }
      errors.value = []
      return response
    } catch (_error) {
      console.error('Failed to fetch team history entry', _error)
      errors.value = translateErrors(_error as ErrorResponse)
      return null
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

  const revertToHistory = async (teamName: string, historyId: string, comment?: string) => {
    const service = await authStore.getApiService('teams')
    try {
      const data = { comment: comment ? comment : null }
      const response = await service.patch<{ comment?: string } | null, Team>(
        `/${teamName}/revert/${historyId}`,
        data,
      )
      errors.value = []
      return response
    } catch (_error) {
      console.error(`Failed to revert team ${teamName} to history entry ${historyId}`, _error)
      errors.value = translateErrors(_error as ErrorResponse)
      return null
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
