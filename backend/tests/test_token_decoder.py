# pyright: strict, reportPrivateUsage=false
# ruff: noqa: ARG005
import base64
import datetime
from collections.abc import Callable
from typing import Any
from unittest.mock import patch
from uuid import UUID, uuid4

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.api.token import (
    JWTClaims,
    LocalTokenDecoder,
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
TEST_AUDIENCE = "04e22317-4036-4b6c-9d27-a14c607dce08"


def create_test_jwt(
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


def get_test_session_jwt_payload(
    issuer: str = TEST_ISSUER,
    audience: str = TEST_AUDIENCE,
    subject: str | None = None,
    exp_delta: datetime.timedelta = datetime.timedelta(hours=1),
    aal: str | None = "aal2",
    name: str | None = "Test Account",
    client_id: str | None = None,
) -> dict[str, Any]:
    """Create a test JWT token for session authentication."""
    if subject is None:
        subject = str(UUID(int=0))

    now = getnow()
    payload: dict[str, Any] = {
        "iss": issuer,
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + exp_delta).timestamp()),
        "aud": [audience],
    }
    if name:
        payload["name"] = name
    if client_id:
        payload["client_id"] = client_id
    if aal:
        payload["aal"] = aal

    return payload


def get_test_oidc_jwt_payload(
    issuer: str = TEST_ISSUER,
    audience: str = TEST_AUDIENCE,
    client_id: str = TEST_CLIENT_ID,
    subject: str | None = None,
    exp_delta: datetime.timedelta = datetime.timedelta(hours=1),
    aal: str | None = "aal2",
    name: str | None = "Test Account",
) -> dict[str, Any]:

    if subject is None:
        subject = str(UUID(int=0))

    now = getnow()

    payload: dict[str, Any] = {
        "iss": issuer,
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + exp_delta).timestamp()),
        "aud": [audience],
        "client_id": client_id,
        "ext": {},
    }
    if name:
        # we are dealing with a human, it has an scp claim and kiwix-name ext claim
        payload["ext"]["kiwix-name"] = name
        payload["scp"] = ["openid", "offline"]
    if aal:
        payload["ext"]["kiwix-aal"] = aal

    return payload


def create_jwt_from_payload(payload: dict[str, Any]) -> str:
    """Create a test JWT token from payload."""
    # Create a test token (unsigned for testing purposes)
    return jwt.encode(payload, "test-secret", algorithm="HS256")


def test_verify_oidc_jwt_expired():
    """Test that expired tokens raise ValueError."""

    test_token = create_jwt_from_payload(get_test_oidc_jwt_payload())
    decoder = OAuthOIDCTokenDecoder()

    with (
        patch.object(decoder._jwks_client, "get_signing_key_from_jwt"),
        patch("zimfarm_backend.api.token.jwt.decode") as mock_decode,
    ):
        mock_decode.side_effect = jwt.ExpiredSignatureError("Token has expired")

        with pytest.raises(jwt.ExpiredSignatureError, match="Token has expired"):
            decoder.decode(test_token)


def test_verify_oidc_jwt_with_2fa_enabled_and_two_factors(
    monkeypatch: pytest.MonkeyPatch,
):
    """Test successful verification when 2FA is enabled and account has both factors."""
    monkeypatch.setattr("zimfarm_backend.api.token.OAUTH_OIDC_LOGIN_REQUIRE_2FA", True)

    test_payload = get_test_oidc_jwt_payload()
    test_token = create_jwt_from_payload(test_payload)

    decoder = OAuthOIDCTokenDecoder()

    with (
        patch.object(decoder._jwks_client, "get_signing_key_from_jwt"),
        patch("zimfarm_backend.api.token.jwt.decode") as mock_decode,
    ):
        mock_decode.return_value = test_payload

        result = decoder.decode(test_token)

        assert result.iss == test_payload["iss"]
        assert str(result.sub) == test_payload["sub"]
        assert result.name == test_payload["ext"]["kiwix-name"]


def test_verify_oidc_jwt_with_2fa_enabled_and_only_first_factor(
    monkeypatch: pytest.MonkeyPatch,
):
    """Test verification fails when 2FA is enabled but only first factor is present."""
    monkeypatch.setattr("zimfarm_backend.api.token.OAUTH_OIDC_LOGIN_REQUIRE_2FA", True)

    test_token = create_test_jwt()

    test_payload = get_test_oidc_jwt_payload(aal="aal1")
    test_token = create_jwt_from_payload(test_payload)
    decoder = OAuthOIDCTokenDecoder()

    with (
        patch.object(decoder._jwks_client, "get_signing_key_from_jwt"),
        patch("zimfarm_backend.api.token.jwt.decode") as mock_decode,
    ):
        mock_decode.return_value = test_payload

        with pytest.raises(
            ValueError, match="2FA authentication is mandatory on Zimfarm"
        ):
            decoder.decode(test_token)


def test_verify_oidc_jwt_with_2fa_enabled_and_missing_aal(
    monkeypatch: pytest.MonkeyPatch,
):
    """Test verification fails when 2FA is enabled but aal info is missing."""
    monkeypatch.setattr("zimfarm_backend.api.token.OAUTH_OIDC_LOGIN_REQUIRE_2FA", True)

    test_token = create_test_jwt()

    test_payload = get_test_oidc_jwt_payload(aal=None)
    test_token = create_jwt_from_payload(test_payload)

    decoder = OAuthOIDCTokenDecoder()

    with (
        patch.object(decoder._jwks_client, "get_signing_key_from_jwt"),
        patch("zimfarm_backend.api.token.jwt.decode") as mock_decode,
    ):
        mock_decode.return_value = test_payload

        with pytest.raises(
            ValueError, match="2FA authentication is mandatory on Zimfarm"
        ):
            decoder.decode(test_token)


def test_verify_oidc_jwt_with_2fa_disabled_and_only_first_factor(
    monkeypatch: pytest.MonkeyPatch,
):
    """
    Test that verification succeeds when 2FA is disabled even with only first factor
    """
    monkeypatch.setattr("zimfarm_backend.api.token.OAUTH_OIDC_LOGIN_REQUIRE_2FA", False)

    test_payload = get_test_oidc_jwt_payload(aal="aal1")
    test_token = create_jwt_from_payload(test_payload)

    decoder = OAuthOIDCTokenDecoder()

    with (
        patch.object(decoder._jwks_client, "get_signing_key_from_jwt"),
        patch("zimfarm_backend.api.token.jwt.decode") as mock_decode,
    ):
        mock_decode.return_value = test_payload

        result = decoder.decode(test_token)

        assert result.iss == test_payload["iss"]
        assert str(result.sub) == test_payload["sub"]
        assert result.name == test_payload["ext"]["kiwix-name"]


def test_verify_oidc_jwt_with_2fa_disabled_and_missing_aal(
    monkeypatch: pytest.MonkeyPatch,
):
    """
    Test that verification succeeds when 2FA is disabled and aal is missing
    """
    monkeypatch.setattr("zimfarm_backend.api.token.OAUTH_OIDC_LOGIN_REQUIRE_2FA", False)

    test_payload = get_test_oidc_jwt_payload(aal=None)
    test_token = create_jwt_from_payload(test_payload)

    decoder = OAuthOIDCTokenDecoder()

    with (
        patch.object(decoder._jwks_client, "get_signing_key_from_jwt"),
        patch("zimfarm_backend.api.token.jwt.decode") as mock_decode,
    ):
        mock_decode.return_value = test_payload

        result = decoder.decode(test_token)

        assert result.iss == test_payload["iss"]
        assert str(result.sub) == test_payload["sub"]
        assert result.name == test_payload["ext"]["kiwix-name"]


def test_verify_oidc_jwt_from_machine_requires_no_2fa(
    monkeypatch: pytest.MonkeyPatch,
):
    """
    Test that verification succeeds when 2FA is enabled but token comes from a machine
    """
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_SESSION_LOGIN_REQUIRE_2FA", True
    )

    test_payload = get_test_oidc_jwt_payload(
        aal=None, name=None, client_id=TEST_CLIENT_ID, subject=TEST_CLIENT_ID
    )
    test_token = create_jwt_from_payload(test_payload)

    decoder = OAuthSessionTokenDecoder()

    with (
        patch.object(decoder._jwks_client, "get_signing_key_from_jwt"),
        patch("zimfarm_backend.api.token.jwt.decode") as mock_decode,
    ):
        mock_decode.return_value = test_payload

        result = decoder.decode(test_token)

        # The decoder returns a JWTClaims object, not the raw payload
        assert result.iss == test_payload["iss"]
        assert str(result.sub) == test_payload["sub"]
        assert not result.name


def test_verify_oidc_jwt_from_machine_matches_sub(
    monkeypatch: pytest.MonkeyPatch,
):
    """
    Test that verification fails when token comes from a machine and client_id doesn't
    match sub
    """
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_SESSION_LOGIN_REQUIRE_2FA", False
    )

    test_payload = get_test_oidc_jwt_payload(
        aal=None, name=None, client_id=TEST_CLIENT_ID, subject=str(uuid4())
    )
    test_token = create_jwt_from_payload(test_payload)

    decoder = OAuthSessionTokenDecoder()

    with (
        patch.object(decoder._jwks_client, "get_signing_key_from_jwt"),
        patch("zimfarm_backend.api.token.jwt.decode") as mock_decode,
    ):
        mock_decode.return_value = test_payload

        with pytest.raises(
            ValueError,
            match="Oauth client ID does not match sub, while it should for a machine",
        ):
            decoder.decode(test_token)


def test_verify_session_jwt_expired():
    """Test that expired session tokens raise ValueError."""

    test_token = create_jwt_from_payload(get_test_session_jwt_payload())

    decoder = OAuthSessionTokenDecoder()

    with (
        patch.object(decoder._jwks_client, "get_signing_key_from_jwt"),
        patch("zimfarm_backend.api.token.jwt.decode") as mock_decode,
    ):
        mock_decode.side_effect = jwt.ExpiredSignatureError("Token has expired")

        with pytest.raises(jwt.ExpiredSignatureError, match="Token has expired"):
            decoder.decode(test_token)


def test_verify_session_jwt_with_2fa_enabled_and_two_factors(
    monkeypatch: pytest.MonkeyPatch,
):
    """Test successful verification when 2FA is enabled and account has aal2."""
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_SESSION_LOGIN_REQUIRE_2FA",
        True,
    )

    test_payload = get_test_session_jwt_payload()
    test_token = create_jwt_from_payload(test_payload)

    decoder = OAuthSessionTokenDecoder()

    with (
        patch.object(decoder._jwks_client, "get_signing_key_from_jwt"),
        patch("zimfarm_backend.api.token.jwt.decode") as mock_decode,
    ):
        mock_decode.return_value = test_payload

        result = decoder.decode(test_token)

        assert result.iss == test_payload["iss"]
        assert str(result.sub) == test_payload["sub"]
        assert result.name == test_payload["name"]


def test_verify_session_jwt_with_2fa_enabled_and_only_first_factor(
    monkeypatch: pytest.MonkeyPatch,
):
    """Test verification fails when 2FA is enabled but only aal1 is present."""
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_SESSION_LOGIN_REQUIRE_2FA", True
    )

    test_payload = get_test_session_jwt_payload(aal="aal1")
    test_token = create_jwt_from_payload(test_payload)

    decoder = OAuthSessionTokenDecoder()

    with (
        patch.object(decoder._jwks_client, "get_signing_key_from_jwt"),
        patch("zimfarm_backend.api.token.jwt.decode") as mock_decode,
    ):
        mock_decode.return_value = test_payload

        with pytest.raises(
            ValueError, match="2FA authentication is mandatory on Zimfarm"
        ):
            decoder.decode(test_token)


def test_verify_session_jwt_with_2fa_enabled_and_missing_aal(
    monkeypatch: pytest.MonkeyPatch,
):
    """Test verification fails when 2FA is enabled but aal info is missing."""
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_SESSION_LOGIN_REQUIRE_2FA", True
    )

    test_payload = get_test_session_jwt_payload(aal=None)
    test_token = create_jwt_from_payload(test_payload)

    decoder = OAuthSessionTokenDecoder()

    with (
        patch.object(decoder._jwks_client, "get_signing_key_from_jwt"),
        patch("zimfarm_backend.api.token.jwt.decode") as mock_decode,
    ):
        mock_decode.return_value = test_payload

        with pytest.raises(
            ValueError, match="2FA authentication is mandatory on Zimfarm"
        ):
            decoder.decode(test_token)


def test_verify_session_jwt_with_2fa_disabled_and_only_aal1(
    monkeypatch: pytest.MonkeyPatch,
):
    """
    Test that verification succeeds when 2FA is disabled even with only aal1
    """
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_SESSION_LOGIN_REQUIRE_2FA", False
    )

    test_payload = get_test_session_jwt_payload(aal="aal1")
    test_token = create_jwt_from_payload(test_payload)

    decoder = OAuthSessionTokenDecoder()

    with (
        patch.object(decoder._jwks_client, "get_signing_key_from_jwt"),
        patch("zimfarm_backend.api.token.jwt.decode") as mock_decode,
    ):
        mock_decode.return_value = test_payload

        result = decoder.decode(test_token)

        # The decoder returns a JWTClaims object, not the raw payload
        assert result.iss == test_payload["iss"]
        assert str(result.sub) == test_payload["sub"]
        assert result.name == test_payload["name"]


def test_verify_session_jwt_with_2fa_disabled_and_missing_aal(
    monkeypatch: pytest.MonkeyPatch,
):
    """
    Test that verification succeeds when 2FA is disabled even when aal is missing
    """
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_SESSION_LOGIN_REQUIRE_2FA", False
    )

    test_payload = get_test_session_jwt_payload(aal=None)
    test_token = create_jwt_from_payload(test_payload)

    decoder = OAuthSessionTokenDecoder()

    with (
        patch.object(decoder._jwks_client, "get_signing_key_from_jwt"),
        patch("zimfarm_backend.api.token.jwt.decode") as mock_decode,
    ):
        mock_decode.return_value = test_payload

        result = decoder.decode(test_token)

        # The decoder returns a JWTClaims object, not the raw payload
        assert result.iss == test_payload["iss"]
        assert str(result.sub) == test_payload["sub"]
        assert result.name == test_payload["name"]


def test_verify_session_jwt_from_machine_requires_no_2fa(
    monkeypatch: pytest.MonkeyPatch,
):
    """
    Test that verification succeeds when 2FA is enabled but token comes from a machine
    """
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_SESSION_LOGIN_REQUIRE_2FA", True
    )

    test_payload = get_test_session_jwt_payload(
        aal=None, name=None, client_id=TEST_CLIENT_ID, subject=TEST_CLIENT_ID
    )
    test_token = create_jwt_from_payload(test_payload)

    decoder = OAuthSessionTokenDecoder()

    with (
        patch.object(decoder._jwks_client, "get_signing_key_from_jwt"),
        patch("zimfarm_backend.api.token.jwt.decode") as mock_decode,
    ):
        mock_decode.return_value = test_payload

        result = decoder.decode(test_token)

        # The decoder returns a JWTClaims object, not the raw payload
        assert result.iss == test_payload["iss"]
        assert str(result.sub) == test_payload["sub"]
        assert not result.name


def test_verify_session_jwt_from_machine_matches_sub(
    monkeypatch: pytest.MonkeyPatch,
):
    """
    Test that verification fails when token comes from a machine and client_id doesn't
    match sub
    """
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_SESSION_LOGIN_REQUIRE_2FA", False
    )

    test_payload = get_test_session_jwt_payload(
        aal=None, name=None, client_id=TEST_CLIENT_ID, subject=str(uuid4())
    )
    test_token = create_jwt_from_payload(test_payload)

    decoder = OAuthSessionTokenDecoder()

    with (
        patch.object(decoder._jwks_client, "get_signing_key_from_jwt"),
        patch("zimfarm_backend.api.token.jwt.decode") as mock_decode,
    ):
        mock_decode.return_value = test_payload

        with pytest.raises(
            ValueError,
            match="Oauth client ID does not match sub, while it should for a machine",
        ):
            decoder.decode(test_token)


def test_ssh_token_decoder_can_decode_valid_format(
    account: Account,
    rsa_private_key: RSAPrivateKey,
    create_worker: Callable[..., Worker],
):
    """Test SSH token decoder can_decode with valid token format."""
    worker = create_worker(account=account)
    datetime_str = (getnow() + datetime.timedelta(minutes=5)).isoformat()
    message_to_sign = f"{worker.name}.{datetime_str}"
    signature = sign_message_with_rsa_key(
        rsa_private_key, bytes(message_to_sign, encoding="ascii")
    )
    b64_signature = base64.b64encode(signature).decode()
    token = f"{worker.name}.{datetime_str}.{b64_signature}"

    decoder = SshTokenDecoder()
    assert decoder.can_decode(token) is True


@pytest.mark.parametrize(
    "token",
    [
        pytest.param("worker.timestamp", id="invalid-format"),
        pytest.param("worker.not-a-timestamp.signature", id="invalid-timestamp"),
        pytest.param(
            "worker.2026-04-14T11:03:03:not-valid-base64-!@#", id="invalid-base64"
        ),
        pytest.param("random-string", id="random-string"),
    ],
)
def test_ssh_token_decoder_can_decode_invalid_format(token: str):
    """Test SSH token decoder can_decode with invalid token formats."""
    decoder = SshTokenDecoder()
    assert decoder.can_decode(token) is False


def test_local_token_decoder_can_decode_with_auth_mode_disabled(
    monkeypatch: pytest.MonkeyPatch,
):
    """Test local token decoder can_decode returns False when auth mode disabled."""
    monkeypatch.setattr("zimfarm_backend.api.token.AUTH_MODES", ["oauth-oidc"])

    decoder = LocalTokenDecoder()
    token = create_test_jwt(issuer="zimfarm_backend")
    assert decoder.can_decode(token) is False


def test_local_token_decoder_can_decode_with_correct_issuer(
    monkeypatch: pytest.MonkeyPatch,
):
    """Test local token decoder can_decode with correct issuer."""
    monkeypatch.setattr("zimfarm_backend.api.token.AUTH_MODES", ["local"])
    monkeypatch.setattr("zimfarm_backend.api.token.JWT_TOKEN_ISSUER", "zimfarm_backend")

    decoder = LocalTokenDecoder()
    token = create_test_jwt(issuer="zimfarm_backend")
    assert decoder.can_decode(token) is True


def test_local_token_decoder_can_decode_with_wrong_issuer(
    monkeypatch: pytest.MonkeyPatch,
):
    """Test local token decoder can_decode with wrong issuer."""
    monkeypatch.setattr("zimfarm_backend.api.token.AUTH_MODES", ["local"])
    monkeypatch.setattr("zimfarm_backend.api.token.JWT_TOKEN_ISSUER", "zimfarm_backend")

    decoder = LocalTokenDecoder()
    token = create_test_jwt(issuer="wrong-issuer")
    assert decoder.can_decode(token) is False


def test_oauth_oidc_token_decoder_can_decode_with_auth_mode_disabled(
    monkeypatch: pytest.MonkeyPatch,
):
    """Test OAuth OIDC can_decode returns False when disabled."""
    monkeypatch.setattr("zimfarm_backend.api.token.AUTH_MODES", ["local"])

    decoder = OAuthOIDCTokenDecoder()
    token = create_test_jwt()
    assert decoder.can_decode(token) is False


def test_oauth_oidc_token_decoder_can_decode_with_correct_issuer_and_audience(
    monkeypatch: pytest.MonkeyPatch,
):
    """Test OAuth OIDC token decoder can_decode with correct issuer and audience."""
    monkeypatch.setattr("zimfarm_backend.api.token.AUTH_MODES", ["oauth-oidc"])
    monkeypatch.setattr("zimfarm_backend.api.token.OAUTH_ISSUER", TEST_ISSUER)
    monkeypatch.setattr("zimfarm_backend.api.token.OAUTH_OIDC_AUDIENCE", TEST_AUDIENCE)

    decoder = OAuthOIDCTokenDecoder()

    token = create_jwt_from_payload(get_test_oidc_jwt_payload())
    assert decoder.can_decode(token) is True


def test_oauth_oidc_token_decoder_can_decode_with_wrong_issuer(
    monkeypatch: pytest.MonkeyPatch,
):
    """Test OAuth OIDC token decoder can_decode with wrong issuer."""
    monkeypatch.setattr("zimfarm_backend.api.token.AUTH_MODES", ["oauth-oidc"])
    monkeypatch.setattr("zimfarm_backend.api.token.OAUTH_ISSUER", TEST_ISSUER)
    monkeypatch.setattr("zimfarm_backend.api.token.OAUTH_OIDC_AUDIENCE", TEST_AUDIENCE)

    decoder = OAuthOIDCTokenDecoder()

    token = create_jwt_from_payload(get_test_oidc_jwt_payload(issuer="wrong-issuer"))
    assert decoder.can_decode(token) is False


def test_oauth_oidc_token_decoder_can_decode_with_wrong_audience(
    monkeypatch: pytest.MonkeyPatch,
):
    """Test OAuth OIDC token decoder can_decode with wrong audience."""
    monkeypatch.setattr("zimfarm_backend.api.token.AUTH_MODES", ["oauth-oidc"])
    monkeypatch.setattr("zimfarm_backend.api.token.OAUTH_ISSUER", TEST_ISSUER)
    monkeypatch.setattr("zimfarm_backend.api.token.OAUTH_OIDC_AUDIENCE", TEST_AUDIENCE)

    decoder = OAuthOIDCTokenDecoder()
    token = create_jwt_from_payload(
        get_test_oidc_jwt_payload(audience="wrong-audience")
    )

    assert decoder.can_decode(token) is False


def test_oauth_session_token_decoder_can_decode_with_auth_mode_disabled(
    monkeypatch: pytest.MonkeyPatch,
):
    """Test OAuth Session can_decode returns False when disabled."""
    monkeypatch.setattr("zimfarm_backend.api.token.AUTH_MODES", ["local"])

    decoder = OAuthSessionTokenDecoder()
    token = create_jwt_from_payload(get_test_session_jwt_payload())
    assert decoder.can_decode(token) is False


def test_oauth_session_token_decoder_can_decode_with_correct_issuer_and_audience(
    monkeypatch: pytest.MonkeyPatch,
):
    """Test OAuth Session token decoder can_decode with correct issuer and audience."""
    monkeypatch.setattr("zimfarm_backend.api.token.AUTH_MODES", ["oauth-session"])
    monkeypatch.setattr("zimfarm_backend.api.token.OAUTH_ISSUER", TEST_ISSUER)
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_SESSION_AUDIENCE", TEST_AUDIENCE
    )

    decoder = OAuthSessionTokenDecoder()
    token = create_jwt_from_payload(get_test_session_jwt_payload())
    assert decoder.can_decode(token) is True


def test_oauth_session_token_decoder_can_decode_with_wrong_issuer(
    monkeypatch: pytest.MonkeyPatch,
):
    """Test OAuth Session token decoder can_decode with wrong issuer."""
    monkeypatch.setattr("zimfarm_backend.api.token.AUTH_MODES", ["oauth-session"])
    monkeypatch.setattr("zimfarm_backend.api.token.OAUTH_ISSUER", TEST_ISSUER)
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_SESSION_AUDIENCE", TEST_AUDIENCE
    )

    decoder = OAuthSessionTokenDecoder()
    token = create_jwt_from_payload(get_test_session_jwt_payload(issuer="wrong-issuer"))
    assert decoder.can_decode(token) is False


def test_oauth_session_token_decoder_can_decode_with_wrong_audience(
    monkeypatch: pytest.MonkeyPatch,
):
    """Test OAuth Session token decoder can_decode with wrong audience."""
    monkeypatch.setattr("zimfarm_backend.api.token.AUTH_MODES", ["oauth-session"])
    monkeypatch.setattr("zimfarm_backend.api.token.OAUTH_ISSUER", TEST_AUDIENCE)
    monkeypatch.setattr(
        "zimfarm_backend.api.token.OAUTH_SESSION_AUDIENCE", TEST_AUDIENCE
    )

    decoder = OAuthSessionTokenDecoder()
    token = create_jwt_from_payload(
        get_test_session_jwt_payload(audience="wrong-audience")
    )
    assert decoder.can_decode(token) is False


@pytest.mark.parametrize(
    ["datetime_str", "message_modifier", "expected_exception", "exception_msg"],
    [
        pytest.param(
            datetime.datetime.fromtimestamp(0, tz=datetime.UTC)
            .replace(tzinfo=None)
            .isoformat(timespec="seconds"),
            lambda w, t, s: f"{w}.{t}.{s}",  # pyright: ignore[reportUnknownArgumentType, reportUnknownLambdaType]
            ValueError,
            "Difference between message time and server time is greater than",
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
        ValueError, match=r"OrmSession is required to decode SSH bearer tokens."
    ):
        decoder.decode(token)
