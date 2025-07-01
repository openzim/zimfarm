export interface User {
  username: string;
  scope: Record<string, Record<string, boolean>>;
  role: string;
}

export interface JWTPayload {
  iss: string;
  exp: number;
  iat: number;
  subject: string;
  user: User;
}

export interface Token {
  access_token: string;
  refresh_token: string;
  expires_in: number;
}
