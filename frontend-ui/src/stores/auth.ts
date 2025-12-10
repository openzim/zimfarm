import type { Config } from '@/config'
import constants from '@/constants'
import type { ErrorResponse, OAuth2ErrorResponse } from '@/types/errors'
import type { JWTUser } from '@/types/user'
import { translateErrors } from '@/utils/errors'
import {
  exchangeCodeForToken,
  getKiwixAuthConfig,
  logoutFromKiwixAuth,
  refreshKiwixToken,
} from '@/services/auth/kiwix'
import httpRequest from '@/utils/httpRequest'
import { defineStore } from 'pinia'
import { computed, inject, ref } from 'vue'

interface StoredToken {
  access_token: string
  refresh_token: string
  token_type: 'api' | 'kiwix'
  expires_time: string // ISO 8601 datetime string
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<StoredToken | null>(null)
  const user = ref<JWTUser | null>(null)
  const errors = ref<string[]>([])

  // Track refresh state to prevent duplicate requests
  const isRefreshFailed = ref(false)
  const refreshPromise = ref<Promise<StoredToken | null> | null>(null)

  const config = inject<Config>(constants.config)

  if (!config) {
    throw new Error('Config is not defined')
  }

  const service = httpRequest({
    baseURL: `${config.ZIMFARM_WEBAPI}/auth`,
  })

  // Computed properties
  const isLoggedIn = computed(() => {
    return token.value !== null && user.value !== null
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

  const tokenExpiryDate = computed(() => {
    if (!token.value) return null
    return new Date(token.value.expires_time)
  })

  const isTokenExpired = computed(() => {
    if (!tokenExpiryDate.value) return true
    return new Date() >= tokenExpiryDate.value
  })

  /**
   * Check if an error is a permanent refresh token failure
   */
  const isPermanentRefreshFailure = (error: unknown): boolean => {
    // Check if it's an OAuth2 error response
    const oauth2Error = error as OAuth2ErrorResponse
    if (oauth2Error?.error === 'invalid_grant') {
      return true
    }

    // Check if it's a backend API error response
    const apiError = error as ErrorResponse
    if (apiError?.message) {
      const message = apiError.message.toLowerCase()
      if (
        message.includes('invalid authentication credentials') ||
        message.includes('refresh token expired')
      ) {
        return true
      }
    }

    return false
  }

  const fetchUserInfo = async (accessToken: string) => {
    try {
      const apiService = httpRequest({
        baseURL: `${config.ZIMFARM_WEBAPI}/auth`,
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      })
      const response = (await apiService.get('/me')) as JWTUser
      user.value = response
      errors.value = []
    } catch (error) {
      console.error('Failed to fetch user info:', error)
      user.value = null
      errors.value = translateErrors(error as ErrorResponse)
      throw error
    }
  }

  const renewTokenFromApi = async (refreshToken: string): Promise<StoredToken | null> => {
    try {
      const response = await service.post<
        { refresh_token: string },
        { access_token: string; refresh_token: string; expires_time: string }
      >('/refresh', {
        refresh_token: refreshToken,
      })

      const newToken: StoredToken = {
        access_token: response.access_token,
        refresh_token: response.refresh_token,
        token_type: 'api',
        expires_time: response.expires_time,
      }

      token.value = newToken
      await fetchUserInfo(newToken.access_token)
      errors.value = []
      saveTokenToLocalStorage(newToken)

      // Reset failure flag on success
      isRefreshFailed.value = false

      return newToken
    } catch (error) {
      console.error('Token refresh failed:', error)

      // Check if this is a permanent failure
      if (isPermanentRefreshFailure(error)) {
        isRefreshFailed.value = true
        console.log('Refresh token permanently failed, will not retry')
      }

      token.value = null
      user.value = null
      errors.value = translateErrors(error as ErrorResponse)
      return null
    }
  }

  const renewTokenFromKiwixOAuth = async (refreshToken: string): Promise<StoredToken | null> => {
    try {
      const kiwixAuthConfig = getKiwixAuthConfig(config)
      const response = await refreshKiwixToken(refreshToken, kiwixAuthConfig)

      // Calculate expiry time from expires_in
      const expiresTime = new Date(Date.now() + response.expires_in * 1000).toISOString()

      const newToken: StoredToken = {
        access_token: response.id_token,
        refresh_token: response.refresh_token,
        token_type: 'kiwix',
        expires_time: expiresTime,
      }

      token.value = newToken
      await fetchUserInfo(newToken.access_token)
      errors.value = []
      saveTokenToLocalStorage(newToken)

      // Reset failure flag on success
      isRefreshFailed.value = false

      return newToken
    } catch (error) {
      console.error('Kiwix token refresh failed:', error)

      // Check if this is a permanent failure
      if (isPermanentRefreshFailure(error)) {
        isRefreshFailed.value = true
        console.log('Kiwix refresh token permanently failed, will not retry')
      }

      token.value = null
      user.value = null
      errors.value = translateErrors(error as ErrorResponse)
      return null
    }
  }

  const renewToken = async (storedToken: StoredToken): Promise<string | null> => {
    // If refresh has already failed permanently, don't retry
    if (isRefreshFailed.value) {
      console.log('Skipping refresh attempt - refresh token previously failed')
      localStorage.removeItem(constants.TOKEN_STORAGE_KEY)
      return null
    }

    // If a refresh is already in progress, wait for it
    if (refreshPromise.value) {
      console.log('Refresh already in progress, waiting for existing request...')
      const result = await refreshPromise.value
      return result?.access_token || null
    }

    if (!storedToken.refresh_token) {
      console.error('No refresh token available')
      return null
    }

    const tokenType = storedToken.token_type

    // Create and store the refresh promise to prevent duplicate requests
    if (tokenType === 'api') {
      refreshPromise.value = renewTokenFromApi(storedToken.refresh_token)
    } else if (tokenType === 'kiwix') {
      refreshPromise.value = renewTokenFromKiwixOAuth(storedToken.refresh_token)
    } else {
      console.error('Unknown token type:', tokenType)
      return null
    }

    try {
      const newToken = await refreshPromise.value
      return newToken?.access_token || null
    } finally {
      // Clear the promise once done
      refreshPromise.value = null
    }
  }

  const loadTokenFromLocalStorage = async (): Promise<string | null> => {
    // If already authenticated and token is still valid, return current token
    if (token.value && tokenExpiryDate.value && tokenExpiryDate.value > new Date()) {
      return token.value.access_token
    }

    // Try to load from localStorage
    const storedValue = localStorage.getItem(constants.TOKEN_STORAGE_KEY)
    if (!storedValue) return null

    let storedToken: StoredToken
    try {
      storedToken = JSON.parse(storedValue)

      // Validate token structure
      if (!storedToken.access_token || !storedToken.refresh_token || !storedToken.token_type) {
        throw new Error('Invalid token structure in localStorage')
      }
    } catch (error) {
      console.error('Error parsing localStorage value', error)
      // Incorrect token payload
      localStorage.removeItem(constants.TOKEN_STORAGE_KEY)
      return null
    }

    // Check if token is expired
    const expiry = new Date(storedToken.expires_time)
    const now = new Date()

    if (now > expiry) {
      // Token expired, check if refresh is already in progress
      if (refreshPromise.value) {
        console.log('Token refresh already in progress, waiting for existing request...')
        const result = await refreshPromise.value
        return result?.access_token || null
      }
      // Try to refresh
      return await renewToken(storedToken)
    }

    // Token is still valid
    token.value = storedToken
    try {
      await fetchUserInfo(storedToken.access_token)
      return storedToken.access_token
    } catch (error) {
      // If fetching user info fails, check if refresh is already in progress
      console.error('Failed to fetch user info, attempting token refresh', error)
      if (refreshPromise.value) {
        console.log('Token refresh already in progress, waiting for existing request...')
        const result = await refreshPromise.value
        return result?.access_token || null
      }
      return await renewToken(storedToken)
    }
  }

  const saveTokenToLocalStorage = (tokenData: StoredToken) => {
    localStorage.setItem(constants.TOKEN_STORAGE_KEY, JSON.stringify(tokenData))
  }

  const logout = async () => {
    // If we have a Kiwix token, revoke it
    if (token.value?.token_type === 'kiwix' && token.value.access_token) {
      try {
        const kiwixAuthConfig = getKiwixAuthConfig(config)
        await logoutFromKiwixAuth(token.value.access_token, kiwixAuthConfig)
      } catch (error) {
        console.error('Error revoking Kiwix token:', error)
      }
    }

    token.value = null
    user.value = null
    localStorage.removeItem(constants.TOKEN_STORAGE_KEY)

    // Reset refresh failure state on logout
    isRefreshFailed.value = false
    refreshPromise.value = null
  }

  const hasPermission = (resource: string, action: string) => {
    if (!token.value || !user.value) return false
    return user.value?.scope[resource]?.[action] || false
  }

  const authenticate = async (username: string, password: string) => {
    try {
      const response = await service.post<
        { username: string; password: string },
        { access_token: string; refresh_token: string; expires_time: string }
      >('/authorize', {
        username,
        password,
      })

      const newToken: StoredToken = {
        access_token: response.access_token,
        refresh_token: response.refresh_token,
        token_type: 'api',
        expires_time: response.expires_time,
      }

      token.value = newToken

      // Fetch user info from backend
      await fetchUserInfo(response.access_token)

      errors.value = []
      saveTokenToLocalStorage(newToken)

      // Reset refresh failure state on successful login
      isRefreshFailed.value = false

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

      // Calculate expiry time from expires_in
      const expiresTime = new Date(Date.now() + kiwixToken.expires_in * 1000).toISOString()

      const newToken: StoredToken = {
        access_token: kiwixToken.id_token,
        refresh_token: kiwixToken.refresh_token,
        token_type: 'kiwix',
        expires_time: expiresTime,
      }

      token.value = newToken

      // Fetch user info from backend using the Kiwix token
      await fetchUserInfo(newToken.access_token)

      errors.value = []
      saveTokenToLocalStorage(newToken)

      // Reset refresh failure state on successful login
      isRefreshFailed.value = false

      return true
    } catch (err: unknown) {
      token.value = null
      user.value = null
      errors.value = translateErrors(err as ErrorResponse)
      return false
    }
  }

  const getApiService = async (baseURL: string) => {
    const token = await loadTokenFromLocalStorage()
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
    isRefreshFailed,
    refreshPromise,

    // Computed
    isLoggedIn,
    username,
    accessToken,
    refreshToken,
    permissions,
    tokenExpiryDate,
    isTokenExpired,

    // Methods
    saveTokenToLocalStorage,
    hasPermission,
    loadTokenFromLocalStorage,
    fetchUserInfo,
    renewToken,
    renewTokenFromApi,
    renewTokenFromKiwixOAuth,
    authenticate,
    authenticateWithKiwix,
    logout,
    getApiService,
  }
})
