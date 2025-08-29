import constants from '@/constants'
import { useAuthStore } from '@/stores/auth'
import type { ListResponse, Paginator } from '@/types/base'
import type { ErrorResponse } from '@/types/errors'
import type {
  NewRequestedTaskSchemaResponse,
  RequestedTaskFullSchema,
  RequestedTaskLight,
} from '@/types/requestedTasks'
import { translateErrors } from '@/utils/errors'
import { defineStore } from 'pinia'
import { inject, ref } from 'vue'
import type { VueCookies } from 'vue-cookies'

export const useRequestedTasksStore = defineStore('requestedTasks', () => {
  const $cookies = inject<VueCookies>('$cookies')
  const limit = Number($cookies?.get('requested-tasks-table-limit') || 20)
  const requestedTasks = ref<RequestedTaskLight[]>([])
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
    $cookies?.set('requested-tasks-table-limit', limit, constants.COOKIE_LIFETIME_EXPIRY)
  }

  const fetchRequestedTasks = async (
    params: {
      limit?: number
      skip?: number
      scheduleName?: string[] | null
    } = {},
  ) => {
    const { limit = 100, skip = 0, scheduleName = null } = params
    const service = await authStore.getApiService('requested-tasks')
    const cleanedParams = Object.fromEntries(
      Object.entries({
        limit,
        skip,
        schedule_name: scheduleName,
      }).filter(([, value]) => !!value),
    )

    try {
      const response = await service.get<null, ListResponse<RequestedTaskLight>>('', {
        params: cleanedParams,
      })

      requestedTasks.value = response.items
      paginator.value = response.meta
      errors.value = []
      return requestedTasks.value
    } catch (_error) {
      errors.value = translateErrors(_error as ErrorResponse)
      return null
    }
  }

  const removeRequestedTask = async (id: string) => {
    try {
      const service = await authStore.getApiService('requested-tasks')
      await service.delete(`/${id}`)

      // Remove the task from the local state
      const index = requestedTasks.value.findIndex((task) => task.id === id)
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

  const requestTasks = async (body: {
    scheduleNames: string[]
    worker?: string | null
    priority?: number | null
  }) => {
    const cleanedBody = Object.fromEntries(
      Object.entries({
        schedule_names: body.scheduleNames,
        worker: body.worker,
        priority: body.priority,
      }).filter(([, value]) => value !== null),
    )
    try {
      const service = await authStore.getApiService('requested-tasks')
      const response = await service.post<
        Record<string, string[] | string | number>,
        NewRequestedTaskSchemaResponse
      >('', cleanedBody)
      return response
    } catch (_error) {
      errors.value = translateErrors(_error as ErrorResponse)
      return null
    }
  }

  const updateRequestedTask = async (id: string, body: { priority: number }) => {
    try {
      const service = await authStore.getApiService('requested-tasks')
      const response = await service.patch<{ priority: number }, RequestedTaskFullSchema>(
        `/${id}`,
        body,
      )
      return response
    } catch (_error) {
      errors.value = translateErrors(_error as ErrorResponse)
      return null
    }
  }

  const deleteRequestedTask = async (id: string) => {
    try {
      const service = await authStore.getApiService('requested-tasks')
      await service.delete(`/${id}`)
      return true
    } catch (_error) {
      errors.value = translateErrors(_error as ErrorResponse)
      return false
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
    updateRequestedTask,
    deleteRequestedTask,
    savePaginatorLimit,
  }
})
