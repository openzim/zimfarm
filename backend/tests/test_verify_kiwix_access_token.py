from unittest.mock import MagicMock, patch

import pytest
from ory_client.models.introspected_o_auth2_token import IntrospectedOAuth2Token

from zimfarm_backend.api import token as token_module
from zimfarm_backend.api.token import (
    _introspection_token_cache,  # pyright: ignore[reportPrivateUsage]
    verify_kiwix_access_token,
)


def test_verify_kiwix_access_token_success(
    monkeypatch: pytest.MonkeyPatch,
    valid_introspected_token: IntrospectedOAuth2Token,
):
    """Test successful verification of a valid Kiwix access token."""
    monkeypatch.setattr(token_module, "KIWIX_ISSUER", "https://login.kiwix.org")
    monkeypatch.setattr(
        token_module, "KIWIX_CLIENT_ID", "d87a31d2-874e-44c4-9dc2-63fad523bf1b"
    )

    with patch(
        "zimfarm_backend.api.token.OryOAuth2Api.introspect_o_auth2_token"
    ) as mock_introspect:
        mock_introspect.return_value = valid_introspected_token

        result = verify_kiwix_access_token("valid_token")

        assert result == valid_introspected_token
        assert result.active is True
        assert result.iss == "https://login.kiwix.org"
        assert result.client_id == "d87a31d2-874e-44c4-9dc2-63fad523bf1b"
        mock_introspect.assert_called_once_with("valid_token")


def test_verify_kiwix_access_token_uses_cache_on_second_call(
    monkeypatch: pytest.MonkeyPatch,
    valid_introspected_token: IntrospectedOAuth2Token,
):
    """Test that verify_kiwix_access_token uses cache on subsequent calls."""
    monkeypatch.setattr(token_module, "KIWIX_ISSUER", "https://login.kiwix.org")
    monkeypatch.setattr(
        token_module, "KIWIX_CLIENT_ID", "d87a31d2-874e-44c4-9dc2-63fad523bf1b"
    )

    with patch(
        "zimfarm_backend.api.token.OryOAuth2Api.introspect_o_auth2_token"
    ) as mock_introspect:
        mock_introspect.return_value = valid_introspected_token

        # First call - should hit the API
        result1 = verify_kiwix_access_token("cached_token")
        assert mock_introspect.call_count == 1

        # Second call - should use cache
        result2 = verify_kiwix_access_token("cached_token")
        assert mock_introspect.call_count == 1  # Still 1

        assert result1 == result2


def test_verify_kiwix_access_token_inactive_token(
    monkeypatch: pytest.MonkeyPatch,
):
    """Test that inactive tokens raise ValueError."""
    monkeypatch.setattr(token_module, "KIWIX_ISSUER", "https://login.kiwix.org")
    monkeypatch.setattr(
        token_module, "KIWIX_CLIENT_ID", "d87a31d2-874e-44c4-9dc2-63fad523bf1b"
    )

    inactive_token = MagicMock(spec=IntrospectedOAuth2Token)
    inactive_token.active = False

    with patch(
        "zimfarm_backend.api.token.OryOAuth2Api.introspect_o_auth2_token"
    ) as mock_introspect:
        mock_introspect.return_value = inactive_token

        with pytest.raises(ValueError, match="Kiwix access token is not active"):
            verify_kiwix_access_token("inactive_token")


def test_verify_kiwix_access_token_invalid_issuer(
    monkeypatch: pytest.MonkeyPatch,
):
    """Test that tokens with invalid issuer raise ValueError."""
    monkeypatch.setattr(token_module, "KIWIX_ISSUER", "https://login.kiwix.org")
    monkeypatch.setattr(
        token_module, "KIWIX_CLIENT_ID", "d87a31d2-874e-44c4-9dc2-63fad523bf1b"
    )

    invalid_issuer_token = MagicMock(spec=IntrospectedOAuth2Token)
    invalid_issuer_token.active = True
    invalid_issuer_token.iss = "https://wrong-issuer.com"
    invalid_issuer_token.client_id = "d87a31d2-874e-44c4-9dc2-63fad523bf1b"

    with patch(
        "zimfarm_backend.api.token.OryOAuth2Api.introspect_o_auth2_token"
    ) as mock_introspect:
        mock_introspect.return_value = invalid_issuer_token

        with pytest.raises(ValueError, match="Kiwix access token issuer is not valid"):
            verify_kiwix_access_token("invalid_issuer_token")


def test_verify_kiwix_access_token_invalid_client_id(
    monkeypatch: pytest.MonkeyPatch,
):
    """Test that tokens with invalid client_id raise ValueError."""
    monkeypatch.setattr(token_module, "KIWIX_ISSUER", "https://login.kiwix.org")
    monkeypatch.setattr(
        token_module, "KIWIX_CLIENT_ID", "d87a31d2-874e-44c4-9dc2-63fad523bf1b"
    )

    invalid_client_token = MagicMock(spec=IntrospectedOAuth2Token)
    invalid_client_token.active = True
    invalid_client_token.iss = "https://login.kiwix.org"
    invalid_client_token.client_id = "wrong-client-id"

    with patch(
        "zimfarm_backend.api.token.OryOAuth2Api.introspect_o_auth2_token"
    ) as mock_introspect:
        mock_introspect.return_value = invalid_client_token

        with pytest.raises(
            ValueError, match="Kiwix access token client ID is not valid"
        ):
            verify_kiwix_access_token("invalid_client_token")


def test_verify_kiwix_access_token_caches_successful_verification(
    monkeypatch: pytest.MonkeyPatch,
    valid_introspected_token: IntrospectedOAuth2Token,
):
    """Test that successful verifications are cached."""
    monkeypatch.setattr(token_module, "KIWIX_ISSUER", "https://login.kiwix.org")
    monkeypatch.setattr(
        token_module, "KIWIX_CLIENT_ID", "d87a31d2-874e-44c4-9dc2-63fad523bf1b"
    )

    with patch(
        "zimfarm_backend.api.token.OryOAuth2Api.introspect_o_auth2_token"
    ) as mock_introspect:
        mock_introspect.return_value = valid_introspected_token

        # Verify cache is empty
        assert len(_introspection_token_cache) == 0

        # First call should populate cache
        verify_kiwix_access_token("token_to_cache")

        # Verify cache now has the token
        assert len(_introspection_token_cache) == 1


def test_verify_kiwix_access_token_does_not_cache_failures(
    monkeypatch: pytest.MonkeyPatch,
):
    """Test that failed verifications are not cached."""
    monkeypatch.setattr(token_module, "KIWIX_ISSUER", "https://login.kiwix.org")
    monkeypatch.setattr(
        token_module, "KIWIX_CLIENT_ID", "d87a31d2-874e-44c4-9dc2-63fad523bf1b"
    )

    inactive_token = MagicMock(spec=IntrospectedOAuth2Token)
    inactive_token.active = False

    with patch(
        "zimfarm_backend.api.token.OryOAuth2Api.introspect_o_auth2_token"
    ) as mock_introspect:
        mock_introspect.return_value = inactive_token

        # Verify cache is empty
        assert len(_introspection_token_cache) == 0

        # Try to verify - should fail
        with pytest.raises(ValueError):
            verify_kiwix_access_token("inactive_token")

        # Verify cache is still empty
        assert len(_introspection_token_cache) == 0


def test_verify_kiwix_access_token_cache_miss_different_tokens(
    monkeypatch: pytest.MonkeyPatch,
    valid_introspected_token: IntrospectedOAuth2Token,
):
    """Test that different tokens each trigger API calls."""
    monkeypatch.setattr(token_module, "KIWIX_ISSUER", "https://login.kiwix.org")
    monkeypatch.setattr(
        token_module, "KIWIX_CLIENT_ID", "d87a31d2-874e-44c4-9dc2-63fad523bf1b"
    )

    with patch(
        "zimfarm_backend.api.token.OryOAuth2Api.introspect_o_auth2_token"
    ) as mock_introspect:
        mock_introspect.return_value = valid_introspected_token

        # First token
        verify_kiwix_access_token("token1")
        assert mock_introspect.call_count == 1

        # Second different token should trigger another API call
        verify_kiwix_access_token("token2")
        assert mock_introspect.call_count == 2
