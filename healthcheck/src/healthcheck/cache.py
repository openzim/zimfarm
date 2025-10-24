from collections.abc import Awaitable, Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from diskcache import FanoutCache

from healthcheck.constants import CACHE_KEY_PREFIX, CACHE_LOCATION, DEFAULT_CACHE_TTL

P = ParamSpec("P")
R = TypeVar("R")

_cache: FanoutCache | None = None


def init_cache() -> FanoutCache:
    """Get or create the disk cache instance."""
    global _cache  # noqa: PLW0603
    if _cache is None:
        _cache = FanoutCache(CACHE_LOCATION)
    return _cache


def close_cache() -> None:
    """Close the disk cache instance."""
    global _cache  # noqa: PLW0603
    if _cache is not None:
        _cache.close()
        _cache = None


def memoize(
    key: str, ttl: float = DEFAULT_CACHE_TTL
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """Memoize successful results of functions with results at CACHE_KEY_PREFIX:key.

    Results are considered successful if ther success attribute is truthy.
    """

    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            cache = init_cache()
            _key = f"{CACHE_KEY_PREFIX}:{key}"

            if (result := cache.get(_key)) is not None:
                return result

            result = await func(*args, **kwargs)
            if (
                hasattr(result, "success")
                and result.success  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
            ):
                cache.set(_key, result, expire=ttl)
            return result

        return wrapper

    return decorator
