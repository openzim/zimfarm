import datetime
from unittest.mock import MagicMock

import pytest
from ory_client.models.introspected_o_auth2_token import IntrospectedOAuth2Token

from zimfarm_backend.api.token import (
    _cache_introspection_token,  # pyright: ignore[reportPrivateUsage]
    _CachedToken,  # pyright: ignore[reportPrivateUsage]
    _get_cached_introspection_token,  # pyright: ignore[reportPrivateUsage]
    _hash_token,  # pyright: ignore[reportPrivateUsage]
    _introspection_token_cache,  # pyright: ignore[reportPrivateUsage]
    _is_cache_entry_valid,  # pyright: ignore[reportPrivateUsage]
)
from zimfarm_backend.common import getnow


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear the introspection token cache before and after each test."""
    _introspection_token_cache.clear()
    yield
    _introspection_token_cache.clear()


@pytest.fixture
def mock_introspected_token():
    """Create a mock introspected token with future expiration."""
    token = MagicMock(spec=IntrospectedOAuth2Token)
    token.active = True
    token.iss = "https://auth.kiwix.org"
    token.client_id = "test_client_id"
    # Set expiration 1 hour in the future
    token.exp = int((getnow() + datetime.timedelta(hours=1)).timestamp())
    return token


@pytest.fixture
def expired_introspected_token():
    """Create a mock introspected token with past expiration."""
    token = MagicMock(spec=IntrospectedOAuth2Token)
    token.active = True
    token.iss = "https://auth.kiwix.org"
    token.client_id = "test_client_id"
    # Set expiration 1 hour in the past
    token.exp = int((getnow() - datetime.timedelta(hours=1)).timestamp())
    return token


def test_cache_introspection_token_adds_to_cache(
    mock_introspected_token: IntrospectedOAuth2Token,
):
    """Test that caching a token adds it to the cache."""
    token = "test_token"
    assert len(_introspection_token_cache) == 0

    _cache_introspection_token(token, mock_introspected_token)

    assert len(_introspection_token_cache) == 1
    token_hash = _hash_token(token)
    assert token_hash in _introspection_token_cache


def test_cache_introspection_token_stores_correct_data(
    mock_introspected_token: IntrospectedOAuth2Token,
):
    """Test that the cached data contains the correct token and expiration."""
    token = "test_token"
    _cache_introspection_token(token, mock_introspected_token)

    token_hash = _hash_token(token)
    cached = _introspection_token_cache[token_hash]

    assert isinstance(cached, _CachedToken)
    assert cached.introspected_token == mock_introspected_token
    assert isinstance(cached.expires_at, datetime.datetime)


def test_cache_introspection_token_sets_expiration_from_token_exp(
    mock_introspected_token: IntrospectedOAuth2Token,
):
    """Test that cached tokens have expiration time based on token's exp field."""
    token = "test_token"
    _cache_introspection_token(token, mock_introspected_token)

    token_hash = _hash_token(token)
    cached = _introspection_token_cache[token_hash]

    # Expiration should be set based on token's exp field
    assert mock_introspected_token.exp is not None
    expected_expires = datetime.datetime.fromtimestamp(mock_introspected_token.exp)
    assert cached.expires_at == expected_expires


def test_cache_introspection_token_without_exp():
    """Test that tokens without exp field are not cached."""
    token = "test_token"
    mock_token = MagicMock(spec=IntrospectedOAuth2Token)
    mock_token.active = True
    mock_token.iss = "https://auth.kiwix.org"
    mock_token.client_id = "test_client_id"
    mock_token.exp = None

    _cache_introspection_token(token, mock_token)

    # Token without exp should not be cached
    assert len(_introspection_token_cache) == 0


def test_get_cached_introspection_token_hit(
    mock_introspected_token: IntrospectedOAuth2Token,
):
    """Test that cache hit returns the cached token."""
    token = "test_token"
    _cache_introspection_token(token, mock_introspected_token)

    result = _get_cached_introspection_token(token)

    assert result is not None
    assert result == mock_introspected_token


def test_get_cached_introspection_token_expired_removes_from_cache(
    expired_introspected_token: IntrospectedOAuth2Token,
):
    """Test that expired cache entries are removed and return None."""
    token = "test_token"
    _cache_introspection_token(token, expired_introspected_token)

    # Verify it was cached
    token_hash = _hash_token(token)
    assert token_hash in _introspection_token_cache

    # Try to get it - should return None and remove from cache
    result = _get_cached_introspection_token(token)

    assert result is None
    assert token_hash not in _introspection_token_cache


@pytest.mark.parametrize(
    "exp_delta,should_be_valid",
    [
        pytest.param(
            datetime.timedelta(hours=1),
            True,
            id="one_hour_future",
        ),
        pytest.param(
            datetime.timedelta(minutes=1),
            True,
            id="one_minute_future",
        ),
        pytest.param(
            datetime.timedelta(seconds=1),
            True,
            id="one_second_future",
        ),
        pytest.param(
            datetime.timedelta(hours=-1),
            False,
            id="one_hour_past",
        ),
        pytest.param(
            datetime.timedelta(minutes=-1),
            False,
            id="one_minute_past",
        ),
        pytest.param(
            datetime.timedelta(seconds=-1),
            False,
            id="one_second_past",
        ),
    ],
)
def test_cache_entry_validity_with_various_expirations(
    exp_delta: datetime.timedelta, *, should_be_valid: bool
):
    """Test cache entry validity with various expiration times."""
    token = "test_token"
    mock_token = MagicMock(spec=IntrospectedOAuth2Token)
    mock_token.active = True
    mock_token.exp = int((getnow() + exp_delta).timestamp())

    _cache_introspection_token(token, mock_token)

    token_hash = _hash_token(token)
    if token_hash in _introspection_token_cache:
        cached = _introspection_token_cache[token_hash]
        assert _is_cache_entry_valid(cached) is should_be_valid
