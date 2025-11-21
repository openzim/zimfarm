import datetime
import hashlib
from dataclasses import dataclass

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
from zimfarm_backend.common import getnow

_ory_client_configuration = OryClientConfiguration(
    host=KIWIX_ISSUER, access_token=ORY_ACCESS_TOKEN
)


@dataclass
class _CachedToken:
    """Cached introspected token with expiration time."""

    introspected_token: IntrospectedOAuth2Token
    expires_at: datetime.datetime


# Cache to store introspected tokens with their expiration time
# Key is SHA256 hash of the token, value is _CachedToken
_introspection_token_cache: dict[str, _CachedToken] = {}


def _hash_token(token: str) -> str:
    """Hash token for use as cache key to avoid storing raw tokens in memory."""
    return hashlib.sha256(token.encode()).hexdigest()


def _is_cache_entry_valid(cached: _CachedToken) -> bool:
    """Check if a cached token entry is still valid (not expired)."""
    return getnow() < cached.expires_at


def _get_cached_introspection_token(token: str) -> IntrospectedOAuth2Token | None:
    """Get cached introspection result if available and not expired."""
    token_hash = _hash_token(token)
    if cached := _introspection_token_cache.get(token_hash):
        if _is_cache_entry_valid(cached):
            return cached.introspected_token
        # Remove expired entry
        del _introspection_token_cache[token_hash]
    return None


def _cache_introspection_token(token: str, introspected_token: IntrospectedOAuth2Token):
    """Cache an introspected token with TTL based on its expiration time."""
    token_hash = _hash_token(token)
    # Use token's exp time if available, otherwise cache for a short duration
    if introspected_token.exp:
        # exp is a Unix timestamp (seconds since epoch)
        expires_at = datetime.datetime.fromtimestamp(introspected_token.exp)
        _introspection_token_cache[token_hash] = _CachedToken(
            introspected_token=introspected_token,
            expires_at=expires_at,
        )


def verify_kiwix_access_token(token: str) -> IntrospectedOAuth2Token:
    """Verify a Kiwix access token by calling introspection endpoint.

    Results are cached based on token expiration time to reduce API calls.
    """
    # Check cache first
    if cached_token := _get_cached_introspection_token(token):
        return cached_token

    # Cache miss - perform introspection
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

        # Cache the successful introspection result
        _cache_introspection_token(token, introspected_token)

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
