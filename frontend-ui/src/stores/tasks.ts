import type { Config } from '@/config'
import constants from '@/constants'
import { useLoadingStore } from '@/stores/loading'
import type { ListResponse, Paginator } from '@/types/base'
import { type TaskLight } from '@/types/tasks'
import httpRequest from '@/utils/httpRequest'
import { defineStore } from 'pinia'
import { inject, ref } from 'vue'
import type { VueCookies } from 'vue-cookies'


export const useTasksStore = defineStore('tasks', () => {
  const tasks = ref<TaskLight[]>([])
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
    baseURL: `${config.ZIMFARM_WEBAPI}/tasks`,
    headers,
  })

  const fetchTasks = async (limit: number = 100, skip: number = 0, status: string[]) => {
    try {
      loadingStore.startLoading('Fetching tasks...')
      const response = await service.get<null, ListResponse<TaskLight>>('', { params: { limit, skip, status } })

      tasks.value = response.items
      paginator.value = response.meta

    } catch (_error) {
      console.error('Failed to fetch tasks', _error)
      error.value = _error as Error
    } finally {
      loadingStore.stopLoading()
    }
  }

  return {
    tasks,
    paginator,
    error,
    fetchTasks,
  }
})
