from pathlib import Path

import pytest

from healthcheck import cache as cache_module
from healthcheck.cache import close_cache, init_cache


@pytest.fixture(autouse=True)
def cache_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for cache files."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return cache_dir


@pytest.fixture(autouse=True)
def cache(cache_dir: Path, monkeypatch: pytest.MonkeyPatch):
    """Configure cache to use temporary directory and ensure it's closed after test."""
    monkeypatch.setattr(cache_module, "CACHE_LOCATION", cache_dir)
    cache = init_cache()
    yield cache
    close_cache()
