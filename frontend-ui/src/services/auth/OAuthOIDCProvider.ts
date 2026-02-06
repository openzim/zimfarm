import httpRequest from '@/utils/httpRequest'
import { type StoredToken } from '@/types/auth'
import constants from '@/constants'
import { AuthProvider, type OAuthConfig } from '@/services/auth/base'

interface OAuthOIDCTokenResponse {
  access_token: string
  token_type: string
  expires_in: number
  refresh_token: string
  id_token: string
}

/**
 * OIDC/OAuth2 authentication provider using PKCE flow
 */
export class OAuthOIDCProvider extends AuthProvider {
  protected config: OAuthConfig
  protected keyName: string

  constructor(config: OAuthConfig) {
    super()
    this.config = config
    this.keyName = `${constants.TOKEN_STORAGE_KEY}-oauth-oidc`
  }
  /**
   * Initiates the OAuth2 PKCE flow
   * Generates PKCE parameters, stores them, and redirects to Kiwix authorization endpoint
   */
  async initiateLogin(): Promise<void> {
    const codeVerifier = this.generateCodeVerifier()
    const codeChallenge = await this.generateCodeChallenge(codeVerifier)
    const state = this.generateState()

    // Store PKCE parameters for later validation
    this.storePKCEParams(codeVerifier, state)

    // Build authorization URL with all required OAuth2 parameters
    // Note: Only requesting 'openid' and 'offline_access' as these are the only
    // scopes supported by this Kiwix auth instance (profile and email are not available)
    const params = new URLSearchParams({
      client_id: this.config.clientId,
      response_type: 'code',
      redirect_uri: this.getRedirectUri('/oauth/callback'),
      state: state,
      code_challenge: codeChallenge,
      code_challenge_method: 'S256',
      scope: 'openid profile offline_access',
    })

    const authUrl = `${this.config.authorizeUrl}?${params.toString()}`

    // Redirect to Kiwix authorization page
    window.location.href = authUrl
  }

  /**
   * Logout from Kiwix auth session by revoking the access token
   */
  async logout(accessToken?: string): Promise<void> {
    if (!accessToken) return

    const service = httpRequest({
      baseURL: this.config.revocationUrl,
    })

    const params = new URLSearchParams({
      client_id: this.config.clientId,
      token: accessToken,
    })

    try {
      await service.post<URLSearchParams, void>('', params, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      })
    } catch (error) {
      console.error('Error revoking token:', error)
      // Continue with logout even if revocation fails
    }
    this.removeToken()
  }

  /**
   * Refresh access token using refresh token
   */
  async refreshAuth(refreshToken?: string): Promise<StoredToken> {
    if (!refreshToken) {
      throw new Error('Refresh token is missing.')
    }
    const service = httpRequest({
      baseURL: this.config.tokenUrl,
    })

    const params = new URLSearchParams({
      grant_type: 'refresh_token',
      client_id: this.config.clientId,
      refresh_token: refreshToken,
    })

    const response = await service.post<URLSearchParams, OAuthOIDCTokenResponse>('', params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })
    // Calculate expiry time from expires_in
    const expiresTime = new Date(Date.now() + response.expires_in * 1000).toISOString()
    const newToken: StoredToken = {
      access_token: response.id_token,
      refresh_token: response.refresh_token,
      token_type: 'oauth',
      expires_time: expiresTime,
    }
    this.saveToken(newToken)
    return newToken
  }

  /**
   * Handles OAuth callback by parsing URL, validating state, and exchanging code for token
   */
  async onCallback(callbackUrl: string): Promise<StoredToken> {
    const url = new URL(callbackUrl)
    const params = url.searchParams

    // Get code and state from URL query parameters
    const code = params.get('code')
    const state = params.get('state')
    const errorParam = params.get('error')
    const errorDescription = params.get('error_description')

    // Check for OAuth errors from Kiwix auth
    if (errorParam) {
      throw new Error(errorDescription || `OAuth error: ${errorParam}`)
    }

    if (!code || !state) {
      throw new Error('Missing authorization code or state parameter')
    }

    // Retrieve PKCE parameters from session storage
    const pkceParams = this.retrieveAndClearPKCEParams()
    if (!pkceParams) {
      throw new Error('PKCE parameters not found. Please try signing in again.')
    }

    // Verify state to prevent CSRF attacks
    if (state !== pkceParams.state) {
      throw new Error('Invalid state parameter. Possible CSRF attack.')
    }

    // Exchange authorization code for tokens using PKCE verifier
    const response = await this.exchangeCodeForToken(code, pkceParams.verifier)
    const expiresTime = new Date(Date.now() + response.expires_in * 1000).toISOString()
    return {
      access_token: response.id_token,
      refresh_token: response.refresh_token,
      token_type: 'oauth',
      expires_time: expiresTime,
    }
  }

  /**
   * Exchange authorization code for tokens
   * This is specific to OIDC flow and called after redirect from auth server
   */
  async exchangeCodeForToken(code: string, codeVerifier: string): Promise<OAuthOIDCTokenResponse> {
    const service = httpRequest({
      baseURL: this.config.tokenUrl,
    })

    const params = new URLSearchParams({
      grant_type: 'authorization_code',
      client_id: this.config.clientId,
      code: code,
      redirect_uri: this.getRedirectUri('/oauth/callback'),
      code_verifier: codeVerifier,
    })

    const response = await service.post<URLSearchParams, OAuthOIDCTokenResponse>('', params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })
    return response
  }

  saveToken(token: StoredToken): null {
    localStorage.setItem(this.keyName, JSON.stringify(token))
    return null
  }

  removeToken(): void {
    localStorage.removeItem(this.keyName)
  }

  async loadToken(): Promise<StoredToken | null> {
    const storedValue = localStorage.getItem(this.keyName)
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
   * Get redirect URI based on current origin
   */
  private getRedirectUri(returnUrl: string): string {
    return `${window.location.origin}${returnUrl}`
  }

  /**
   * Generates a random code verifier for PKCE
   */
  private generateCodeVerifier(): string {
    const array = new Uint8Array(32)
    crypto.getRandomValues(array)
    return this.base64URLEncode(array)
  }

  /**
   * Generates code challenge from verifier using SHA-256
   */
  private async generateCodeChallenge(verifier: string): Promise<string> {
    const encoder = new TextEncoder()
    const data = encoder.encode(verifier)
    const hash = await crypto.subtle.digest('SHA-256', data)
    return this.base64URLEncode(new Uint8Array(hash))
  }

  /**
   * Generates a random state for CSRF protection
   */
  private generateState(): string {
    const array = new Uint8Array(32)
    crypto.getRandomValues(array)
    return this.base64URLEncode(array)
  }

  /**
   * Base64URL encoding (without padding)
   * Converts a buffer to base64url format as specified in RFC 4648
   */
  private base64URLEncode(buffer: Uint8Array): string {
    const base64 = btoa(String.fromCharCode(...buffer))
    return base64.replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '')
  }

  /**
   * Store PKCE parameters in session storage
   */
  private storePKCEParams(verifier: string, state: string): void {
    sessionStorage.setItem('pkce_code_verifier', verifier)
    sessionStorage.setItem('pkce_state', state)
  }

  /**
   * Retrieve and clear PKCE parameters from session storage
   * This should be called once during the OAuth callback to validate the flow
   */
  private retrieveAndClearPKCEParams(): { verifier: string; state: string } | null {
    const verifier = sessionStorage.getItem('pkce_code_verifier')
    const state = sessionStorage.getItem('pkce_state')

    if (!verifier || !state) {
      return null
    }

    // Clear from storage immediately after retrieval
    sessionStorage.removeItem('pkce_code_verifier')
    sessionStorage.removeItem('pkce_state')

    return { verifier, state }
  }
}
