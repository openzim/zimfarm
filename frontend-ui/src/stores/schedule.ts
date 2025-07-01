import type { Config } from '@/config'
import constants from '@/constants'
import type { Schedule } from '@/types/schedule'
import httpRequest from '@/utils/httpRequest'
import { defineStore } from 'pinia'
import { inject, ref } from 'vue'

export const useScheduleStore = defineStore('schedule', () => {
  const schedule = ref<Schedule | null>(null)
  const error = ref<Error | null>(null)

  const config = inject<Config>(constants.config)

  if (!config) {
    throw new Error('Config is not defined')
  }

  const service = httpRequest({
    baseURL: `${config.ZIMFARM_WEBAPI}/schedules`,
  })

  const fetchSchedule = async (
    scheduleName: string,
    forceReload: boolean = false,
    onSuccess?: () => void,
    onError?: (error: string) => void,
  ) => {
    // Check if we already have the schedule and don't need to force reload
    if (!forceReload && schedule.value && schedule.value.name === scheduleName) {
      if (onSuccess) {
        onSuccess()
      }
      return
    }

    try {
      error.value = null
      // Clear current schedule until we receive the right one
      schedule.value = null

      const response = await service.get<Schedule, Schedule>(`/${scheduleName}`)
      schedule.value = response

      if (onSuccess) {
        onSuccess()
      }
    } catch (_error) {
      const errorMessage = _error instanceof Error ? _error.message : 'Unknown error occurred'
      console.error('Failed to load schedule', _error)
      error.value = _error as Error

      if (onError) {
        onError(errorMessage)
      }
    }
  }

  const clearSchedule = () => {
    schedule.value = null
    error.value = null
  }

  return {
    schedule,
    error,
    fetchSchedule,
    clearSchedule,
  }
})
