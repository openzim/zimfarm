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

  const fetchOfflinerVersions = async (offliner: string, limit: number = 100) => {
    try {
      const service = await authStore.getApiService('offliners')
      const response = await service.get<null, ListResponse<string>>(`/${offliner}/versions`, {
        params: { limit },
      })
      return response.items
    } catch (_error) {
      console.error('Failed to fetch offliner versions', _error)
      errors.value = translateErrors(_error as ErrorResponse)
      return null
    }
  }

  const fetchOfflinerDefinitionByVersion = async (offliner: string, version: string) => {
    if (offlinerDefinitions.value[`${offliner}-${version}`]) {
      return offlinerDefinitions.value[`${offliner}-${version}`]
    }

    try {
      const service = await authStore.getApiService('offliners')
      const response = await service.get<null, OfflinerDefinitionResponse>(
        `/${offliner}/${version}`,
      )
      offlinerDefinitions.value[`${offliner}-${version}`] = response
      errors.value = []
      return offlinerDefinitions.value[`${offliner}-${version}`]
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
    fetchOfflinerVersions,
    fetchOfflinerDefinitionByVersion,
  }
})
