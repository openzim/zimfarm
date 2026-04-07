import { useAuthStore } from '@/stores/auth'
import type { ListResponse, Paginator } from '@/types/base'
import type { ErrorResponse } from '@/types/errors'
import type { User } from '@/types/user'
import { translateErrors } from '@/utils/errors'
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore('user', () => {
  const defaultLimit = ref<number>(Number(localStorage.getItem('users-table-limit') || 20))
  const errors = ref<string[]>([])
  const users = ref<User[]>([])
  const paginator = ref<Paginator>({
    page: 1,
    page_size: defaultLimit.value,
    skip: 0,
    limit: defaultLimit.value,
    count: 0,
  })

  const authStore = useAuthStore()

  const savePaginatorLimit = (limit: number) => {
    localStorage.setItem('users-table-limit', limit.toString())
  }

  const createUser = async (username: string, role: string, password: string) => {
    const service = await authStore.getApiService('accounts')
    try {
      const response = await service.post<
        { username: string; role: string; password: string },
        User
      >('', {
        username,
        role,
        password,
      })
      errors.value = []
      return response
    } catch (error) {
      console.error('Failed to create user', error)
      errors.value = translateErrors(error as ErrorResponse)
      return null
    }
  }

  const fetchUsers = async (skip: number = 0, limit: number = 20, username?: string) => {
    const service = await authStore.getApiService('accounts')
    // filter out undefined values from params
    const cleanedParams = Object.fromEntries(
      Object.entries({
        limit,
        skip,
        username,
      }).filter(([, value]) => !!value),
    )
    try {
      const response = await service.get<null, ListResponse<User>>('', {
        params: cleanedParams,
      })
      errors.value = []
      users.value = response.items
      paginator.value = response.meta
      return users.value
    } catch (error) {
      errors.value = translateErrors(error as ErrorResponse)
      users.value = []
      paginator.value = {
        page: 1,
        page_size: 100,
        skip: 0,
        limit: 100,
        count: 0,
      }
      return null
    }
  }

  const fetchUser = async (userId: string) => {
    const service = await authStore.getApiService('accounts')
    try {
      const response = await service.get<null, User>(`/${userId}`)
      errors.value = []
      return response
    } catch (error) {
      console.error('Failed to fetch user', error)
      errors.value = translateErrors(error as ErrorResponse)
      return null
    }
  }

  const changePassword = async (userId: string, body: { current?: string; new: string | null }) => {
    const service = await authStore.getApiService('accounts')
    try {
      await service.patch<{ current?: string; new: string | null }, null>(
        `/${userId}/password`,
        body,
      )
      errors.value = []
      return true
    } catch (error) {
      console.error('Failed to change password', error)
      errors.value = translateErrors(error as ErrorResponse)
      return false
    }
  }

  const updateUser = async (
    userId: string,
    payload: {
      username?: string | null
      display_name?: string
      role?: string
      scope?: Record<string, Record<string, boolean>>
      idp_sub?: string | null
    },
  ) => {
    const service = await authStore.getApiService('accounts')
    const cleanedPayload = Object.fromEntries(
      Object.entries(payload).filter(([, value]) => value !== undefined),
    )
    try {
      await service.patch<
        {
          username?: string | null
          display_name?: string
          role?: string
          scope?: Record<string, Record<string, boolean>>
          idp_sub?: string | null
        },
        null
      >(`/${userId}`, cleanedPayload)
      errors.value = []
      return true
    } catch (error) {
      console.error('Failed to update user', error)
      errors.value = translateErrors(error as ErrorResponse)
      return false
    }
  }

  const deleteUser = async (userId: string) => {
    const service = await authStore.getApiService('accounts')
    try {
      await service.delete(`/${userId}`)
      errors.value = []
      return true
    } catch (error) {
      console.error('Failed to delete user', error)
      errors.value = translateErrors(error as ErrorResponse)
      return false
    }
  }

  return {
    // State
    errors,
    users,
    defaultLimit,
    paginator,

    // Actions
    createUser,
    fetchUsers,
    fetchUser,
    changePassword,
    updateUser,
    deleteUser,
    savePaginatorLimit,
  }
})
