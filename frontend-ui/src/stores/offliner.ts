import { useAuthStore } from '@/stores/auth'
import type { ListResponse } from '@/types/base'
import type { ErrorResponse } from '@/types/errors'
import { type OfflinerDefinitionResponse } from '@/types/offliner'
import { translateErrors } from '@/utils/errors'
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useOfflinerStore = defineStore('offliner', () => {
  const offliners = ref<string[]>([])
  const errors = ref<string[]>([])
  const offlinerDefinitions = ref<Record<string, OfflinerDefinitionResponse>>({})

  const authStore = useAuthStore()

  const fetchOffliners = async (limit: number = 100) => {
    if (offliners.value.length > 0) {
      return offliners.value
    }
    try {
      const service = await authStore.getApiService('offliners')
      const response = await service.get<null, ListResponse<string>>('', { params: { limit } })
      offliners.value = response.items
      errors.value = []
      return offliners.value
    } catch (_error) {
      console.error('Failed to fetch offliners', _error)
      errors.value = translateErrors(_error as ErrorResponse)
      return null
    }
  }

  const fetchOfflinerDefinition = async (offliner: string) => {
    if (offlinerDefinitions.value[offliner]) {
      return offlinerDefinitions.value[offliner]
    }

    try {
      const service = await authStore.getApiService('offliners')
      const response = await service.get<null, OfflinerDefinitionResponse>(`/${offliner}`)
      offlinerDefinitions.value[offliner] = response
      errors.value = []
      return offlinerDefinitions.value[offliner]
    } catch (_error) {
      console.error('Failed to fetch offliner definition', _error)
      errors.value = translateErrors(_error as ErrorResponse)
      return null
    }
  }

  return {
    // state
    offliners,
    errors,
    offlinerDefinitions,
    // actions
    fetchOffliners,
    fetchOfflinerDefinition,
  }
})
