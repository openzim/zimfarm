import type { ListResponse } from '@/types/base'
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useAuthStore } from './auth'
export const usePlatformStore = defineStore('platform', () => {
  const platforms = ref<string[]>([])
  const error = ref<Error | null>(null)

  const authStore = useAuthStore()

  const fetchPlatforms = async (limit: number = 100) => {
    if (platforms.value.length > 0) {
      return platforms.value
    }
    try {
      const service = await authStore.getApiService('platforms')
      const response = await service.get<null, ListResponse<string>>('', { params: { limit } })
      platforms.value = response.items
      return platforms.value
    } catch (_error) {
      console.error('Failed to fetch platforms', _error)
      error.value = _error as Error
      return null
    }
  }

  return {
    platforms,
    error,
    fetchPlatforms,
  }
})
