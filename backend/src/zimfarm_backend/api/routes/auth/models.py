import datetime
from uuid import UUID

from zimfarm_backend.common.schemas import BaseModel


class CredentialsIn(BaseModel):
    username: str
    password: str


class RefreshTokenIn(BaseModel):
    refresh_token: UUID


class Token(BaseModel):
    """Access token on successful authentication."""

    access_token: str
    token_type: str = "Bearer"
    expires_time: datetime.datetime
    refresh_token: str
