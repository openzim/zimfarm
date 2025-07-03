import { useAuthStore } from '@/stores/auth'
import type { ErrorResponse } from '@/types/errors'
import type { Schedule } from '@/types/schedule'
import { translateErrors } from '@/utils/errors'
import { defineStore } from 'pinia'
import { ref } from 'vue'
export const useScheduleStore = defineStore('schedule', () => {
  const schedule = ref<Schedule | null>(null)
  const error = ref<string[]>([])
  const authStore = useAuthStore()

  const fetchSchedule = async (
    scheduleName: string,
    forceReload: boolean = false,
  ) => {
    const service = await authStore.getApiService('schedules')
    // Check if we already have the schedule and don't need to force reload
    if (!forceReload && schedule.value && schedule.value.name === scheduleName) {
      return
    }

    try {
      error.value = []
      // Clear current schedule until we receive the right one
      schedule.value = null

      const response = await service.get<Schedule, Schedule>(`/${scheduleName}`)
      schedule.value = response
    } catch (_error) {
      console.error('Failed to load schedule', _error)
      error.value = translateErrors(_error as ErrorResponse)
    }
  }

  const clearSchedule = () => {
    schedule.value = null
    error.value = []
  }

  return {
    schedule,
    error,
    fetchSchedule,
    clearSchedule,
  }
})
