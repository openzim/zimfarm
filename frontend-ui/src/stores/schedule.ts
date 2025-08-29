import constants from '@/constants'
import { useAuthStore } from '@/stores/auth'
import type { ListResponse, Paginator } from '@/types/base'
import type { ErrorResponse } from '@/types/errors'
import type { Schedule, ScheduleLight, ScheduleUpdateSchema } from '@/types/schedule'
import { translateErrors } from '@/utils/errors'
import { defineStore } from 'pinia'
import { inject, ref } from 'vue'
import type { VueCookies } from 'vue-cookies'

export const useScheduleStore = defineStore('schedule', () => {
  const $cookies = inject<VueCookies>('$cookies')
  const schedule = ref<Schedule | null>(null)
  const errors = ref<string[]>([])
  const schedules = ref<ScheduleLight[]>([])
  const limit = Number($cookies?.get('schedules-table-limit') || 20)
  const paginator = ref<Paginator>({
    page: 1,
    page_size: limit,
    skip: 0,
    limit: limit,
    count: 0,
  })
  const authStore = useAuthStore()

  const fetchSchedule = async (
    scheduleName: string,
    forceReload: boolean = false,
    hideSecrets: boolean = false
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

      const response = await service.get<null, Schedule>(`/${scheduleName}`, { params: { hide_secrets: hideSecrets } })
      schedule.value = response
      // generate artifacts_globs_str
      schedule.value.config.artifacts_globs_str = schedule.value.config.artifacts_globs?.join('\n')
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
      const response = await service.get<null, ListResponse<ScheduleLight>>("", { params: cleanedParams  })
      schedules.value = response.items
      paginator.value = response.meta
      errors.value = []
      return schedules.value
    } catch (_error) {
      console.error('Failed to fetch schedules', _error)
      errors.value = translateErrors(_error as ErrorResponse)
      return null
    }
  }

  const clearSchedule = () => {
    schedule.value = null
    errors.value = []
  }

  const cloneSchedule = async (scheduleName: string, newScheduleName: string) => {
    const service = await authStore.getApiService('schedules')
    try {
      const response = await service.post<{name: string}, {id: string}>(`/${scheduleName}/clone`, { name: newScheduleName })
      return response
    } catch (_error) {
      console.error('Failed to clone schedule', _error)
      errors.value = translateErrors(_error as ErrorResponse)
      return null
    }
  }

  const fetchScheduleImageTags = async (scheduleName: string, params: { hubName: string}) => {
    const service = await authStore.getApiService('schedules')
    try {
      const response = await service.get<null, ListResponse<string>>(`/${scheduleName}/image-names`, { params: { hub_name: params.hubName } })
      return response.items
    } catch (_error) {
      console.error('Failed to fetch image tags', _error)
      errors.value = translateErrors(_error as ErrorResponse)
      return null
    }
  }

  const updateSchedule = async (scheduleName: string, schedule: ScheduleUpdateSchema) => {
    const service = await authStore.getApiService('schedules')
    try {
      const response = await service.patch<ScheduleUpdateSchema, Schedule>(`/${scheduleName}`, schedule)
      return response
    } catch (_error) {
      console.error('Failed to update schedule', _error)
      errors.value = translateErrors(_error as ErrorResponse)
      return null
    }
  }

  const deleteSchedule = async (scheduleName: string) => {
    const service = await authStore.getApiService('schedules')
    try {
      await service.delete<null, null>(`/${scheduleName}`)
      return true
    } catch (_error) {
      console.error('Failed to delete schedule', _error)
      errors.value = translateErrors(_error as ErrorResponse)
      return false
    }
  }

  const validateSchedule = async (scheduleName: string) => {
    const service = await authStore.getApiService('schedules')
    errors.value = []
    try {
      await service.get<null, null>(`/${scheduleName}/validate`)
      return true
    }
    catch (_error) {
      console.error('Failed to validate schedule', _error)
      errors.value = translateErrors(_error as ErrorResponse)
      return false
    }
  }

  const savePaginatorLimit = (limit: number) => {
    $cookies?.set('schedules-table-limit', limit, constants.COOKIE_LIFETIME_EXPIRY)
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
    cloneSchedule,
    fetchScheduleImageTags,
    updateSchedule,
    deleteSchedule,
    validateSchedule,
    savePaginatorLimit,
  }
})
