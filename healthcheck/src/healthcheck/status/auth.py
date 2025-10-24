import datetime

from pydantic import BaseModel

from healthcheck.cache import memoize
from healthcheck.constants import ZIMFARM_API_URL, ZIMFARM_PASSWORD, ZIMFARM_USERNAME
from healthcheck.requests import query_api
from healthcheck.status import Result


class Token(BaseModel):
    """Access token on successful authentication."""

    access_token: str
    expires_time: datetime.datetime
    refresh_token: str
    token_type: str = "Bearer"


@memoize("ZIMFARM_AUTH")
async def authenticate() -> Result[Token]:
    """Check if authentication is sucessful with Zimfarm"""
    response = await query_api(
        f"{ZIMFARM_API_URL}/auth/authorize",
        method="POST",
        payload={"username": ZIMFARM_USERNAME, "password": ZIMFARM_PASSWORD},
    )
    return Result(
        success=response.success,
        status_code=response.status_code,
        data=Token.model_validate(response.json) if response.success else None,
    )
