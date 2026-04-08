export interface BaseUser {
  id: string
  username: string | null
  display_name: string
  has_password?: boolean
}

export interface JWTUser extends BaseUser {
  scope: Record<string, Record<string, boolean>>
}

export interface JWTPayload {
  iss: string
  exp: number
  iat: number
  subject: string
}

export interface User extends JWTUser {
  role: string
  idp_sub?: string
}

export interface Token {
  access_token: string
  refresh_token: string
  expires_time: string
}
