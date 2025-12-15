import datetime
from typing import Any

import jwt
from jwt import PyJWKClient

from zimfarm_backend.api.constants import (
    JWT_SECRET,
    JWT_TOKEN_EXPIRY_DURATION,
    JWT_TOKEN_ISSUER,
    KIWIX_CLIENT_ID,
    KIWIX_ISSUER,
    KIWIX_JWKS_URI,
    KIWIX_LOGIN_REQUIRE_2FA,
)

# PyJWKClient for fetching and caching JWKS from OpenID configuration
# The client will automatically discover JWKS URI from /.well-known/openid-configuration
# and cache the keys internally
_jwks_client = PyJWKClient(KIWIX_JWKS_URI, cache_keys=True)


def verify_kiwix_access_token(token: str) -> dict[str, Any]:
    """Verify a Kiwix access token by validating JWT signature using JWKS."""
    signing_key = _jwks_client.get_signing_key_from_jwt(token)

    # Decode and verify the token
    decoded_token = jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        issuer=KIWIX_ISSUER,
        audience=KIWIX_CLIENT_ID,
        options={
            "require": ["exp", "iat", "iss", "sub", "name", "amr", "aud"],
        },
    )

    # Ensure the user logged in with two authentication factors. As per the Ory docs,
    # "password" and "oidc" are categorized as first methods of login while "totp",
    # "webauthn" and "lookup_secret" are second authentication methods
    # https://www.ory.com/docs/kratos/mfa/overview#authenticator-assurance-level-aal
    amr = set(decoded_token.get("amr", []))
    if KIWIX_LOGIN_REQUIRE_2FA and not (
        {"password", "oidc"} & amr and {"webauthn", "lookup_secrets", "totp"} & amr
    ):
        raise ValueError(
            "2FA authentication is mandatory on Zimfarm but it looks like you only "
            "have one setup on Ory. Please, configure a second one on Ory at "
            "https://login.kiwix.org/settings"
        )

    return decoded_token


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
