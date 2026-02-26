export interface BaseUser {
  id: string
  username: string | null
  display_name: string
  has_password?: boolean
  has_ssh_keys?: boolean
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
