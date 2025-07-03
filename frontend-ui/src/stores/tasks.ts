import { useAuthStore } from '@/stores/auth'
import { useLoadingStore } from '@/stores/loading'
import type { ListResponse, Paginator } from '@/types/base'
import type { ErrorResponse } from '@/types/errors'
import { type TaskLight } from '@/types/tasks'
import { translateErrors } from '@/utils/errors'
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useTasksStore = defineStore('tasks', () => {
  const tasks = ref<TaskLight[]>([])
  const paginator = ref<Paginator>({
    page: 1,
    page_size: 100,
    skip: 0,
    limit: 100,
    count: 0,
  })
  const errors = ref<string[]>([])

  const loadingStore = useLoadingStore()
  const authStore = useAuthStore()


  const fetchTasks = async (limit: number = 100, skip: number = 0, status: string[]) => {
    try {
      loadingStore.startLoading('Fetching tasks...')
      const service = await authStore.getApiService('tasks')
      const response = await service.get<null, ListResponse<TaskLight>>('', { params: { limit, skip, status } })

      tasks.value = response.items
      paginator.value = response.meta

    } catch (_error) {
      console.error('Failed to fetch tasks', _error)
      errors.value = translateErrors(_error as ErrorResponse)
    } finally {
      loadingStore.stopLoading()
    }
  }

  return {
    tasks,
    paginator,
    errors,
    fetchTasks,
  }
})
