import datetime
import time
from typing import Any

import jwt
from jwt import PyJWKClient

from zimfarm_backend.api.constants import (
    JWT_SECRET,
    JWT_TOKEN_EXPIRY_DURATION,
    JWT_TOKEN_ISSUER,
    KIWIX_JWKS_URI,
)


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


class JWKSVerifier:
    """
    Verifies JWT tokens using JWKS from an identity provider (offline verification)."""

    def __init__(self, jwks_uri: str, cache_ttl: int = 3600):
        """Initialize the JWKS verifier."""
        self.jwks_uri = jwks_uri
        self.cache_ttl = cache_ttl
        self._jwk_client: PyJWKClient | None = None
        self._init_time = 0

    def _get_jwk_client(self) -> PyJWKClient:
        """
        Get or create the JWK client with cache management.
        """
        current_time = time.time()

        # Reinitialize client if cache has expired or not initialized
        if (
            self._jwk_client is None
            or (current_time - self._init_time) > self.cache_ttl
        ):
            self._jwk_client = PyJWKClient(
                uri=self.jwks_uri,
                cache_keys=True,  # Enable key caching for offline verification
                max_cached_keys=16,
                lifespan=self.cache_ttl,
            )
            self._init_time = current_time

        return self._jwk_client

    def verify_and_decode(
        self,
        token: str,
        audience: str | list[str] | None = None,
        issuer: str | None = None,
        algorithms: list[str] | None = None,
        *,
        verify_exp: bool = True,
    ) -> dict[str, Any]:
        """
        Verify and decode a JWT token using JWKS.
        """
        if algorithms is None:
            algorithms = ["RS256"]

        jwk_client = self._get_jwk_client()
        signing_key = jwk_client.get_signing_key_from_jwt(token)
        decoded = jwt.decode(
            token,
            signing_key.key,
            algorithms=algorithms,
            audience=audience,
            issuer=issuer,
            options={
                "verify_signature": True,
                "verify_exp": verify_exp,
                "verify_aud": audience is not None,
                "verify_iss": issuer is not None,
                "verify_iat": True,
            },
        )
        return decoded

    def decode_unverified(self, token: str) -> dict[str, Any]:
        """
        Decode a JWT without verification (for debugging/inspection only).

        WARNING: Do not use this for authentication! This does not verify
        the signature and should only be used for debugging.

        Args:
            token: The JWT token to decode

        Returns:
            Decoded JWT payload
        """
        return jwt.decode(token, options={"verify_signature": False})


jwks_verifier = JWKSVerifier(KIWIX_JWKS_URI, cache_ttl=3600)
