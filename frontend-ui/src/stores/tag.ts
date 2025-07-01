import type { Config } from '@/config'
import constants from '@/constants'
import { useLoadingStore } from '@/stores/loading'
import type { ListResponse } from '@/types/base'
import httpRequest from '@/utils/httpRequest'
import { defineStore } from 'pinia'
import { inject, ref } from 'vue'

export const useTagStore = defineStore('tag', () => {
  const tags = ref<string[]>([])
  const error = ref<Error | null>(null)

  const config = inject<Config>(constants.config)
  if (!config) {
    throw new Error('Config is not defined')
  }

  const service = httpRequest({
    baseURL: `${config.ZIMFARM_WEBAPI}/tags`,
  })

  const loadingStore = useLoadingStore()

  const fetchTags = async (limit: number = 100) => {
    try {
      loadingStore.startLoading('Fetching tags...')
      const response = await service.get<null, ListResponse<string>>('', { params: { limit } })
      tags.value = response.items
    } catch (_error) {
      console.error('Failed to fetch tags', _error)
      error.value = _error as Error
    } finally {
      loadingStore.stopLoading()
    }
  }

  return {
    tags,
    error,
    fetchTags,
  }
})
