export type AuthProviderType = 'local' | 'kiwix'

export interface StoredToken {
  access_token: string
  refresh_token: string
  token_type: AuthProviderType
  expires_time: string // ISO 8601 datetime string
}
