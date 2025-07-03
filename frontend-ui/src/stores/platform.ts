import { useLoadingStore } from '@/stores/loading'
import type { ListResponse } from '@/types/base'
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useAuthStore } from './auth'
export const usePlatformStore = defineStore('platform', () => {
  const platforms = ref<string[]>([])
  const error = ref<Error | null>(null)

  const loadingStore = useLoadingStore()
  const authStore = useAuthStore()

  const fetchPlatforms = async (limit: number = 100) => {
    try {
      loadingStore.startLoading('Fetching platforms...')
      const service = await authStore.getApiService('platforms')
      const response = await service.get<null, ListResponse<string>>('', { params: { limit } })
      platforms.value = response.items
    } catch (_error) {
      console.error('Failed to fetch platforms', _error)
      error.value = _error as Error
    } finally {
      loadingStore.stopLoading()
    }
  }

  return {
    platforms,
    error,
    fetchPlatforms,
  }
})
