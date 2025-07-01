import type { Config } from '@/config'
import constants from '@/constants'
import type { JWTPayload, Token, User } from '@/types/user'
import httpRequest from '@/utils/httpRequest'
import { jwtDecode } from 'jwt-decode'
import { defineStore } from 'pinia'
import { computed, inject, ref } from 'vue'
import type { VueCookies } from 'vue-cookies'

export const useAuthStore = defineStore('auth', () => {
  // TODO: Store is not really working now as we need to include the user
  // in the jwt payload. This is just a rough implementation.
  const token = ref<Token | null>(null)
  const user = ref<User | null>(null)
  const error = ref<Error | null>(null)

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
    const now = Math.floor(Date.now() / 1000)
    return token.value.expires_in > now
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
      error.value = null
      saveTokenToCookie(token.value)
      return true
    } catch (_error) {
      error.value = _error as Error
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
      tokenData = JSON.parse(cookieValue)
      jwtPayload = jwtDecode<JWTPayload>(tokenData.access_token)
    } catch {
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
    $cookies.set(
      constants.TOKEN_COOKIE_NAME,
      JSON.stringify(tokenData),
      tokenData.expires_in,
      undefined,
      undefined,
      config.ZIMFARM_WEBAPI.startsWith('https://'),
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

  return {
    // State
    token,
    user,

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
  }
})
