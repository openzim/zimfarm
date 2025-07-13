import { useAuthStore } from '@/stores/auth'
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

  const authStore = useAuthStore()


  const fetchTasks = async (params: {
    limit?: number
    skip?: number
    status?: string[]
    scheduleName?: string
  } = {}) => {
    const { limit = 100, skip = 0, status = [], scheduleName = null } = params
    const cleanedParams = Object.fromEntries(
      Object.entries({
        limit,
        skip,
        status,
        schedule_name: scheduleName,
      })
      .filter(([, value]) => !!value)
    )
    try {
      const service = await authStore.getApiService('tasks')
      const response = await service.get<null, ListResponse<TaskLight>>('', { params: cleanedParams })
      tasks.value = response.items
      paginator.value = response.meta
      errors.value = []
      return tasks.value
    } catch (_error) {
      console.error('Failed to fetch tasks', _error)
      errors.value = translateErrors(_error as ErrorResponse)
      return null
    }
  }

  const cancelTask = async (id: string) => {
    const service = await authStore.getApiService('tasks')
    try {
      await service.post(`/${id}/cancel`)
      return true
    } catch (_error) {
      console.error('Failed to cancel task', _error)
      errors.value = translateErrors(_error as ErrorResponse)
      return false
    }
  }

  return {
    tasks,
    paginator,
    errors,
    fetchTasks,
    cancelTask,
  }
})
