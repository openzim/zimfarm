import { useAuthStore } from '@/stores/auth'
import type { ListResponse, Paginator } from '@/types/base'
import type { ErrorResponse } from '@/types/errors'
import type { SshKeyRead, User, UserWithSshKeys } from '@/types/user'
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

  const fetchUser = async (username: string) => {
    const service = await authStore.getApiService('users')
    try {
      const response = await service.get<null, UserWithSshKeys>(`/${username}`)
      errors.value = []
      return response
    } catch (error) {
      console.error('Failed to fetch user', error)
      errors.value = translateErrors(error as ErrorResponse)
      return null
    }
  }

  const deleteSshKey = async (username: string, fingerprint: string) => {
    const service = await authStore.getApiService('users')
    try {
      await service.delete(`/${username}/keys/${fingerprint}`)
      errors.value = []
      return true
    } catch (error) {
      console.error('Failed to delete SSH key', error)
      errors.value = translateErrors(error as ErrorResponse)
      return false
    }
  }

  const changePassword = async (username: string, body: { current?: string, new: string }) => {
    const service = await authStore.getApiService('users')
    try {
      await service.patch<{ current?: string, new: string }, null>(`/${username}/password`, body)
      errors.value = []
      return true
    } catch (error) {
      console.error('Failed to change password', error)
      errors.value = translateErrors(error as ErrorResponse)
      return false
    }
  }

  const updateUser = async (username: string, payload: { role?: string; email?: string }) => {
    const service = await authStore.getApiService('users')
    try {
      await service.patch<{ role?: string; email?: string }, null>(`/${username}`, payload)
      errors.value = []
      return true
    } catch (error) {
      console.error('Failed to update user', error)
      errors.value = translateErrors(error as ErrorResponse)
      return false
    }
  }

  const addSshKey = async (username: string, payload: { name: string; key: string }) => {
    const service = await authStore.getApiService('users')
    try {
      await service.post<{ name: string; key: string }, SshKeyRead>(`/${username}/keys`, payload)
      errors.value = []
      return true
    } catch (error) {
      console.error('Failed to add SSH key', error)
      errors.value = translateErrors(error as ErrorResponse)
      return false
    }
  }

  const deleteUser = async (username: string) => {
    const service = await authStore.getApiService('users')
    try {
      await service.delete(`/${username}`)
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
    paginator,

    // Actions
    createUser,
    fetchUsers,
    fetchUser,
    deleteSshKey,
    changePassword,
    updateUser,
    addSshKey,
    deleteUser,
  }
})
