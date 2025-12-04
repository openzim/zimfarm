export interface BaseUser {
  username: string
}

export interface JWTUser extends BaseUser {
  email: string
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

export interface BaseSshKey {
  key: string
  name: string
  type: string
}

export interface SshKeyRead extends BaseSshKey {
  added: string
  fingerprint: string
}

export interface BaseUserWithSshKeys extends BaseUser, BaseSshKey {}

export interface SshKeyList {
  ssh_keys: SshKeyRead[]
}

export interface UserWithSshKeys extends User, SshKeyList {
  ssh_keys: SshKeyRead[]
}

// Kiwix OAuth2 authentication types
export interface KiwixTokenResponse {
  access_token: string
  token_type: string
  expires_in: number
  refresh_token: string
}
