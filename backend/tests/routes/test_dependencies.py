import uuid
from collections.abc import Callable

import pytest
from fastapi.security import HTTPAuthorizationCredentials

from zimfarm_backend.api.routes.dependencies import get_jwt_claims_or_none
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
