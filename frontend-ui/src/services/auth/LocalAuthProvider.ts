import type { StoredToken } from '@/types/auth'
import constants from '@/constants'
import { AuthProvider } from '@/services/auth/base'
import httpRequest from '@/utils/httpRequest'

/**
 * Local authentication provider for username/password authentication
 * Uses the Zimfarm API's /auth endpoints
 */
export class LocalAuthProvider extends AuthProvider {
  private zimfarmApiBaseUrl: string

  constructor(zimfarmApiBaseUrl: string) {
    super()
    this.zimfarmApiBaseUrl = zimfarmApiBaseUrl
  }

  /**
   * Initiates local login - not applicable for local auth
   * Local auth uses direct username/password authentication via authenticate method
   */
  async initiateLogin(username?: string, password?: string): Promise<void> {
    const service = httpRequest({
      baseURL: `${this.zimfarmApiBaseUrl}/auth`,
    })
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
      token_type: 'local',
      expires_time: response.expires_time,
    }
    this.saveToken(newToken)
  }

  saveToken(token: StoredToken): null {
    localStorage.setItem(constants.TOKEN_STORAGE_KEY, JSON.stringify(token))
    return null
  }

  removeToken(): void {
    localStorage.removeItem(constants.TOKEN_STORAGE_KEY)
  }

  async loadToken(): Promise<StoredToken | null> {
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
      this.removeToken()
      return null
    }
    return storedToken
  }

  /**
   * Logout from local auth
   * For local auth, we just clear client-side state (no server-side revocation)
   */
  async logout(): Promise<void> {
    this.removeToken()
  }

  /**
   * Refresh access token using refresh token for local auth
   */
  async refreshAuth(refreshToken: string): Promise<StoredToken> {
    const service = httpRequest({
      baseURL: `${this.zimfarmApiBaseUrl}/auth`,
    })
    const response = await service.post<
      { refresh_token: string },
      { access_token: string; refresh_token: string; expires_time: string }
    >('/refresh', {
      refresh_token: refreshToken,
    })

    const newToken: StoredToken = {
      access_token: response.access_token,
      refresh_token: response.refresh_token,
      token_type: 'local',
      expires_time: response.expires_time,
    }

    this.saveToken(newToken)
    return newToken
  }

  /**
   * Callback handling not applicable for local auth
   */
  async onCallback(): Promise<StoredToken> {
    throw new Error('onCallback not applicable for local username/password authentication')
  }
}
