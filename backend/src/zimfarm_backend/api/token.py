import datetime

import jwt
from ory_client.api.o_auth2_api import OAuth2Api as OryOAuth2Api
from ory_client.api_client import ApiClient as OryApiClient
from ory_client.configuration import Configuration as OryClientConfiguration
from ory_client.exceptions import ApiException
from ory_client.models.introspected_o_auth2_token import IntrospectedOAuth2Token

from zimfarm_backend import logger
from zimfarm_backend.api.constants import (
    JWT_SECRET,
    JWT_TOKEN_EXPIRY_DURATION,
    JWT_TOKEN_ISSUER,
    KIWIX_CLIENT_ID,
    KIWIX_ISSUER,
    ORY_ACCESS_TOKEN,
)

_ory_client_configuration = OryClientConfiguration(
    host=KIWIX_ISSUER, access_token=ORY_ACCESS_TOKEN
)


def verify_kiwix_access_token(token: str) -> IntrospectedOAuth2Token:
    """Verify a Kiwix access token by calling introspection endpoint."""
    with OryApiClient(_ory_client_configuration) as api_client:
        api_instance = OryOAuth2Api(api_client)
        try:
            introspected_token = api_instance.introspect_o_auth2_token(token)
        except ApiException as e:
            logger.exception("Failed to verify Kiwix access token")
            raise ValueError("Failed to verify Kiwix access token") from e
        if not introspected_token.active:
            raise ValueError("Kiwix access token is not active")
        if KIWIX_ISSUER != introspected_token.iss:
            raise ValueError("Kiwix access token issuer is not valid")
        if KIWIX_CLIENT_ID != introspected_token.client_id:
            raise ValueError("Kiwix access token client ID is not valid")
        return introspected_token


def generate_access_token(
    *,
    user_id: str,
    issue_time: datetime.datetime,
) -> str:
    """Generate a JWT access token for the given user ID with configured expiry."""

    expire_time = issue_time + datetime.timedelta(seconds=JWT_TOKEN_EXPIRY_DURATION)
    payload = {
        "iss": JWT_TOKEN_ISSUER,  # issuer
        "exp": expire_time.timestamp(),  # expiration time
        "iat": issue_time.timestamp(),  # issued at
        "subject": user_id,
    }
    return jwt.encode(payload, key=JWT_SECRET, algorithm="HS256")
