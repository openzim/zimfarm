import { useAuthStore } from '@/stores/auth'
import type { ListResponse, Paginator } from '@/types/base'
import type { ErrorResponse } from '@/types/errors'
import type { Team, TeamCreateSchema, TeamLight, TeamUpdateSchema } from '@/types/team'
import { translateErrors } from '@/utils/errors'
import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface FetchTeamsParams {
  skip?: number
  limit?: number
  name?: string
  is_private?: boolean
}

export const useTeamStore = defineStore('team', () => {
  const defaultLimit = ref<number>(Number(localStorage.getItem('teams-table-limit') || 20))
  const errors = ref<string[]>([])
  const teams = ref<TeamLight[]>([])
  const paginator = ref<Paginator>({
    page: 1,
    page_size: defaultLimit.value,
    skip: 0,
    limit: defaultLimit.value,
    count: 0,
  })

  const authStore = useAuthStore()

  const savePaginatorLimit = (limit: number) => {
    localStorage.setItem('teams-table-limit', limit.toString())
  }

  const fetchTeams = async (params: FetchTeamsParams = {}) => {
    const { skip = 0, limit = defaultLimit.value, name, is_private } = params
    const service = await authStore.getApiService('teams')
    const cleanedParams = Object.fromEntries(
      Object.entries({ skip, limit, name, is_private }).filter(([, value]) => value !== undefined),
    )
    try {
      const response = await service.get<null, ListResponse<TeamLight>>('', {
        params: cleanedParams,
      })
      errors.value = []
      teams.value = response.items
      paginator.value = response.meta
      return teams.value
    } catch (error) {
      console.error('Failed to fetch teams', error)
      errors.value = translateErrors(error as ErrorResponse)
      teams.value = []
      paginator.value = {
        page: 1,
        page_size: defaultLimit.value,
        skip: 0,
        limit: defaultLimit.value,
        count: 0,
      }
      return null
    }
  }

  const fetchTeam = async (teamName: string) => {
    const service = await authStore.getApiService('teams')
    try {
      const response = await service.get<null, Team>(`/${teamName}`)
      errors.value = []
      return response
    } catch (error) {
      console.error('Failed to fetch team', error)
      errors.value = translateErrors(error as ErrorResponse)
      return null
    }
  }

  const createTeam = async (payload: TeamCreateSchema) => {
    const service = await authStore.getApiService('teams')
    try {
      const response = await service.post<TeamCreateSchema, Team>('', payload)
      errors.value = []
      return response
    } catch (error) {
      console.error('Failed to create team', error)
      errors.value = translateErrors(error as ErrorResponse)
      return null
    }
  }

  const updateTeam = async (teamName: string, payload: TeamUpdateSchema) => {
    const service = await authStore.getApiService('teams')
    const cleanedPayload = Object.fromEntries(
      Object.entries(payload).filter(([, value]) => value !== undefined),
    )
    try {
      await service.patch<TeamUpdateSchema, null>(`/${teamName}`, cleanedPayload)
      errors.value = []
      return true
    } catch (error) {
      console.error('Failed to update team', error)
      errors.value = translateErrors(error as ErrorResponse)
      return false
    }
  }

  return {
    // State
    errors,
    teams,
    defaultLimit,
    paginator,

    // Actions
    fetchTeams,
    fetchTeam,
    createTeam,
    updateTeam,
    savePaginatorLimit,
  }
})
