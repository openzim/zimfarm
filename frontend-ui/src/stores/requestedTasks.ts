import type { Config } from '@/config'
import constants from '@/constants'
import { useAuthStore } from '@/stores/auth'
import { useLoadingStore } from '@/stores/loading'
import type { ListResponse, Paginator } from '@/types/base'
import type { ErrorResponse } from '@/types/errors'
import { type RequestedTaskLight } from '@/types/requestedTasks'
import { translateErrors } from '@/utils/errors'
import httpRequest from '@/utils/httpRequest'
import { defineStore } from 'pinia'
import { inject, ref } from 'vue'

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
  const loadingStore = useLoadingStore()

  const config = inject<Config>(constants.config)

  if (!config) {
    throw new Error('Config is not defined')
  }
  const authStore = useAuthStore()



  let headers: Record<string, string> = {}
  if (authStore.token) {
    headers = {
      'Authorization': `Bearer ${authStore.token.access_token}`,
    }
  }

  const service = httpRequest({
    baseURL: `${config.ZIMFARM_WEBAPI}/requested-tasks`,
    headers,
  })

  const fetchRequestedTasks = async (limit: number = 100, skip: number = 0) => {
    try {
      loadingStore.startLoading('Fetching requested tasks...')
      const response = await service.get<null, ListResponse<RequestedTaskLight>>('', { params: { limit, skip } })

      requestedTasks.value = response.items
      paginator.value = response.meta

    } catch (_error) {
      console.error('Failed to fetch requested tasks', _error)
      errors.value = translateErrors(_error as ErrorResponse)
    } finally {
      loadingStore.stopLoading()
    }
  }

  const removeRequestedTask = async (id: string) => {
    try {
      loadingStore.startLoading('Removing requested task...')
      await service.delete(`/${id}`)

      // Remove the task from the local state
      const index = requestedTasks.value.findIndex(task => task.id === id)
      if (index !== -1) {
        requestedTasks.value.splice(index, 1)
        paginator.value.count = Math.max(0, paginator.value.count - 1)
      }

      return true
    } catch (_error) {
      console.error('Failed to remove requested task', _error)
      errors.value = translateErrors(_error as ErrorResponse)
      return false
    } finally {
      loadingStore.stopLoading()
    }
  }

  return {
    requestedTasks,
    errors,
    fetchRequestedTasks,
    removeRequestedTask,
    paginator,
  }
})
