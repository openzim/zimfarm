import type { Config } from '@/config'
import constants from '@/constants'
import type { ErrorResponse } from '@/types/errors'
import type { Schedule } from '@/types/schedule'
import { translateErrors } from '@/utils/errors'
import httpRequest from '@/utils/httpRequest'
import { defineStore } from 'pinia'
import { inject, ref } from 'vue'

export const useScheduleStore = defineStore('schedule', () => {
  const schedule = ref<Schedule | null>(null)
  const error = ref<string[]>([])

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
  ) => {
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
