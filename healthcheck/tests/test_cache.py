import asyncio
from http import HTTPStatus
from typing import Any

import pytest
from diskcache import FanoutCache

from healthcheck.cache import CACHE_KEY_PREFIX, memoize
from healthcheck.status import Result


@pytest.mark.asyncio
async def test_memoize_successful_result() -> None:
    """Test that successful results are cached."""
    counter = 0

    @memoize("test-success")
    async def get_success() -> Result[str]:
        nonlocal counter
        counter += 1
        return Result(
            success=True,
            status_code=HTTPStatus.OK,
            data="success",
        )

    result1 = await get_success()
    assert result1.success
    assert result1.data == "success"
    assert counter == 1

    result2 = await get_success()
    assert result2.success
    assert result2.data == "success"
    assert counter == 1  # Counter shouldn't increment


@pytest.mark.asyncio
async def test_memoize_failed_result() -> None:
    """Test that failed results are not cached."""
    counter = 0

    @memoize("test-failure")
    async def get_failure() -> Result[Any]:
        nonlocal counter
        counter += 1
        return Result(
            success=False,
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            data=None,
        )

    result1 = await get_failure()
    assert not result1.success
    assert result1.data is None
    assert counter == 1

    result2 = await get_failure()
    assert not result2.success
    assert result2.data is None
    assert counter == 2  # Counter should increment


@pytest.mark.asyncio
async def test_memoize_cache_expiry() -> None:
    """Test that cached values expire after TTL."""
    counter = 0

    @memoize("test-expiry", ttl=0.1)
    async def get_data() -> Result[int]:
        nonlocal counter
        counter += 1
        return Result(
            success=True,
            status_code=HTTPStatus.OK,
            data=counter,
        )

    result1 = await get_data()
    assert result1.success
    assert result1.data == 1
    assert counter == 1

    # Immediate second call should use cache
    result2 = await get_data()
    assert result2.data == 1
    assert counter == 1

    # Wait for cache to expire
    await asyncio.sleep(0.2)

    # Call after expiry should execute function again
    result3 = await get_data()
    assert result3.data == 2
    assert counter == 2


@pytest.mark.asyncio
async def test_cache_key_prefix(cache: FanoutCache) -> None:
    """Test that cache keys include the configured prefix."""

    @memoize("test-prefix")
    async def get_data() -> Result[str]:
        return Result(
            success=True,
            status_code=HTTPStatus.OK,
            data="test",
        )

    await get_data()

    # Check that the key exists with correct prefix
    key = f"{CACHE_KEY_PREFIX}:test-prefix"
    assert key in cache

    cached_value = cache.get(key)
    assert isinstance(cached_value, Result)
    assert cached_value.success
    assert cached_value.data == "test"  # pyright: ignore[reportUnknownMemberType]
