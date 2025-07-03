import { useAuthStore } from '@/stores/auth'
import type { ListResponse } from '@/types/base'
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useTagStore = defineStore('tag', () => {
  const tags = ref<string[]>([])
  const error = ref<Error | null>(null)

  const authStore = useAuthStore()

  const fetchTags = async (limit: number = 100) => {
    try {
      const service = await authStore.getApiService('tags')
      const response = await service.get<null, ListResponse<string>>('', { params: { limit } })
      tags.value = response.items
    } catch (_error) {
      console.error('Failed to fetch tags', _error)
      error.value = _error as Error
    }
  }

  return {
    tags,
    error,
    fetchTags,
  }
})
