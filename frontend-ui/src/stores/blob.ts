import { useAuthStore } from '@/stores/auth'
import type { ListResponse, Paginator } from '@/types/base'
import { defineStore } from 'pinia'
import { type Blob } from '@/types/blob'
import { ref } from 'vue'
import type { ErrorResponse } from '@/types/errors'
import { translateErrors } from '@/utils/errors'

export const useBlobStore = defineStore('blob', () => {
  const blobs = ref<Blob[]>([])
  const paginator = ref<Paginator>({
    page: 1,
    page_size: 20,
    skip: 0,
    limit: 20,
    count: 0,
  })
  const errors = ref<string[]>([])
  const authStore = useAuthStore()

  const fetchBlobs = async (scheduleName: string, skip: number = 0, limit: number = 100) => {
    try {
      const service = await authStore.getApiService('blobs')
      const response = await service.get<null, ListResponse<Blob>>(`/${scheduleName}`, {
        params: { limit, skip },
      })
      blobs.value = response.items
      paginator.value = response.meta
      errors.value = []
      return blobs.value
    } catch (_error) {
      console.error('Failed to fetch blobs', _error)
      errors.value = translateErrors(_error as ErrorResponse)
      return null
    }
  }

  return {
    // State
    blobs,
    paginator,
    errors,
    // Actions
    fetchBlobs,
  }
})
