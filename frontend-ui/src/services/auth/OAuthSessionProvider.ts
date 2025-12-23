import httpRequest from '@/utils/httpRequest'
import { jwtDecode } from 'jwt-decode'
import { AuthProvider, type OAuthConfig } from '@/services/auth/base'
import { type StoredToken } from '@/types/auth'

interface OAuthSessionResponse {
  id: string
  expires_at: string
  issued_at: string
  active: boolean
  authenticator_assurance_level: string
  authenticated_at: string
  tokenized: string // JWT token
}

interface LogoutSessionResponse {
  logout_url: string
  logout_token: string
}

/**
 * Session-based authentication provider
 * Uses cookie-based sessions managed by the Kiwix auth server
 */
export class OAuthSessionProvider extends AuthProvider {
  protected config: OAuthConfig
  #token: StoredToken | null = null // in memory reference to token
  #shouldLoadToken: boolean = true // if token should be loaded again

  constructor(config: OAuthConfig) {
    super()
    this.config = config
  }
  /**
   * Initiates session-based login by redirecting to self-service login
   */
  async initiateLogin(): Promise<void> {
    const loginUrl = this.buildLoginRedirectUrl('/oauth/callback')
    window.location.href = loginUrl
  }

  async loadToken(): Promise<StoredToken | null> {
    if (!this.#shouldLoadToken) return null

    if (!this.#token) return await this.refreshAuth()

    if (!this.#token.access_token || !this.#token.refresh_token || !this.#token.token_type) {
      this.#token = null
      return null
    }

    return this.#token
  }

  removeToken(): void {
    this.#token = null
    this.#shouldLoadToken = false
  }

  saveToken(token: StoredToken): null {
    this.#token = token
    return null
  }

  /**
   * Logout from session-based auth
   * Session-based auth typically handles logout via server-side session destruction
   */
  async logout(): Promise<void> {
    this.#token = null
    this.#shouldLoadToken = false

    const service = httpRequest({
      baseURL: `${this.config.basePath}`,
    })
    const response = await service.get<null, LogoutSessionResponse>('/self-service/logout/browser')
    await service.get<null, null>('/self-service/logout', {
      params: { token: response.logout_token },
    })
  }

  /**
   * Calls /sessions/whoami?tokenize_as=kiwix-tokenizer endpoint
   * to get current session information
   */
  async refreshAuth(): Promise<StoredToken> {
    const service = httpRequest({
      baseURL: `${this.config.basePath}/sessions`,
    })

    let response: OAuthSessionResponse
    try {
      response = await service.get<null, OAuthSessionResponse>(
        '/whoami?tokenize_as=kiwix-tokenizer',
      )
    } catch (error: unknown) {
      console.error('Failed to refresh token: ', error)
      this.#shouldLoadToken = false
      throw error
    }
    const decoded = jwtDecode(response.tokenized)
    if (!decoded.exp) {
      throw new Error('Invalid JWT token')
    }
    const newToken: StoredToken = {
      access_token: response.tokenized,
      expires_time: new Date(decoded.exp * 1000).toISOString(),
      refresh_token: response.tokenized,
      token_type: 'oauth',
    }
    this.#shouldLoadToken = true
    this.saveToken(newToken)
    return newToken
  }

  /**
   * Handles callback for session-based auth
   * Session-based auth doesn't use callbacks in the same way as OIDC
   */
  async onCallback(): Promise<StoredToken> {
    return await this.refreshAuth()
  }

  private getRedirectUri(returnUrl: string): string {
    return `${window.location.origin}${returnUrl}`
  }

  /**
   * Build the login redirect URL for self-service login
   * User should be redirected here when they don't have an active session
   */
  private buildLoginRedirectUrl(returnToUrl: string): string {
    const params = new URLSearchParams({
      return_to: this.getRedirectUri(returnToUrl),
    })

    return `${this.config.basePath}/self-service/login/browser?${params.toString()}`
  }
}
