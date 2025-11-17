import { useAuthStore } from '@/stores/auth'
import type { ListResponse, Paginator } from '@/types/base'
import type { ErrorResponse } from '@/types/errors'
import type { TaskLight } from '@/types/tasks'
import type { Worker, WorkerMetrics, WorkerUpdateSchema } from '@/types/workers'
import { translateErrors } from '@/utils/errors'
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useWorkersStore = defineStore('workers', () => {
  const workers = ref<Worker[]>([])
  const errors = ref<string[]>([])
  const defaultLimit = ref<number>(Number(localStorage.getItem('workers-table-limit') || 20))
  const paginator = ref<Paginator>({
    page: 1,
    page_size: defaultLimit.value,
    skip: 0,
    limit: defaultLimit.value,
    count: 0,
  })

  const authStore = useAuthStore()

  const savePaginatorLimit = (limit: number) => {
    localStorage.setItem('workers-table-limit', limit.toString())
  }

  const fetchWorkers = async (
    params: { limit?: number; skip?: number; hide_offlines?: boolean } = {},
  ) => {
    const { limit = 20, skip = 0, hide_offlines = true } = params
    try {
      const service = await authStore.getApiService('workers')
      const response = await service.get<null, ListResponse<Worker>>('', {
        params: { limit, skip, hide_offlines },
      })

      // Preserve existing tasks when fetching workers
      const existingTasks = new Map(workers.value.map((w) => [w.name, w.tasks || []]))
      workers.value = response.items.map((worker) => ({
        ...worker,
        tasks: existingTasks.get(worker.name) || [],
      }))
      paginator.value = response.meta

      errors.value = []
      return response.items
    } catch (_error) {
      console.error('Failed to fetch workers', _error)
      errors.value = translateErrors(_error as ErrorResponse)
      return null
    }
  }

  const updateWorkerTasks = (tasks: TaskLight[]) => {
    workers.value = workers.value.map((worker) => ({
      ...worker,
      tasks: tasks.filter((task) => task.worker_name === worker.name),
    }))
  }

  const fetchWorkerMetrics = async (name: string) => {
    try {
      const service = await authStore.getApiService('workers')
      const response = await service.get<null, WorkerMetrics>(`/${name}`)
      errors.value = []
      return response
    } catch (_error) {
      console.error('Failed to fetch worker metrics', _error)
      errors.value = translateErrors(_error as ErrorResponse)
      return null
    }
  }

  const updateWorker = async (name: string, payload: WorkerUpdateSchema) => {
    // Remove null values from the payload
    const cleanedPayload = Object.fromEntries(
      Object.entries(payload).filter(([, value]) => value !== null),
    )
    try {
      const service = await authStore.getApiService('workers')
      await service.put(`/${name}`, cleanedPayload)
      errors.value = []
      return true
    } catch (_error) {
      console.error('Failed to update worker', _error)
      errors.value = translateErrors(_error as ErrorResponse)
      return false
    }
  }

  return {
    // State
    workers,
    errors,
    defaultLimit,
    paginator,

    // Actions
    fetchWorkers,
    updateWorkerTasks,
    savePaginatorLimit,
    fetchWorkerMetrics,
    updateWorker,
  }
})
