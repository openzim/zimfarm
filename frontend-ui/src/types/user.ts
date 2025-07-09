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
  user: JWTUser
}

export interface User extends JWTUser {
  role: string
}

export interface Token {
  access_token: string
  refresh_token: string
  expires_in: number
}

export interface BaseSshKey {
  key: string
  name: string
  type: string
}

export interface SshKeyRead extends BaseSshKey {
  added: string
  fingerprint: string
  pkcs8_key: string
}

export interface BaseUserWithSshKeys extends BaseUser, BaseSshKey
{
}


export interface SshKeyList {
  ssh_keys: SshKeyRead[]
}

export interface UserWithSshKeys extends BaseUser, SshKeyList {
  ssh_keys: SshKeyRead[]
}
