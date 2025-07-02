import type { Config } from '@/config'
import constants from '@/constants'
import type { ErrorResponse } from '@/types/errors'
import type { JWTPayload, Token, User } from '@/types/user'
import { translateErrors } from '@/utils/errors'
import httpRequest from '@/utils/httpRequest'
import { jwtDecode } from 'jwt-decode'
import { defineStore } from 'pinia'
import { computed, inject, ref } from 'vue'
import type { VueCookies } from 'vue-cookies'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<Token | null>(null)
  const user = ref<User | null>(null)
  const errors = ref<string[]>([])

  const $cookies = inject<VueCookies>('$cookies')
  if (!$cookies) {
    throw new Error('VueCookies is not defined')
  }
  const config = inject<Config>(constants.config)

  if (!config) {
    throw new Error('Config is not defined')
  }

  const service = httpRequest({
    baseURL: `${config.ZIMFARM_WEBAPI}/auth`,
  })

  // Computed properties
  const isLoggedIn = computed(() => {
    if (!token.value) return false
    const jwtPayload = jwtDecode<JWTPayload>(token.value.access_token)
    const now = Math.floor(Date.now() / 1000)
    return jwtPayload.exp > now
  })

  const username = computed(() => {
    return user.value?.username || null
  })

  const accessToken = computed(() => {
    return token.value?.access_token || null
  })

  const refreshToken = computed(() => {
    return token.value?.refresh_token || null
  })

  const permissions = computed(() => {
    return user.value?.scope || {}
  })

  const renewTokenFromRefresh = async (refreshToken: string) => {
    try {
      const response = await service.post<{ refreshToken: string }, Token>('/refresh', {
        refreshToken: refreshToken,
      })
      token.value = response
      user.value = jwtDecode<JWTPayload>(token.value.access_token).user
      errors.value = []
      saveTokenToCookie(token.value)
      return true
    } catch (_error) {
      token.value = null
      user.value = null
      errors.value = translateErrors(_error as ErrorResponse)
      return false
    }
  }

  const loadTokenFromCookie = async (forceRefresh: boolean = false) => {
    // already authenticated
    if (isLoggedIn.value && !forceRefresh) return true

    const cookieValue = $cookies.get(constants.TOKEN_COOKIE_NAME)
    if (!cookieValue) return false

    let jwtPayload: JWTPayload
    let tokenData: Token
    try {
      jwtPayload = jwtDecode<JWTPayload>(cookieValue.access_token)
      tokenData = cookieValue
    } catch (error) {
      console.error('Error parsing cookie value', error)
      // incorrect cookie payload
      $cookies.remove(constants.TOKEN_COOKIE_NAME)
      return false
    }

    const expiry = new Date(jwtPayload.exp * 1000)
    const now = new Date()
    if (now > expiry || forceRefresh) {
      return await renewTokenFromRefresh(tokenData.refresh_token)
    }

    token.value = tokenData
    user.value = jwtPayload.user
    return true
  }

  const saveTokenToCookie = (tokenData: Token) => {
    // Decode JWT to get actual expiry time
    const jwtPayload = jwtDecode<JWTPayload>(tokenData.access_token)
    const expiryDate = new Date(jwtPayload.exp * 1000)

    // Set cookie with proper configuration for persistence
    $cookies.set(
      constants.TOKEN_COOKIE_NAME,
      JSON.stringify(tokenData),
      expiryDate, // Use actual JWT expiry
      '/', // path
      undefined, // domain
      config.ZIMFARM_WEBAPI.startsWith('https://'), // secure flag
    )
  }

  const removeTokenFromCookie = () => {
    token.value = null
    user.value = null
    $cookies.remove(constants.TOKEN_COOKIE_NAME)
  }

  const hasPermission = (resource: string, action: string) => {
    if (!token.value) return false
    return user.value?.scope[resource]?.[action] || false
  }

  const authenticate = async (username: string, password: string) => {
    try {
      const response = await service.post<{ username: string; password: string }, Token>(
        '/authorize',
        {
          username,
          password,
        },
      )
      token.value = response
      user.value = jwtDecode<JWTPayload>(token.value.access_token).user
      errors.value = []
      saveTokenToCookie(token.value)
      return true
    } catch (err: unknown) {
      token.value = null
      user.value = null
      errors.value = translateErrors(err as ErrorResponse)
      return false
    }
  }

  return {
    // State
    token,
    user,
    errors,

    // Computed
    isLoggedIn,
    username,
    accessToken,
    refreshToken,
    permissions,

    // Methods
    saveTokenToCookie,
    removeTokenFromCookie,
    hasPermission,
    loadTokenFromCookie,
    renewTokenFromRefresh,
    authenticate,
  }
})
