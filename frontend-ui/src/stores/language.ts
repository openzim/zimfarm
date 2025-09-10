import type { ListResponse } from '@/types/base'
import type { ErrorResponse } from '@/types/errors'
import { type Language } from '@/types/language'
import { translateErrors } from '@/utils/errors'
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useAuthStore } from './auth'

export const useLanguageStore = defineStore('language', () => {
  const languages = ref<Language[]>([])
  const error = ref<string[]>([])
  const authStore = useAuthStore()

  const fetchLanguages = async (limit: number = 400) => {
    if (languages.value.length > 0) {
      return languages.value
    }
    try {
      const service = await authStore.getApiService('languages')
      const response = await service.get<null, ListResponse<Language>>('', { params: { limit } })
      languages.value = response.items
      return languages.value
    } catch (_error) {
      console.error('Failed to fetch languages', _error)
      error.value = translateErrors(_error as ErrorResponse)
      return null
    }
  }

  return {
    languages,
    error,
    fetchLanguages,
  }
})
