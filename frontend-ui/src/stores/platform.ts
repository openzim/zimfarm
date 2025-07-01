import type { Config } from '@/config'
import constants from '@/constants'
import { useLoadingStore } from '@/stores/loading'
import type { ListResponse } from '@/types/base'
import httpRequest from '@/utils/httpRequest'
import { defineStore } from 'pinia'
import { inject, ref } from 'vue'
export const usePlatformStore = defineStore('platform', () => {
  const platforms = ref<string[]>([])
  const error = ref<Error | null>(null)

  const config = inject<Config>(constants.config)
  const loadingStore = useLoadingStore()
  if (!config) {
    throw new Error('Config is not defined')
  }

  const service = httpRequest({
    baseURL: `${config.ZIMFARM_WEBAPI}/platforms`,
  })

  const fetchPlatforms = async (limit: number = 100) => {
    try {
      loadingStore.startLoading('Fetching platforms...')
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
