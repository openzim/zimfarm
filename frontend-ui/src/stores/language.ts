import type { Config } from '@/config'
import constants from '@/constants'
import { useLoadingStore } from '@/stores/loading'
import type { ListResponse } from '@/types/base'
import { type Language } from '@/types/language'
import httpRequest from '@/utils/httpRequest'
import { defineStore } from 'pinia'
import { inject, ref } from 'vue'

export const useLanguageStore = defineStore('language', () => {
  const languages = ref<Language[]>([])
  const error = ref<Error | null>(null)
  const loadingStore = useLoadingStore()
  const config = inject<Config>(constants.config)

  if (!config) {
    throw new Error('Config is not defined')
  }

  const service = httpRequest({
    baseURL: `${config.ZIMFARM_WEBAPI}/languages`,
  })

  const fetchLanguages = async (limit: number = 100) => {
    try {
      loadingStore.startLoading('Fetching languages...')
      const response = await service.get<null, ListResponse<Language>>('', { params: { limit } })
      languages.value = response.items
    } catch (_error) {
      console.error('Failed to fetch languages', _error)
      error.value = _error as Error
    } finally {
      loadingStore.stopLoading()
    }
  }

  return {
    languages,
    error,
    fetchLanguages,
  }
})
