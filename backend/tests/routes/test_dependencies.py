import uuid
from collections.abc import Callable
from unittest.mock import MagicMock, patch

import pytest
from fastapi.security import HTTPAuthorizationCredentials
from ory_client.models.introspected_o_auth2_token import IntrospectedOAuth2Token

from zimfarm_backend.api import token as token_module
from zimfarm_backend.api.routes.dependencies import get_jwt_claims_or_none
from zimfarm_backend.api.routes.http_errors import UnauthorizedError
from zimfarm_backend.api.token import generate_access_token
from zimfarm_backend.common import getnow


@pytest.fixture
def create_mock_authorization() -> Callable[..., HTTPAuthorizationCredentials]:
    """Create a mock HTTPAuthorizationCredentials object."""

    def _create_auth(token: str) -> HTTPAuthorizationCredentials:
        return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    return _create_auth


def test_get_jwt_claims_or_none_with_no_authorization():
    """Test that None is returned when no authorization is provided."""
    result = get_jwt_claims_or_none(None)
    assert result is None


def test_get_jwt_claims_or_none_with_valid_zimfarm_token(
    create_mock_authorization: Callable[..., HTTPAuthorizationCredentials],
):
    """Test successful JWT claims extraction from a valid Zimfarm token."""
    user_id = str(uuid.uuid4())
    now = getnow()
    access_token = generate_access_token(issue_time=now, user_id=user_id)

    auth = create_mock_authorization(access_token)
    claims = get_jwt_claims_or_none(auth)

    assert claims is not None
    assert claims.sub == uuid.UUID(user_id)


def test_get_jwt_claims_or_none_with_valid_kiwix_token(
    monkeypatch: pytest.MonkeyPatch,
    create_mock_authorization: Callable[..., HTTPAuthorizationCredentials],
    valid_introspected_token: IntrospectedOAuth2Token,
):
    """Test successful JWT claims extraction from a valid Kiwix token."""
    monkeypatch.setattr(token_module, "KIWIX_ISSUER", "https://login.kiwix.org")
    monkeypatch.setattr(
        token_module, "KIWIX_CLIENT_ID", "d87a31d2-874e-44c4-9dc2-63fad523bf1b"
    )

    with patch(
        "zimfarm_backend.api.token.OryOAuth2Api.introspect_o_auth2_token"
    ) as mock_introspect:
        mock_introspect.return_value = valid_introspected_token

        auth = create_mock_authorization("kiwix_token_123")
        claims = get_jwt_claims_or_none(auth)

        assert claims is not None
        assert claims.iss == "https://login.kiwix.org"
        assert claims.sub == uuid.UUID(valid_introspected_token.sub)


def test_get_jwt_claims_or_none_with_inactive_kiwix_token(
    monkeypatch: pytest.MonkeyPatch,
    create_mock_authorization: Callable[..., HTTPAuthorizationCredentials],
):
    """Test that inactive Kiwix tokens raise UnauthorizedError."""
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

        auth = create_mock_authorization("inactive_kiwix_token")

        with pytest.raises(UnauthorizedError):
            get_jwt_claims_or_none(auth)
