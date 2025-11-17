import type { Config } from '@/config'
import type { KiwixTokenResponse } from '@/types/user'
import httpRequest from '@/utils/httpRequest'
import {
  generateCodeChallenge,
  generateCodeVerifier,
  generateState,
  storePKCEParams,
} from '@/utils/pkce'

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
 * Initiates the OAuth2 PKCE flow
 * Generates PKCE parameters, stores them, and redirects to Kiwix authorization endpoint
 */
export async function initiateKiwixLogin(config: KiwixAuthConfig): Promise<void> {
  const codeVerifier = generateCodeVerifier()
  const codeChallenge = await generateCodeChallenge(codeVerifier)
  const state = generateState()

  // Store PKCE parameters for later validation
  storePKCEParams(codeVerifier, state)

  // Build authorization URL with all required OAuth2 parameters
  // Note: Only requesting 'openid' and 'offline_access' as these are the only
  // scopes supported by this Kiwix auth instance (profile and email are not available)
  const params = new URLSearchParams({
    client_id: config.clientId,
    response_type: 'code',
    redirect_uri: getRedirectUri(),
    state: state,
    code_challenge: codeChallenge,
    code_challenge_method: 'S256',
    scope: 'openid offline_access',
  })

  const authUrl = `${config.authorizeUrl}?${params.toString()}`

  // Redirect to Kiwix authorization page
  window.location.href = authUrl
}

/**
 * Exchange authorization code for tokens
 */
export async function exchangeCodeForToken(
  code: string,
  codeVerifier: string,
  config: KiwixAuthConfig,
): Promise<KiwixTokenResponse> {
  const service = httpRequest({
    baseURL: config.tokenUrl,
  })

  const params = new URLSearchParams({
    grant_type: 'authorization_code',
    client_id: config.clientId,
    code: code,
    redirect_uri: getRedirectUri(),
    code_verifier: codeVerifier,
  })

  const response = await service.post<URLSearchParams, KiwixTokenResponse>('', params, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  })
  return response
}

/**
 * Refresh access token using refresh token
 */
export async function refreshKiwixToken(
  refreshToken: string,
  config: KiwixAuthConfig,
): Promise<KiwixTokenResponse> {
  const service = httpRequest({
    baseURL: config.tokenUrl,
  })

  const params = new URLSearchParams({
    grant_type: 'refresh_token',
    client_id: config.clientId,
    refresh_token: refreshToken,
  })

  const response = await service.post<URLSearchParams, KiwixTokenResponse>('', params, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  })
  return response
}

/**
 * Logout from Kiwix auth session by revoking the access token
 */
export async function logoutFromKiwixAuth(
  accessToken: string | undefined,
  config: KiwixAuthConfig,
): Promise<void> {
  if (!accessToken) return

  const service = httpRequest({
    baseURL: config.revocationUrl,
  })

  const params = new URLSearchParams({
    client_id: config.clientId,
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
}
