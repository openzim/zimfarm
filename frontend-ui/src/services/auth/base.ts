import type { Config } from '@/config'
import type { StoredToken } from '@/types/auth'

export interface KiwixAuthConfig {
  clientId: string
  authorizeUrl: string
  tokenUrl: string
  userInfoUrl: string
  revocationUrl: string
  basePath: string
}

/**
 * Get Kiwix authentication configuration from app config
 */
export function getKiwixAuthConfig(config: Config): KiwixAuthConfig {
  const basePath = config.KIWIX_AUTH_BASE_URL
  return {
    clientId: config.KIWIX_AUTH_CLIENT_ID,
    authorizeUrl: `${basePath}/oauth2/auth`,
    tokenUrl: `${basePath}/oauth2/token`,
    userInfoUrl: `${basePath}/userinfo`,
    revocationUrl: `${basePath}/oauth2/revoke`,
    basePath: basePath,
  }
}

/**
 * Get redirect URI based on current origin
 */
export function getRedirectUri(): string {
  return `${window.location.origin}/oauth/callback`
}

/**
 * Abstract base class for authentication providers
 * Defines the common interface that all auth providers must implement
 */
export abstract class AuthProvider {
  /**
   * Initiates the login flow
   */
  abstract initiateLogin(returnUrl?: string, username?: string, password?: string): Promise<void>

  /**
   * Handles the logout process
   */
  abstract logout(accessToken?: string): Promise<void>

  /**
   * Refreshes the authentication credentials
   */
  abstract refreshAuth(refreshToken: string): Promise<StoredToken>

  /**
   * Handles the authentication callback from the auth provider
   */
  abstract onCallback(callbackUrl: string): Promise<StoredToken>

  /**
   * Save the token from the auth provider
   */
  abstract saveToken(token: StoredToken): null

  /**
   * Load auth token
   */
  abstract loadToken(): Promise<StoredToken | null>

  abstract removeToken(): void
}
