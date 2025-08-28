import { useAuthStore } from '@/stores/auth'
import type { ListResponse } from '@/types/base'
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useContextStore = defineStore('context', () => {
  const contexts = ref<string[]>([])
  const error = ref<Error | null>(null)

  const authStore = useAuthStore()

  const fetchContexts = async (limit: number = 100) => {
    if (contexts.value.length > 0) {
      return contexts.value
    }
    try {
      const service = await authStore.getApiService('contexts')
      const response = await service.get<null, ListResponse<string>>('', { params: { limit } })
      contexts.value = response.items
      return contexts.value
    } catch (_error) {
      console.error('Failed to fetch contexts', _error)
      error.value = _error as Error
      return null
    }
  }

  return {
    contexts,
    error,
    fetchContexts,
  }
})
