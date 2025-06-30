export interface User {
  username: string;
  scope: Record<string, Record<string, boolean>>;
}

export interface Token {
  accessToken: string;
  refreshToken: string;
  payload: {
    user: User;
    exp: number;
  };
}
