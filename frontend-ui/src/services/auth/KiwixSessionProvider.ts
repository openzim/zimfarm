import type { KiwixSessionResponse } from '@/types/user'
import httpRequest from '@/utils/httpRequest'
import { jwtDecode } from 'jwt-decode'
import { AuthProvider, type KiwixAuthConfig } from '@/services/auth/base'
import { type StoredToken } from '@/types/auth'

/**
 * Session-based authentication provider
 * Uses cookie-based sessions managed by the Kiwix auth server
 */
export class KiwixSessionProvider extends AuthProvider {
  protected config: KiwixAuthConfig
  #token: StoredToken | null = null // in memory reference to token

  constructor(config: KiwixAuthConfig) {
    super()
    this.config = config
  }
  /**
   * Initiates session-based login by redirecting to self-service login
   */
  async initiateLogin(returnUrl?: string): Promise<void> {
    const returnToUrl = returnUrl || window.location.href
    const loginUrl = this.buildLoginRedirectUrl(returnToUrl)
    window.location.href = loginUrl
  }

  async loadToken(): Promise<StoredToken | null> {
    if (!this.#token) return await this.refreshAuth()

    if (!this.#token.access_token || !this.#token.refresh_token || !this.#token.token_type) {
      this.#token = null
      return null
    }

    return this.#token
  }

  removeToken(): void {
    this.#token = null
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
  }

  /**
   * Calls /sessions/whoami?tokenize_as=kiwix-tokenizer endpoint
   * to get current session information
   */
  async refreshAuth(): Promise<StoredToken> {
    const service = httpRequest({
      baseURL: `${this.config.basePath}/sessions`,
    })

    const response = await service.get<null, KiwixSessionResponse>(
      '/whoami?tokenize_as=kiwix-tokenizer',
    )
    const decoded = jwtDecode(response.tokenized)
    if (!decoded.exp) {
      throw new Error('Invalid JWT token')
    }
    const newToken: StoredToken = {
      access_token: response.tokenized,
      expires_time: new Date(decoded.exp * 1000).toISOString(),
      refresh_token: response.tokenized,
      token_type: 'kiwix',
    }
    this.saveToken(newToken)
    return newToken
  }

  /**
   * Handles callback for session-based auth
   * Session-based auth doesn't use callbacks in the same way as OIDC
   */
  async onCallback(): Promise<StoredToken> {
    throw new Error('onCallback not applicable for session-based authentication')
  }

  /**
   * Build the login redirect URL for self-service login
   * User should be redirected here when they don't have an active session
   */
  private buildLoginRedirectUrl(returnToUrl: string): string {
    const params = new URLSearchParams({
      return_to: returnToUrl,
    })
    return `${this.config.basePath}/self-service/login/browser?${params.toString()}`
  }
}
