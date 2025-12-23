# pyright: strict, reportPrivateUsage=false
import datetime
from unittest.mock import MagicMock, patch
from uuid import UUID

import jwt
import pytest

from zimfarm_backend.api.token import OAuthOIDCTokenDecoder, OAuthSessionTokenDecoder
from zimfarm_backend.common import getnow

# Authentication method constants for testing
FIRST_FACTOR_METHODS = ["password", "oidc"]
SECOND_FACTOR_METHODS = ["webauthn", "lookup_secrets", "totp"]


def create_test_jwt_token(
    issuer: str = "https://login.kiwix.org",
    client_id: str = "d87a31d2-874e-44c4-9dc2-63fad523bf1b",
    subject: str | None = None,
    exp_delta: datetime.timedelta = datetime.timedelta(hours=1),
) -> str:
    """Create a test JWT token with the given parameters."""
    if subject is None:
        subject = str(UUID(int=0))

    now = getnow()
    payload = {
        "iss": issuer,
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + exp_delta).timestamp()),
    }
    payload["client_id"] = client_id

    # Create a test token (unsigned for testing purposes)
    return jwt.encode(payload, "test-secret", algorithm="HS256")


def create_test_session_jwt_token(
    issuer: str = "https://login.kiwix.org",
    audience_id: str = "d87a31d2-874e-44c4-9dc2-63fad523bf1b",
    subject: str | None = None,
    exp_delta: datetime.timedelta = datetime.timedelta(hours=1),
    aal: str = "aal2",
) -> str:
    """Create a test JWT token for session authentication."""
    if subject is None:
        subject = str(UUID(int=0))

    now = getnow()
    payload = {
        "iss": issuer,
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + exp_delta).timestamp()),
        "aud": audience_id,
        "aal": aal,
        "name": "Test User",
    }

    # Create a test token (unsigned for testing purposes)
    return jwt.encode(payload, "test-secret", algorithm="HS256")


def test_verify_oidc_access_token_expired_token(
    monkeypatch: pytest.MonkeyPatch,
):
    """Test that expired tokens raise ValueError."""
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_ISSUER", "https://login.kiwix.org"
    )
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_OIDC_CLIENT_ID",
        "d87a31d2-874e-44c4-9dc2-63fad523bf1b",
    )

    test_token = create_test_jwt_token()

    mock_signing_key = MagicMock()
    mock_signing_key.key = "test-key"

    decoder = OAuthOIDCTokenDecoder()

    with (
        patch.object(
            decoder._jwks_client,
            "get_signing_key_from_jwt",
        ) as mock_get_key,
        patch("zimfarm_backend.api.token.jwt.decode") as mock_decode,
    ):
        mock_get_key.return_value = mock_signing_key
        mock_decode.side_effect = jwt.ExpiredSignatureError("Token has expired")

        with pytest.raises(jwt.ExpiredSignatureError, match="Token has expired"):
            decoder.decode(test_token)


def test_verify_oidc_access_token_with_2fa_enabled_and_valid_amr(
    monkeypatch: pytest.MonkeyPatch,
):
    """Test successful verification when 2FA is enabled and user has both factors."""
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_ISSUER", "https://login.kiwix.org"
    )
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_OIDC_CLIENT_ID",
        "d87a31d2-874e-44c4-9dc2-63fad523bf1b",
    )
    monkeypatch.setattr("zimfarm_backend.api.token.OAUTH_OIDC_LOGIN_REQUIRE_2FA", True)

    test_token = create_test_jwt_token()

    # Mock the PyJWKClient and jwt.decode
    mock_signing_key = MagicMock()
    mock_signing_key.key = "test-key"

    decoded_payload = {
        "iss": "https://login.kiwix.org",
        "sub": str(UUID(int=0)),
        "aud": "d87a31d2-874e-44c4-9dc2-63fad523bf1b",
        "name": "Test User",
        "iat": int(getnow().timestamp()),
        "exp": int((getnow() + datetime.timedelta(hours=1)).timestamp()),
        "amr": ["password", "totp"],  # Both first and second factor
    }

    decoder = OAuthOIDCTokenDecoder()

    with (
        patch.object(
            decoder._jwks_client,
            "get_signing_key_from_jwt",
        ) as mock_get_key,
        patch("zimfarm_backend.api.token.jwt.decode") as mock_decode,
    ):
        mock_get_key.return_value = mock_signing_key
        mock_decode.return_value = decoded_payload

        result = decoder.decode(test_token)

        assert result.iss == decoded_payload["iss"]
        assert str(result.sub) == decoded_payload["sub"]
        assert result.name == decoded_payload["name"]


def test_verify_oidc_access_token_with_2fa_enabled_only_first_factor(
    monkeypatch: pytest.MonkeyPatch,
):
    """Test verification fails when 2FA is enabled but only first factor is present."""
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_ISSUER", "https://login.kiwix.org"
    )
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_OIDC_CLIENT_ID",
        "d87a31d2-874e-44c4-9dc2-63fad523bf1b",
    )
    monkeypatch.setattr("zimfarm_backend.api.token.OAUTH_OIDC_LOGIN_REQUIRE_2FA", True)

    test_token = create_test_jwt_token()

    mock_signing_key = MagicMock()
    mock_signing_key.key = "test-key"

    decoded_payload = {
        "iss": "https://login.kiwix.org",
        "sub": str(UUID(int=0)),
        "aud": "d87a31d2-874e-44c4-9dc2-63fad523bf1b",
        "name": "Test User",
        "iat": int(getnow().timestamp()),
        "exp": int((getnow() + datetime.timedelta(hours=1)).timestamp()),
        "amr": ["password"],  # Only first factor
    }

    decoder = OAuthOIDCTokenDecoder()

    with (
        patch.object(
            decoder._jwks_client,
            "get_signing_key_from_jwt",
        ) as mock_get_key,
        patch("zimfarm_backend.api.token.jwt.decode") as mock_decode,
    ):
        mock_get_key.return_value = mock_signing_key
        mock_decode.return_value = decoded_payload

        with pytest.raises(
            ValueError, match="2FA authentication is mandatory on Zimfarm"
        ):
            decoder.decode(test_token)


def test_verify_kiwix_access_token_with_2fa_disabled_only_first_factor(
    monkeypatch: pytest.MonkeyPatch,
):
    """
    Test that verification succeeds when 2FA is disabled even with only first factor
    """
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_ISSUER", "https://login.kiwix.org"
    )
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_OIDC_CLIENT_ID",
        "d87a31d2-874e-44c4-9dc2-63fad523bf1b",
    )
    monkeypatch.setattr("zimfarm_backend.api.token.OAUTH_OIDC_LOGIN_REQUIRE_2FA", False)

    test_token = create_test_jwt_token()

    mock_signing_key = MagicMock()
    mock_signing_key.key = "test-key"

    decoded_payload = {
        "iss": "https://login.kiwix.org",
        "sub": str(UUID(int=0)),
        "aud": "d87a31d2-874e-44c4-9dc2-63fad523bf1b",
        "name": "Test User",
        "iat": int(getnow().timestamp()),
        "exp": int((getnow() + datetime.timedelta(hours=1)).timestamp()),
        "amr": ["password"],  # Only first factor, but 2FA is disabled
    }

    decoder = OAuthOIDCTokenDecoder()

    with (
        patch.object(
            decoder._jwks_client,
            "get_signing_key_from_jwt",
        ) as mock_get_key,
        patch("zimfarm_backend.api.token.jwt.decode") as mock_decode,
    ):
        mock_get_key.return_value = mock_signing_key
        mock_decode.return_value = decoded_payload

        result = decoder.decode(test_token)

        # The decoder returns a JWTClaims object, not the raw payload
        assert result.iss == decoded_payload["iss"]
        assert str(result.sub) == decoded_payload["sub"]
        assert result.name == decoded_payload["name"]


def test_verify_session_access_token_expired_token(
    monkeypatch: pytest.MonkeyPatch,
):
    """Test that expired session tokens raise ValueError."""
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_ISSUER", "https://login.kiwix.org"
    )
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_SESSION_AUDIENCE_ID",
        "d87a31d2-874e-44c4-9dc2-63fad523bf1b",
    )

    test_token = create_test_session_jwt_token()

    mock_signing_key = MagicMock()
    mock_signing_key.key = "test-key"

    decoder = OAuthSessionTokenDecoder()

    with (
        patch.object(
            decoder._jwks_client,
            "get_signing_key_from_jwt",
        ) as mock_get_key,
        patch("zimfarm_backend.api.token.jwt.decode") as mock_decode,
    ):
        mock_get_key.return_value = mock_signing_key
        mock_decode.side_effect = jwt.ExpiredSignatureError("Token has expired")

        with pytest.raises(jwt.ExpiredSignatureError, match="Token has expired"):
            decoder.decode(test_token)


def test_verify_session_access_token_with_2fa_enabled_and_valid_aal(
    monkeypatch: pytest.MonkeyPatch,
):
    """Test successful verification when 2FA is enabled and user has aal2."""
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_ISSUER", "https://login.kiwix.org"
    )
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_SESSION_AUDIENCE_ID",
        "d87a31d2-874e-44c4-9dc2-63fad523bf1b",
    )
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_SESSION_LOGIN_REQUIRE_2FA", True
    )

    test_token = create_test_session_jwt_token(aal="aal2")

    # Mock the PyJWKClient and jwt.decode
    mock_signing_key = MagicMock()
    mock_signing_key.key = "test-key"

    decoded_payload = {
        "iss": "https://login.kiwix.org",
        "sub": str(UUID(int=0)),
        "aud": "d87a31d2-874e-44c4-9dc2-63fad523bf1b",
        "name": "Test User",
        "iat": int(getnow().timestamp()),
        "exp": int((getnow() + datetime.timedelta(hours=1)).timestamp()),
        "aal": "aal2",  # Authenticator Assurance Level 2 (2FA)
    }

    decoder = OAuthSessionTokenDecoder()

    with (
        patch.object(
            decoder._jwks_client,
            "get_signing_key_from_jwt",
        ) as mock_get_key,
        patch("zimfarm_backend.api.token.jwt.decode") as mock_decode,
    ):
        mock_get_key.return_value = mock_signing_key
        mock_decode.return_value = decoded_payload

        result = decoder.decode(test_token)

        assert result.iss == decoded_payload["iss"]
        assert str(result.sub) == decoded_payload["sub"]
        assert result.name == decoded_payload["name"]


def test_verify_session_access_token_with_2fa_enabled_only_aal1(
    monkeypatch: pytest.MonkeyPatch,
):
    """Test verification fails when 2FA is enabled but only aal1 is present."""
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_ISSUER", "https://login.kiwix.org"
    )
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_SESSION_AUDIENCE_ID",
        "d87a31d2-874e-44c4-9dc2-63fad523bf1b",
    )
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_SESSION_LOGIN_REQUIRE_2FA", True
    )

    test_token = create_test_session_jwt_token(aal="aal1")

    mock_signing_key = MagicMock()
    mock_signing_key.key = "test-key"

    decoded_payload = {
        "iss": "https://login.kiwix.org",
        "sub": str(UUID(int=0)),
        "aud": "d87a31d2-874e-44c4-9dc2-63fad523bf1b",
        "name": "Test User",
        "iat": int(getnow().timestamp()),
        "exp": int((getnow() + datetime.timedelta(hours=1)).timestamp()),
        "aal": "aal1",  # Only first factor (aal1)
    }

    decoder = OAuthSessionTokenDecoder()

    with (
        patch.object(
            decoder._jwks_client,
            "get_signing_key_from_jwt",
        ) as mock_get_key,
        patch("zimfarm_backend.api.token.jwt.decode") as mock_decode,
    ):
        mock_get_key.return_value = mock_signing_key
        mock_decode.return_value = decoded_payload

        with pytest.raises(
            ValueError, match="2FA authentication is mandatory on Zimfarm"
        ):
            decoder.decode(test_token)


def test_verify_session_access_token_with_2fa_disabled_only_aal1(
    monkeypatch: pytest.MonkeyPatch,
):
    """
    Test that verification succeeds when 2FA is disabled even with only aal1
    """
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_ISSUER", "https://login.kiwix.org"
    )
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_SESSION_AUDIENCE_ID",
        "d87a31d2-874e-44c4-9dc2-63fad523bf1b",
    )
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_SESSION_LOGIN_REQUIRE_2FA", False
    )

    test_token = create_test_session_jwt_token(aal="aal1")

    mock_signing_key = MagicMock()
    mock_signing_key.key = "test-key"

    decoded_payload = {
        "iss": "https://login.kiwix.org",
        "sub": str(UUID(int=0)),
        "aud": "d87a31d2-874e-44c4-9dc2-63fad523bf1b",
        "name": "Test User",
        "iat": int(getnow().timestamp()),
        "exp": int((getnow() + datetime.timedelta(hours=1)).timestamp()),
        "aal": "aal1",  # Only first factor (aal1), but 2FA is disabled
    }

    decoder = OAuthSessionTokenDecoder()

    with (
        patch.object(
            decoder._jwks_client,
            "get_signing_key_from_jwt",
        ) as mock_get_key,
        patch("zimfarm_backend.api.token.jwt.decode") as mock_decode,
    ):
        mock_get_key.return_value = mock_signing_key
        mock_decode.return_value = decoded_payload

        result = decoder.decode(test_token)

        # The decoder returns a JWTClaims object, not the raw payload
        assert result.iss == decoded_payload["iss"]
        assert str(result.sub) == decoded_payload["sub"]
        assert result.name == decoded_payload["name"]
