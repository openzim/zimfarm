import { useAuthStore } from '@/stores/auth'
import type { ListResponse } from '@/types/base'
import type { ErrorResponse } from '@/types/errors'
import type { TaskLight } from '@/types/tasks'
import type { Worker } from '@/types/workers'
import { translateErrors } from '@/utils/errors'
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useWorkersStore = defineStore('workers', () => {
  const workers = ref<Worker[]>([])
  const errors = ref<string[]>([])

  const authStore = useAuthStore()

  const fetchWorkers = async (limit: number = 100) => {
    try {
      const service = await authStore.getApiService('workers')
      const response = await service.get<null, ListResponse<Worker>>('', { params: { limit } })

      // Initialize tasks array for each worker
      workers.value = response.items.map(worker => ({
        ...worker,
        tasks: []
      }))

      errors.value = []
    } catch (_error) {
      console.error('Failed to fetch workers', _error)
      errors.value = translateErrors(_error as ErrorResponse)
    }
  }

  const addTaskToWorker = (task: TaskLight) => {
    const worker = workers.value.find(w => w.name === task.worker_name)
    if (worker) {
      worker.tasks.push(task)
    }
  }

  const clearWorkerTasks = () => {
    workers.value.forEach(worker => {
      worker.tasks = []
    })
  }

  return {
    // State
    workers,
    errors,

    // Actions
    fetchWorkers,
    addTaskToWorker,
    clearWorkerTasks,
  }
})
