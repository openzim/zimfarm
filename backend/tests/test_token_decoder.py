# pyright: strict, reportPrivateUsage=false
# ruff: noqa: ARG005
import base64
import datetime
from collections.abc import Callable
from unittest.mock import MagicMock, patch
from uuid import UUID

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.api.token import (
    JWTClaims,
    OAuthOIDCTokenDecoder,
    OAuthSessionTokenDecoder,
    SshTokenDecoder,
)
from zimfarm_backend.common import getnow
from zimfarm_backend.db.models import Account, Worker
from zimfarm_backend.utils.cryptography import sign_message_with_rsa_key

# Authentication method constants for testing
FIRST_FACTOR_METHODS = ["password", "oidc"]
SECOND_FACTOR_METHODS = ["webauthn", "lookup_secrets", "totp"]
TEST_ISSUER = "https://foo.acme.org"
TEST_CLIENT_ID = "d87a31d2-874e-44c4-9dc2-63fad523bf1b"


def create_test_jwt_token(
    issuer: str = TEST_ISSUER,
    client_id: str = TEST_CLIENT_ID,
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
    issuer: str = TEST_ISSUER,
    audience_id: str = TEST_CLIENT_ID,
    subject: str | None = None,
    exp_delta: datetime.timedelta = datetime.timedelta(hours=1),
    aal: str | None = "aal2",
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
        "name": "Test Account",
    }
    if aal:
        payload["aal"] = aal

    # Create a test token (unsigned for testing purposes)
    return jwt.encode(payload, "test-secret", algorithm="HS256")


def test_verify_oidc_access_token_expired_token(
    monkeypatch: pytest.MonkeyPatch,
):
    """Test that expired tokens raise ValueError."""
    monkeypatch.setattr("zimfarm_backend.api.token.OAUTH_ISSUER", TEST_ISSUER)
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_OIDC_CLIENT_ID",
        TEST_CLIENT_ID,
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
    """Test successful verification when 2FA is enabled and account has both factors."""
    monkeypatch.setattr("zimfarm_backend.api.token.OAUTH_ISSUER", TEST_ISSUER)
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_OIDC_CLIENT_ID",
        TEST_CLIENT_ID,
    )
    monkeypatch.setattr("zimfarm_backend.api.token.OAUTH_OIDC_LOGIN_REQUIRE_2FA", True)

    test_token = create_test_jwt_token()

    # Mock the PyJWKClient and jwt.decode
    mock_signing_key = MagicMock()
    mock_signing_key.key = "test-key"

    decoded_payload = {
        "iss": TEST_ISSUER,
        "sub": str(UUID(int=0)),
        "aud": TEST_CLIENT_ID,
        "name": "Test Account",
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
    monkeypatch.setattr("zimfarm_backend.api.token.OAUTH_ISSUER", TEST_ISSUER)
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_OIDC_CLIENT_ID",
        TEST_CLIENT_ID,
    )
    monkeypatch.setattr("zimfarm_backend.api.token.OAUTH_OIDC_LOGIN_REQUIRE_2FA", True)

    test_token = create_test_jwt_token()

    mock_signing_key = MagicMock()
    mock_signing_key.key = "test-key"

    decoded_payload = {
        "iss": TEST_ISSUER,
        "sub": str(UUID(int=0)),
        "aud": TEST_CLIENT_ID,
        "name": "Test Account",
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
    monkeypatch.setattr("zimfarm_backend.api.token.OAUTH_ISSUER", TEST_ISSUER)
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_OIDC_CLIENT_ID",
        TEST_CLIENT_ID,
    )
    monkeypatch.setattr("zimfarm_backend.api.token.OAUTH_OIDC_LOGIN_REQUIRE_2FA", False)

    test_token = create_test_jwt_token()

    mock_signing_key = MagicMock()
    mock_signing_key.key = "test-key"

    decoded_payload = {
        "iss": TEST_ISSUER,
        "sub": str(UUID(int=0)),
        "aud": TEST_CLIENT_ID,
        "name": "Test Account",
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
    monkeypatch.setattr("zimfarm_backend.api.token.OAUTH_ISSUER", TEST_ISSUER)
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_SESSION_AUDIENCE_ID",
        TEST_CLIENT_ID,
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
    """Test successful verification when 2FA is enabled and account has aal2."""
    monkeypatch.setattr("zimfarm_backend.api.token.OAUTH_ISSUER", TEST_ISSUER)
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_SESSION_AUDIENCE_ID",
        TEST_CLIENT_ID,
    )
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_SESSION_LOGIN_REQUIRE_2FA", True
    )

    test_token = create_test_session_jwt_token(aal="aal2")

    # Mock the PyJWKClient and jwt.decode
    mock_signing_key = MagicMock()
    mock_signing_key.key = "test-key"

    decoded_payload = {
        "iss": TEST_ISSUER,
        "sub": str(UUID(int=0)),
        "aud": TEST_CLIENT_ID,
        "name": "Test Account",
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
    monkeypatch.setattr("zimfarm_backend.api.token.OAUTH_ISSUER", TEST_ISSUER)
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_SESSION_AUDIENCE_ID",
        TEST_CLIENT_ID,
    )
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_SESSION_LOGIN_REQUIRE_2FA", True
    )

    test_token = create_test_session_jwt_token(aal="aal1")

    mock_signing_key = MagicMock()
    mock_signing_key.key = "test-key"

    decoded_payload = {
        "iss": TEST_ISSUER,
        "sub": str(UUID(int=0)),
        "aud": TEST_CLIENT_ID,
        "name": "Test Account",
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
    monkeypatch.setattr("zimfarm_backend.api.token.OAUTH_ISSUER", TEST_ISSUER)
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_SESSION_AUDIENCE_ID",
        TEST_CLIENT_ID,
    )
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_SESSION_LOGIN_REQUIRE_2FA", False
    )

    test_token = create_test_session_jwt_token(aal="aal1")

    mock_signing_key = MagicMock()
    mock_signing_key.key = "test-key"

    decoded_payload = {
        "iss": TEST_ISSUER,
        "sub": str(UUID(int=0)),
        "aud": TEST_CLIENT_ID,
        "name": "Test Account",
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


def test_verify_session_access_token_with_client_id_requires_no_2fa(
    monkeypatch: pytest.MonkeyPatch,
):
    """
    Test that verification succeeds when 2FA is enabled but token contains client_id
    """
    monkeypatch.setattr("zimfarm_backend.api.token.OAUTH_ISSUER", TEST_ISSUER)
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_SESSION_AUDIENCE_ID",
        TEST_CLIENT_ID,
    )
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_SESSION_LOGIN_REQUIRE_2FA", True
    )

    test_token = create_test_session_jwt_token(aal=None)

    mock_signing_key = MagicMock()
    mock_signing_key.key = "test-key"
    sub = str(UUID(int=0))

    decoded_payload = {
        "iss": TEST_ISSUER,
        "aud": TEST_CLIENT_ID,
        "sub": sub,
        "client_id": sub,
        "name": "Test Account",
        "iat": int(getnow().timestamp()),
        "exp": int((getnow() + datetime.timedelta(hours=1)).timestamp()),
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


def test_verify_session_access_token_verify_client_id_matches_sub(
    monkeypatch: pytest.MonkeyPatch,
):
    """
    Test that verification succeeds when 2FA is enabled but token contains client_id
    """
    monkeypatch.setattr("zimfarm_backend.api.token.OAUTH_ISSUER", TEST_ISSUER)
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_SESSION_AUDIENCE_ID",
        TEST_CLIENT_ID,
    )
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_SESSION_LOGIN_REQUIRE_2FA", True
    )

    test_token = create_test_session_jwt_token(aal=None)

    mock_signing_key = MagicMock()
    mock_signing_key.key = "test-key"

    decoded_payload = {
        "iss": TEST_ISSUER,
        "aud": TEST_CLIENT_ID,
        "sub": str(UUID(int=0)),
        "client_id": str(UUID(int=1)),
        "name": "Test Account",
        "iat": int(getnow().timestamp()),
        "exp": int((getnow() + datetime.timedelta(hours=1)).timestamp()),
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

        with pytest.raises(ValueError, match="Oauth client ID does not match"):
            decoder.decode(test_token)


@pytest.mark.parametrize(
    ["datetime_str", "message_modifier", "expected_exception", "exception_msg"],
    [
        pytest.param(
            datetime.datetime.fromtimestamp(0, tz=datetime.UTC)
            .replace(tzinfo=None)
            .isoformat(timespec="seconds"),
            lambda w, t, s: f"{w}.{t}.{s}",  # pyright: ignore[reportUnknownArgumentType, reportUnknownLambdaType]
            ValueError,
            "Difference betweeen message time and server time is greater than",
            id="outdated-timestamp",
        ),
        pytest.param(
            (getnow() + datetime.timedelta(minutes=5)).isoformat(timespec="seconds"),
            lambda w, t, s: "hello",  # pyright: ignore[reportUnknownArgumentType, reportUnknownLambdaType]
            ValueError,
            "Invalid message format.",
            id="invalid-message-format",
        ),
        pytest.param(
            (getnow() + datetime.timedelta(minutes=5)).isoformat(timespec="seconds"),
            lambda w, t, s: f"{w}.{t}.not-base64-!@#",  # pyright: ignore[reportUnknownArgumentType, reportUnknownLambdaType]
            ValueError,
            "Invalid signature format.*",
            id="invalid-signature-format",
        ),
        pytest.param(
            (getnow() + datetime.timedelta(minutes=5)).isoformat(timespec="seconds"),
            lambda w, t, s: f"unknownworker.{t}.{s}",  # pyright: ignore[reportUnknownArgumentType, reportUnknownLambdaType]
            ValueError,
            "Worker unknownworker does not exist.",
            id="worker-does-not-exist",
        ),
        pytest.param(
            # Before CI fully sets up, default timer has expired, so, add
            # additional 5 minutes
            (getnow() + datetime.timedelta(minutes=5)).isoformat(timespec="seconds"),
            lambda w, t, s: f"{w}.{t}.{s}",  # pyright: ignore[reportUnknownArgumentType, reportUnknownLambdaType]
            None,
            "",
            id="valid-message",
        ),
    ],
)
def test_ssh_token_decoder(
    account: Account,
    rsa_private_key: RSAPrivateKey,
    datetime_str: str,
    message_modifier: Callable[[str, str, str], str],
    expected_exception: type[Exception] | None,
    exception_msg: str,
    create_worker: Callable[..., Worker],
    dbsession: OrmSession,
):
    worker = create_worker(account=account)

    # signature is created with f"{worker_name}.{timestamp_str}"
    message_to_sign = f"{worker.name}.{datetime_str}"
    signature = sign_message_with_rsa_key(
        rsa_private_key, bytes(message_to_sign, encoding="ascii")
    )
    b64_signature = base64.b64encode(signature).decode()

    token = message_modifier(worker.name, datetime_str, b64_signature)

    decoder = SshTokenDecoder()

    if expected_exception:
        with pytest.raises(expected_exception, match=exception_msg):
            decoder.decode(token, session=dbsession)
    else:
        claims = decoder.decode(token, session=dbsession)
        assert isinstance(claims, JWTClaims)
        assert claims.iss == "zimfarm-worker"
        assert claims.sub == worker.account_id


def test_ssh_token_decoder_no_session(
    account: Account,
    rsa_private_key: RSAPrivateKey,
    create_worker: Callable[..., Worker],
):
    worker = create_worker(account=account)
    datetime_str = (getnow() + datetime.timedelta(minutes=5)).isoformat()
    message_to_sign = f"{worker.name}.{datetime_str}"
    signature = sign_message_with_rsa_key(
        rsa_private_key, bytes(message_to_sign, encoding="ascii")
    )
    b64_signature = base64.b64encode(signature).decode()
    token = f"{worker.name}.{datetime_str}.{b64_signature}"

    decoder = SshTokenDecoder()
    with pytest.raises(
        ValueError, match="OrmSession is required to decode SSH bearer tokens."
    ):
        decoder.decode(token)
