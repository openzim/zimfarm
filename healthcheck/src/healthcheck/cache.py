from collections.abc import Awaitable, Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from diskcache import FanoutCache

from healthcheck.constants import (
    CACHE_KEY_PREFIX,
    CACHE_LOCATION,
    DEFAULT_CACHE_EXPIRATION,
)

P = ParamSpec("P")
R = TypeVar("R")

# As per the docs, writers can block other writers to the cache. The FanoutCache as
# opposed to the simpler Cache uses sharding to decrease block writes. This makes
# it a good candidate for our usage because the functions we want to memoize are run
# "concurrently" using asyncio.gather.
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
    key: str,
    expire: float = DEFAULT_CACHE_EXPIRATION,
    *,
    cache_only_on_success: bool = True,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """Memoize function calls with results at CACHE_KEY_PREFIX:key.

    Results are considered successful if they have a success attribute and it is truthy.
    """

    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            cache = init_cache()
            location = f"{CACHE_KEY_PREFIX}:{key}"
            if (result := cache.get(location)) is not None:
                return result

            result = await func(*args, **kwargs)

            if cache_only_on_success:
                if (
                    hasattr(result, "success")
                    and result.success  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
                ):
                    cache.set(location, result, expire=expire)
            else:
                cache.set(location, result, expire=expire)
            return result

        return wrapper

    return decorator
