import { useAuthStore } from '@/stores/auth'
import type { ListResponse, Paginator } from '@/types/base'
import { defineStore } from 'pinia'
import { type Blob, type CreateBlob } from '@/types/blob'
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

  const createBlob = async (scheduleName: string, request: CreateBlob) => {
    try {
      const service = await authStore.getApiService('blobs')
      const response = await service.post<CreateBlob, Blob>(`/${scheduleName}`, request)
      return response
    } catch (_error) {
      console.error('Failed to create blob', _error)
      errors.value = translateErrors(_error as ErrorResponse)
      return null
    }
  }

  const updateBlob = async (blobID: string, updates: { comments?: string; data?: string }) => {
    try {
      const service = await authStore.getApiService('blobs')
      const response = await service.patch<typeof updates, Blob>(`/${blobID}`, updates)
      return response
    } catch (_error) {
      console.error('Failed to update blob', _error)
      errors.value = translateErrors(_error as ErrorResponse)
      return null
    }
  }

  const deleteBlob = async (blobID: string) => {
    try {
      const service = await authStore.getApiService('blobs')
      await service.delete<null, null>(`/${blobID}`)
    } catch (_error) {
      console.error('Failed to delete blob', _error)
      errors.value = translateErrors(_error as ErrorResponse)
      return null
    }
  }

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

  const fetchBlob = async (scheduleName: string, checksum: string, flagName: string) => {
    try {
      const service = await authStore.getApiService('blobs')
      const response = await service.get<null, Blob>(`/${scheduleName}/${flagName}/${checksum}`)
      return response
    } catch (_error) {
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
    fetchBlob,
    createBlob,
    updateBlob,
    deleteBlob,
  }
})
