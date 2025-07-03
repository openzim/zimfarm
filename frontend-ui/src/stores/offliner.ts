import type { ListResponse } from '@/types/base'
import type { ErrorResponse } from '@/types/errors'
import { translateErrors } from '@/utils/errors'
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useAuthStore } from './auth'

export const useOfflinerStore = defineStore('offliner', () => {
  const offliners = ref<string[]>([])
  const error = ref<string[]>([])

  const authStore = useAuthStore()


  const fetchOffliners = async (limit: number = 100) => {
    try {
      const service = await authStore.getApiService('offliners')
      const response = await service.get<null, ListResponse<string>>('', { params: { limit } })
      offliners.value = response.items
    } catch (_error) {
      console.error('Failed to fetch offliners', _error)
      error.value = translateErrors(_error as ErrorResponse)
    }
  }

  return {
    offliners,
    error,
    fetchOffliners,
  }
})
