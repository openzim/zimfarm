export function generateCodeVerifier(): string {
  const array = new Uint8Array(32)
  crypto.getRandomValues(array)
  return base64URLEncode(array)
}

/**
 * Generates code challenge from verifier using SHA-256
 */
export async function generateCodeChallenge(verifier: string): Promise<string> {
  const encoder = new TextEncoder()
  const data = encoder.encode(verifier)
  const hash = await crypto.subtle.digest('SHA-256', data)
  return base64URLEncode(new Uint8Array(hash))
}

/**
 * Generates a random state for CSRF protection
 */
export function generateState(): string {
  const array = new Uint8Array(32)
  crypto.getRandomValues(array)
  return base64URLEncode(array)
}

/**
 * Base64URL encoding (without padding)
 * Converts a buffer to base64url format as specified in RFC 4648
 */
function base64URLEncode(buffer: Uint8Array): string {
  const base64 = btoa(String.fromCharCode(...buffer))
  return base64.replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '')
}

/**
 * Store PKCE parameters in session storage
 */
export function storePKCEParams(verifier: string, state: string): void {
  sessionStorage.setItem('pkce_code_verifier', verifier)
  sessionStorage.setItem('pkce_state', state)
}

/**
 * Retrieve and clear PKCE parameters from session storage
 * This should be called once during the OAuth callback to validate the flow
 */
export function retrieveAndClearPKCEParams(): { verifier: string; state: string } | null {
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
