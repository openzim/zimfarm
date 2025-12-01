import datetime
from unittest.mock import MagicMock, patch
from uuid import UUID

import jwt
import pytest

from zimfarm_backend.api import token as token_module
from zimfarm_backend.api.token import verify_kiwix_access_token
from zimfarm_backend.common import getnow


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


def test_verify_kiwix_access_token_success(
    monkeypatch: pytest.MonkeyPatch,
):
    """Test successful verification of a valid Kiwix access token."""
    monkeypatch.setattr(token_module, "KIWIX_ISSUER", "https://login.kiwix.org")
    monkeypatch.setattr(
        token_module, "KIWIX_CLIENT_ID", "d87a31d2-874e-44c4-9dc2-63fad523bf1b"
    )

    test_token = create_test_jwt_token()

    # Mock the PyJWKClient and jwt.decode
    mock_signing_key = MagicMock()
    mock_signing_key.key = "test-key"

    decoded_payload = {
        "iss": "https://login.kiwix.org",
        "sub": str(UUID(int=0)),
        "client_id": "d87a31d2-874e-44c4-9dc2-63fad523bf1b",
        "iat": int(getnow().timestamp()),
        "exp": int((getnow() + datetime.timedelta(hours=1)).timestamp()),
    }

    with (
        patch.object(
            token_module._jwks_client,  # pyright: ignore[reportPrivateUsage]
            "get_signing_key_from_jwt",
        ) as mock_get_key,
        patch("zimfarm_backend.api.token.jwt.decode") as mock_decode,
    ):
        mock_get_key.return_value = mock_signing_key
        mock_decode.return_value = decoded_payload

        result = verify_kiwix_access_token(test_token)

        assert result == decoded_payload
        assert result["iss"] == "https://login.kiwix.org"
        assert result["client_id"] == "d87a31d2-874e-44c4-9dc2-63fad523bf1b"
        mock_get_key.assert_called_once_with(test_token)
        mock_decode.assert_called_once()


def test_verify_kiwix_access_token_expired_token(
    monkeypatch: pytest.MonkeyPatch,
):
    """Test that expired tokens raise ValueError."""
    monkeypatch.setattr(token_module, "KIWIX_ISSUER", "https://login.kiwix.org")
    monkeypatch.setattr(
        token_module, "KIWIX_CLIENT_ID", "d87a31d2-874e-44c4-9dc2-63fad523bf1b"
    )

    test_token = create_test_jwt_token()

    mock_signing_key = MagicMock()
    mock_signing_key.key = "test-key"

    with (
        patch.object(
            token_module._jwks_client,  # pyright: ignore[reportPrivateUsage]
            "get_signing_key_from_jwt",
        ) as mock_get_key,
        patch("zimfarm_backend.api.token.jwt.decode") as mock_decode,
    ):
        mock_get_key.return_value = mock_signing_key
        mock_decode.side_effect = jwt.ExpiredSignatureError("Token has expired")

        with pytest.raises(jwt.ExpiredSignatureError, match="Token has expired"):
            verify_kiwix_access_token(test_token)
