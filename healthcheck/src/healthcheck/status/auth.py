import datetime
from http import HTTPStatus
from typing import cast

from aiohttp.helpers import BasicAuth
from pydantic import BaseModel

from healthcheck.constants import (
    AUTH_MODE,
    REQUESTS_TIMEOUT,
    ZIMFARM_API_URL,
    ZIMFARM_OAUTH_AUDIENCE_ID,
    ZIMFARM_OAUTH_CLIENT_ID,
    ZIMFARM_OAUTH_CLIENT_SECRET,
    ZIMFARM_OAUTH_ISSUER,
    ZIMFARM_PASSWORD,
    ZIMFARM_TOKEN_RENEWAL_WINDOW,
    ZIMFARM_USERNAME,
)
from healthcheck.status import Result
from healthcheck.status import status_logger as logger
from healthcheck.status.requests import query_api


class Token(BaseModel):
    """Access token on successful authentication."""

    access_token: str
    expires_time: datetime.datetime
    refresh_token: str
    token_type: str = "Bearer"


def getnow():
    """naive UTC now"""
    return datetime.datetime.now(datetime.UTC).replace(tzinfo=None)


class ClientTokenProvider:
    """Client to generate access tokens to authenticate with Zimfarm"""

    def __init__(self):
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._expires_at: datetime.datetime = datetime.datetime.fromtimestamp(
            0
        ).replace(tzinfo=None)

    async def _generate_oauth_access_token(self) -> None:
        """Generate oauth access token and update expires_at."""

        response = await query_api(
            f"{ZIMFARM_OAUTH_ISSUER}/oauth2/token",
            method="POST",
            data={
                "grant_type": "client_credentials",
                "audience": ZIMFARM_OAUTH_AUDIENCE_ID,
            },
            auth=BasicAuth(ZIMFARM_OAUTH_CLIENT_ID, ZIMFARM_OAUTH_CLIENT_SECRET),
            timeout=REQUESTS_TIMEOUT,
            check_name="zimfarm-api-authentication",
        )
        if response.json:
            self._access_token = cast(str, response.json["access_token"])
            self._expires_at = getnow() + datetime.timedelta(
                seconds=response.json["expires_in"]
            )

    async def _generate_local_access_token(self) -> None:
        check_name = "zimfarm-api-authentication"
        if self._refresh_token:
            response = await query_api(
                f"{ZIMFARM_API_URL}/auth/refresh",
                method="POST",
                payload={
                    "refresh_token": self._refresh_token,
                },
                timeout=REQUESTS_TIMEOUT,
                check_name=check_name,
            )
        else:
            response = await query_api(
                f"{ZIMFARM_API_URL}/auth/authorize",
                method="POST",
                payload={
                    "username": ZIMFARM_USERNAME,
                    "password": ZIMFARM_PASSWORD,
                },
                timeout=REQUESTS_TIMEOUT,
                check_name=check_name,
            )

        if response.json:
            self._access_token = cast(str, response.json["access_token"])
            self._refresh_token = cast(str, response.json["refresh_token"])
            self._expires_at = datetime.datetime.fromisoformat(
                response.json["expires_time"]
            ).replace(tzinfo=None)

    async def get_access_token(self, *, force_refresh: bool = False) -> str:
        """Retrieve or generate access token depending on if token has expired."""
        now = getnow()
        if (
            force_refresh
            or self._access_token is None
            or now >= (self._expires_at - ZIMFARM_TOKEN_RENEWAL_WINDOW)
        ):
            if AUTH_MODE == "oauth":
                await self._generate_oauth_access_token()
            elif AUTH_MODE == "local":
                await self._generate_local_access_token()
            else:
                raise ValueError(
                    f"Unknown authentication mode: {AUTH_MODE}. "
                    "Allowed values are: 'local', 'oauth'"
                )
        if self._access_token is None:
            raise ValueError("Failed to generate access token.")
        return self._access_token

    @property
    def expires_at(self) -> datetime.datetime:
        return self._expires_at

    @property
    def refresh_token(self) -> str | None:
        return self._refresh_token


_token_provider = ClientTokenProvider()


async def authenticate() -> Result[Token]:
    """Check if authentication is successful with Zimfarm"""
    try:
        access_token = await _token_provider.get_access_token()
        token = Token(
            access_token=access_token,
            expires_time=_token_provider.expires_at,
            refresh_token=_token_provider.refresh_token or "",
        )

        response = await query_api(
            f"{ZIMFARM_API_URL}/auth/test",
            method="GET",
            headers={"Authorization": f"Bearer {token.access_token}"},
            check_name="zimfarm-api-authentication",
        )

        if response.success:
            logger.debug(
                f"Authentication successful using {AUTH_MODE} mode",
                extra={"checkname": "zimfarm-api-authentication"},
            )

            return Result(
                success=True,
                status_code=HTTPStatus.OK,
                data=token,
            )
        else:
            return Result(
                success=False,
                status_code=HTTPStatus.UNAUTHORIZED,
                data=None,
            )
    except Exception:
        return Result(
            success=False,
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            data=None,
        )
