from zimfarm_backend.common.schemas import BaseModel


class CredentialsIn(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    """Access token on successful authentication."""

    access_token: str
    token_type: str = "Bearer"
    expires_in: float
    refresh_token: str
