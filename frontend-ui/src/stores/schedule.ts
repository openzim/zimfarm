import { useAuthStore } from '@/stores/auth'
import type { ListResponse, Paginator } from '@/types/base'
import type { ErrorResponse } from '@/types/errors'
import type { Schedule, ScheduleLight } from '@/types/schedule'
import { translateErrors } from '@/utils/errors'
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useLoadingStore } from './loading'

export const useScheduleStore = defineStore('schedule', () => {
  const schedule = ref<Schedule | null>(null)
  const errors = ref<string[]>([])
  const schedules = ref<ScheduleLight[]>([])
  const paginator = ref<Paginator>({
    page: 1,
    page_size: 100,
    skip: 0,
    limit: 100,
    count: 0,
  })
  const authStore = useAuthStore()
  const loadingStore = useLoadingStore()

  const fetchSchedule = async (
    scheduleName: string,
    forceReload: boolean = false,
  ) => {
    const service = await authStore.getApiService('schedules')
    // Check if we already have the schedule and don't need to force reload
    if (!forceReload && schedule.value && schedule.value.name === scheduleName) {
      return schedule.value
    }

    try {
      errors.value = []
      // Clear current schedule until we receive the right one
      schedule.value = null

      const response = await service.get<null, Schedule>(`/${scheduleName}`)
      schedule.value = response
    } catch (_error) {
      console.error('Failed to load schedule', _error)
      errors.value = translateErrors(_error as ErrorResponse)
    }
    return schedule.value
  }

  const fetchSchedules = async (
    limit: number,
    skip: number,
    category: string[] | undefined,
    lang: string[] | undefined,
    tag: string[] | undefined,
    name: string | undefined
  ) => {
    const service = await authStore.getApiService('schedules')
    // filter out undefined values from params
    const cleanedParams = Object.fromEntries(
      Object.entries(
        {
          limit,
          skip,
          category,
          lang,
          tag,
          name,
        }
      )
      .filter(([, value]) => !!value)
    )
    try {
      loadingStore.startLoading('Fetching schedules...')
      const response = await service.get<null, ListResponse<ScheduleLight>>("", { params: cleanedParams  })
      schedules.value = response.items
      paginator.value = response.meta
      errors.value = []
      return schedules.value
    } catch (_error) {
      console.error('Failed to fetch schedules', _error)
      errors.value = translateErrors(_error as ErrorResponse)
      return null
    } finally {
      loadingStore.stopLoading()
    }
  }

  const clearSchedule = () => {
    schedule.value = null
    errors.value = []
  }

  return {
    // State
    schedule,
    schedules,
    paginator,
    errors,
    // Actions
    fetchSchedule,
    fetchSchedules,
    clearSchedule,
  }
})
