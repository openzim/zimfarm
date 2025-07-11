import { useAuthStore } from '@/stores/auth'
import type { ListResponse, Paginator } from '@/types/base'
import type { ErrorResponse } from '@/types/errors'
import type { User, UserWithSshKeys } from '@/types/user'
import { translateErrors } from '@/utils/errors'
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore('user', () => {
  const errors = ref<string[]>([])
  const users = ref<User[]>([])
  const paginator = ref<Paginator>({
    page: 1,
    page_size: 100,
    skip: 0,
    limit: 100,
    count: 0,
  })

  const authStore = useAuthStore()

  const createUser = async (username: string, email: string, role: string, password: string) => {
    const service = await authStore.getApiService('users')
    try {
      const response = await service.post<{ username: string; email: string; role: string; password: string }, UserWithSshKeys>('', {
        username,
        email,
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

  const fetchUsers = async (skip: number = 0, limit: number = 20) => {
    const service = await authStore.getApiService('users')
    try {
      const response = await service.get<null, ListResponse<User>>('', {
        params: {
          skip,
          limit,
        },
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

  return {
    // State
    errors,
    users,
    paginator,

    // Actions
    createUser,
    fetchUsers,
  }
})
