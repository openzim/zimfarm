import type { Config } from '@/config'
import constants from '@/constants'
import { useLoadingStore } from '@/stores/loading'
import type { ListResponse, Paginator } from '@/types/base'
import { type RequestedTaskLight } from '@/types/requestedTasks'
import httpRequest from '@/utils/httpRequest'
import { defineStore } from 'pinia'
import { inject, ref } from 'vue'
import type { VueCookies } from 'vue-cookies'

export const useRequestedTasksStore = defineStore('requestedTasks', () => {
  const requestedTasks = ref<RequestedTaskLight[]>([])
  const paginator = ref<Paginator>({
    page: 1,
    page_size: 100,
    skip: 0,
    limit: 100,
    count: 0,
  })

  const error = ref<Error | null>(null)
  const loadingStore = useLoadingStore()

  const config = inject<Config>(constants.config)

  if (!config) {
    throw new Error('Config is not defined')
  }

  const $cookies = inject<VueCookies>('$cookies')

  const token = $cookies?.get(constants.TOKEN_COOKIE_NAME)

  let headers: Record<string, string> = {}
  if (token) {
    headers = {
      'Authorization': `Bearer ${token}`,
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
      error.value = _error as Error
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
      error.value = _error as Error
      return false
    } finally {
      loadingStore.stopLoading()
    }
  }

  return {
    requestedTasks,
    error,
    fetchRequestedTasks,
    removeRequestedTask,
    paginator,
  }
})
