import { useAuthStore } from '@/stores/auth'
import type { ListResponse } from '@/types/base'
import type { ErrorResponse } from '@/types/errors'
import { translateErrors } from '@/utils/errors'
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useContextStore = defineStore('context', () => {
  const contexts = ref<string[]>([])
  const errors = ref<string[]>([])

  const authStore = useAuthStore()

  const fetchContexts = async (limit: number = 100) => {
    try {
      const service = await authStore.getApiService('contexts')
      const response = await service.get<null, ListResponse<string>>('', { params: { limit } })
      contexts.value = response.items
      return contexts.value
    } catch (_error) {
      console.error('Failed to fetch contexts', _error)
      errors.value = translateErrors(_error as ErrorResponse)
      return null
    }
  }

  return {
    contexts,
    errors,

    fetchContexts,
  }
})
