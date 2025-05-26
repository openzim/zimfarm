from typing import Literal
from uuid import UUID

from zimfarm_backend.common.schemas import BaseModel


class CredentialsIn(BaseModel):
    username: str
    password: str


class RefreshTokenIn(BaseModel):
    refresh_token: UUID


class OAuth2CredentialsWithPassword(CredentialsIn):
    grant_type: Literal["password"]


class OAuth2CredentialsWithRefreshToken(RefreshTokenIn):
    grant_type: Literal["refresh_token"]


class Token(BaseModel):
    """Access token on successful authentication."""

    access_token: str
    token_type: str = "Bearer"
    expires_in: float
    refresh_token: str
