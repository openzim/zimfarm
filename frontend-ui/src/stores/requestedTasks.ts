import { useAuthStore } from '@/stores/auth'
import type { ListResponse, Paginator } from '@/types/base'
import type { ErrorResponse } from '@/types/errors'
import { type NewRequestedTaskSchemaResponse, type RequestedTaskLight } from '@/types/requestedTasks'
import { translateErrors } from '@/utils/errors'
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useRequestedTasksStore = defineStore('requestedTasks', () => {
  const requestedTasks = ref<RequestedTaskLight[]>([])
  const paginator = ref<Paginator>({
    page: 1,
    page_size: 100,
    skip: 0,
    limit: 100,
    count: 0,
  })

  const errors = ref<string[]>([])
  const authStore = useAuthStore()



  const fetchRequestedTasks = async (limit: number = 100, skip: number = 0) => {
    const service = await authStore.getApiService('requested-tasks')
    try {
      const response = await service.get<null, ListResponse<RequestedTaskLight>>('', { params: { limit, skip } })

      requestedTasks.value = response.items
      paginator.value = response.meta
      errors.value = []

    } catch (_error) {
      errors.value = translateErrors(_error as ErrorResponse)
    }
  }

  const removeRequestedTask = async (id: string) => {
    try {
      const service = await authStore.getApiService('requested-tasks')
      await service.delete(`/${id}`)

      // Remove the task from the local state
      const index = requestedTasks.value.findIndex(task => task.id === id)
      if (index !== -1) {
        requestedTasks.value.splice(index, 1)
        paginator.value.count = Math.max(0, paginator.value.count - 1)
      }

      return true
    } catch (_error) {
      errors.value = translateErrors(_error as ErrorResponse)
      return false
    }
  }

  const requestTasks = async (schedulesNames: string[]) => {
    try {
      const service = await authStore.getApiService('requested-tasks')
      const response = await service.post<{ schedule_names: string[] }, NewRequestedTaskSchemaResponse>('', { schedule_names: schedulesNames })
      return response
    } catch (_error) {
      errors.value = translateErrors(_error as ErrorResponse)
      return null
    }
  }

  return {
    // State
    requestedTasks,
    errors,
    paginator,
    // Actions
    fetchRequestedTasks,
    removeRequestedTask,
    requestTasks,
  }
})
