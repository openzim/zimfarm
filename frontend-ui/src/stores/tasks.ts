import constants from '@/constants'
import { useAuthStore } from '@/stores/auth'
import type { ListResponse, Paginator } from '@/types/base'
import type { ErrorResponse } from '@/types/errors'
import { type Task, type TaskLight } from '@/types/tasks'
import { translateErrors } from '@/utils/errors'
import { defineStore } from 'pinia'
import { inject, ref } from 'vue'
import type { VueCookies } from 'vue-cookies'

export const useTasksStore = defineStore('tasks', () => {
  const $cookies = inject<VueCookies>('$cookies')
  const task = ref<Task | null>(null)
  const tasks = ref<TaskLight[]>([])
  const limit = Number($cookies?.get('tasks-table-limit') || 20)
  const paginator = ref<Paginator>({
    page: 1,
    page_size: limit,
    skip: 0,
    limit: limit,
    count: 0,
  })
  const errors = ref<string[]>([])

  const authStore = useAuthStore()

  const savePaginatorLimit = (limit: number) => {
    $cookies?.set('tasks-table-limit', limit, constants.COOKIE_LIFETIME_EXPIRY)
  }

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

  const fetchTask = async (id: string, hideSecrets: boolean = false) => {
    const service = await authStore.getApiService('tasks')
    try {
      const response = await service.get<null, Task>(`/${id}`, { params: { hide_secrets: hideSecrets } })
      task.value = response
      return task.value
    } catch (_error) {
      console.error('Failed to get task', _error)
      errors.value = translateErrors(_error as ErrorResponse)
      return null
    }
  }

  return {
    // State
    task,
    tasks,
    paginator,
    errors,

    // Actions
    fetchTasks,
    cancelTask,
    fetchTask,
    savePaginatorLimit,
  }
})
