import type { Config } from '@/config'
import constants from '@/constants'
import type { ErrorResponse } from '@/types/errors'
import type { ExtendedToken, JWTPayload, JWTUser, KiwixUserInfo, Token } from '@/types/user'
import { translateErrors } from '@/utils/errors'
import {
  exchangeCodeForToken,
  fetchKiwixUserInfo,
  getKiwixAuthConfig,
  logoutFromKiwixAuth,
  refreshKiwixToken,
} from '@/services/auth/kiwix'
import httpRequest from '@/utils/httpRequest'
import { jwtDecode } from 'jwt-decode'
import { defineStore } from 'pinia'
import { computed, inject, ref } from 'vue'
import type { VueCookies } from 'vue-cookies'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<ExtendedToken | null>(null)
  const user = ref<JWTUser | null>(null)
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
    return true
  })

  const tokenExpiryDate = computed(() => {
    if (!token.value) return null

    // For Kiwix tokens, parse expires_time
    if (token.value.token_type === 'kiwix') {
      if (token.value.expires_time) {
        return new Date(token.value.expires_time)
      }
      return null
    }

    // For legacy tokens, decode JWT
    try {
      const jwtPayload = jwtDecode<JWTPayload>(token.value.access_token)
      return new Date(jwtPayload.exp * 1000)
    } catch (error) {
      console.error('Error decoding token:', error)
      return null
    }
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

  const renewTokenFromRefresh = async (
    refreshToken: string,
    tokenType: 'legacy' | 'kiwix' = 'legacy',
  ) => {
    try {
      if (tokenType === 'kiwix') {
        // Refresh Kiwix token
        const kiwixAuthConfig = getKiwixAuthConfig(config)
        const kiwixToken = await refreshKiwixToken(refreshToken, kiwixAuthConfig)
        const userInfo: KiwixUserInfo = await fetchKiwixUserInfo(
          kiwixToken.access_token,
          kiwixAuthConfig,
        )

        token.value = {
          access_token: kiwixToken.access_token,
          refresh_token: kiwixToken.refresh_token || refreshToken,
          expires_time: new Date(Date.now() + kiwixToken.expires_in * 1000).toISOString(),
          token_type: 'kiwix',
          kiwix_sub: userInfo.sub,
          kiwix_refresh_token: kiwixToken.refresh_token,
        }

        user.value = {
          username: userInfo.preferred_username || userInfo.email || userInfo.sub,
          email: userInfo.email || '',
          scope: {}, // Permissions managed by backend
        }
      } else {
        // Refresh legacy token
        const response = await service.post<{ refresh_token: string }, Token>('/refresh', {
          refresh_token: refreshToken,
        })
        token.value = {
          ...response,
          token_type: 'legacy',
        }
        user.value = jwtDecode<JWTPayload>(token.value.access_token).user
      }

      errors.value = []
      saveTokenToCookie(token.value)
      return token.value?.access_token
    } catch (error) {
      token.value = null
      user.value = null
      errors.value = translateErrors(error as ErrorResponse)
      return null
    }
  }

  const loadTokenFromCookie = async () => {
    // Already authenticated and not expired
    if (tokenExpiryDate.value && tokenExpiryDate.value > new Date()) {
      return token.value?.access_token
    }

    const cookieValue = $cookies.get(constants.TOKEN_COOKIE_NAME)
    if (!cookieValue) return null

    let tokenData: ExtendedToken
    try {
      tokenData = cookieValue

      // For Kiwix tokens
      if (tokenData.token_type === 'kiwix') {
        const expiryDate = tokenData.expires_time ? new Date(tokenData.expires_time) : null
        const now = new Date()

        // Token expired, try to refresh
        if (expiryDate && now > expiryDate && tokenData.kiwix_refresh_token) {
          return await renewTokenFromRefresh(tokenData.kiwix_refresh_token, 'kiwix')
        }

        // Token still valid
        token.value = tokenData
        user.value = {
          username: tokenData.kiwix_sub || 'kiwix-user',
          email: '',
          scope: {},
        } as JWTUser
        return token.value.access_token
      }

      // For legacy tokens, decode JWT
      const jwtPayload = jwtDecode<JWTPayload>(tokenData.access_token)
      const expiry = new Date(jwtPayload.exp * 1000)
      const now = new Date()

      if (now > expiry) {
        return await renewTokenFromRefresh(tokenData.refresh_token, 'legacy')
      }

      token.value = {
        ...tokenData,
        token_type: 'legacy',
      }
      user.value = jwtPayload.user
      return token.value?.access_token
    } catch (error) {
      console.error('Error parsing cookie value', error)
      $cookies.remove(constants.TOKEN_COOKIE_NAME)
      return null
    }
  }

  const saveTokenToCookie = (tokenData: ExtendedToken) => {
    // Decode JWT to get actual expiry time
    // Set cookie with proper configuration for persistence
    $cookies.set(
      constants.TOKEN_COOKIE_NAME,
      JSON.stringify(tokenData),
      // persist with config cookie expiry so that even thought the cookie expires,
      // we can still use the refresh token to get a new access token without logging in again
      constants.TOKEN_COOKIE_EXPIRY,
      '/', // path
      undefined, // domain
      config.ZIMFARM_WEBAPI.startsWith('https://'), // secure flag
    )
  }

  const logout = async () => {
    // If Kiwix token, revoke it
    if (token.value?.token_type === 'kiwix' && token.value.access_token) {
      const kiwixAuthConfig = getKiwixAuthConfig(config)
      await logoutFromKiwixAuth(token.value.access_token, kiwixAuthConfig)
    }

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
      token.value = {
        ...response,
        token_type: 'legacy',
      }
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

  /**
   * Authenticate with Kiwix OAuth2 code
   */
  const authenticateWithKiwix = async (code: string, codeVerifier: string) => {
    try {
      const kiwixAuthConfig = getKiwixAuthConfig(config)

      // Exchange code for token
      const kiwixToken = await exchangeCodeForToken(code, codeVerifier, kiwixAuthConfig)

      // Fetch user info
      const userInfo: KiwixUserInfo = await fetchKiwixUserInfo(
        kiwixToken.access_token,
        kiwixAuthConfig,
      )

      // Create extended token
      const extendedToken: ExtendedToken = {
        access_token: kiwixToken.access_token,
        refresh_token: kiwixToken.refresh_token || '',
        expires_time: new Date(Date.now() + kiwixToken.expires_in * 1000).toISOString(),
        token_type: 'kiwix',
        kiwix_sub: userInfo.sub,
        kiwix_refresh_token: kiwixToken.refresh_token,
      }

      token.value = extendedToken

      // Create user object from Kiwix userinfo
      user.value = {
        username: userInfo.preferred_username || userInfo.email || userInfo.sub,
        email: userInfo.email || '',
        scope: {}, // Permissions will be managed by backend based on idp_sub
      }

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

  const getApiService = async (baseURL: string) => {
    const token = await loadTokenFromCookie()
    if (!token)
      return httpRequest({
        baseURL: `${config.ZIMFARM_WEBAPI}/${baseURL}`,
      })

    return httpRequest({
      baseURL: `${config.ZIMFARM_WEBAPI}/${baseURL}`,
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
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
    hasPermission,
    loadTokenFromCookie,
    renewTokenFromRefresh,
    authenticate,
    authenticateWithKiwix,
    logout,
    getApiService,
  }
})
