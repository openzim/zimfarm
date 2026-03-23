import datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from zimfarm_backend.utils import github_registry
from zimfarm_backend.utils.github_registry import (
    CacheEntry,
    WorkerManagerVersion,
    get_latest_worker_manager_version,
)


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear the cache before and after each test."""
    github_registry._cache.data = None  # pyright: ignore[reportPrivateUsage]
    github_registry._cache.last_run = (  # pyright: ignore[reportPrivateUsage]
        datetime.datetime.fromtimestamp(0).replace(tzinfo=None)
    )

    yield

    # Clear after test
    github_registry._cache.data = None  # pyright: ignore[reportPrivateUsage]
    github_registry._cache.last_run = (  # pyright: ignore[reportPrivateUsage]
        datetime.datetime.fromtimestamp(0).replace(tzinfo=None)
    )


@pytest.fixture
def mock_github_response() -> list[dict[str, Any]]:
    """Create a mock GitHub API response."""
    return [
        {
            "id": 745626629,
            "name": (
                "sha256:8ff3888516bfd2150a5e26fea2472e296da09d2de54fc91e2256e2e"
                "17c69769c"
            ),
            "url": (
                "https://api.github.com/orgs/openzim/packages/container/"
                "zimfarm-worker-manager/versions/745626629"
            ),
            "package_html_url": (
                "https://github.com/orgs/openzim/packages/container/package/"
                "zimfarm-worker-manager"
            ),
            "created_at": "2026-03-19T11:27:59Z",
            "updated_at": "2026-03-19T11:27:59Z",
            "html_url": (
                "https://github.com/orgs/openzim/packages/container/"
                "zimfarm-worker-manager/745626629"
            ),
            "metadata": {
                "package_type": "container",
                "container": {"tags": ["latest"]},
            },
        },
        {
            "id": 741679047,
            "name": (
                "sha256:dfbcb51a16173fb7d65ac6d856f9aa43135eba56578d83897c578c4e"
                "e681bc6f"
            ),
            "url": (
                "https://api.github.com/orgs/openzim/packages/container/"
                "zimfarm-worker-manager/versions/741679047"
            ),
            "package_html_url": (
                "https://github.com/orgs/openzim/packages/container/package/"
                "zimfarm-worker-manager"
            ),
            "created_at": "2026-03-17T16:31:25Z",
            "updated_at": "2026-03-17T16:31:25Z",
            "html_url": (
                "https://github.com/orgs/openzim/packages/container/"
                "zimfarm-worker-manager/741679047"
            ),
            "metadata": {"package_type": "container", "container": {"tags": []}},
        },
    ]


def test_cache_entry_is_valid_no_data() -> None:
    """Test cache is invalid when data is None."""
    cache = CacheEntry(data=None, last_run=datetime.datetime.now(tz=datetime.UTC))
    assert not cache.is_valid


@patch("zimfarm_backend.utils.github_registry.getnow")
def test_cache_entry_is_valid_recent(mock_getnow: MagicMock) -> None:
    """Test cache is valid when data exists and is recent."""
    now = datetime.datetime(2026, 3, 19, 12, 0, 0)
    mock_getnow.return_value = now

    cache = CacheEntry(
        data=WorkerManagerVersion(
            hash="test_hash",
            created_at=datetime.datetime(2026, 3, 19, 11, 0, 0),
        ),
        last_run=now - datetime.timedelta(minutes=2),
    )

    assert cache.is_valid


@patch("zimfarm_backend.utils.github_registry.getnow")
def test_cache_entry_is_valid_expired(mock_getnow: MagicMock) -> None:
    """Test cache is invalid when data is older than cache duration."""
    now = datetime.datetime(2026, 3, 19, 12, 0, 0)
    mock_getnow.return_value = now

    cache = CacheEntry(
        data=WorkerManagerVersion(
            hash="test_hash",
            created_at=datetime.datetime(2026, 3, 19, 11, 0, 0),
        ),
        last_run=now - datetime.timedelta(minutes=6),
    )

    assert not cache.is_valid


@patch("zimfarm_backend.utils.github_registry.requests.get")
@patch("zimfarm_backend.utils.github_registry.GITHUB_TOKEN", "test_token")
def test_fetch_success_with_latest_tag(
    mock_requests_get: MagicMock,
    mock_github_response: list[dict[str, Any]],
) -> None:
    """Test successful fetch of version with latest tag."""
    mock_response = MagicMock()
    mock_response.json.return_value = mock_github_response
    mock_response.raise_for_status = MagicMock()
    mock_requests_get.return_value = mock_response

    result = get_latest_worker_manager_version()

    assert result is not None
    assert result.hash == (
        "sha256:8ff3888516bfd2150a5e26fea2472e296da09d2de54fc91e2256e2e17c69769c"
    )
    assert result.created_at is not None


@patch("zimfarm_backend.utils.github_registry.requests.get")
def test_fetch_no_latest_tag(mock_requests_get: MagicMock) -> None:
    """Test fetch when no version has latest tag."""
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {
            "id": 741679047,
            "name": (
                "sha256:dfbcb51a16173fb7d65ac6d856f9aa43135eba56578d83897c"
                "578c4ee681bc6f"
            ),
            "created_at": "2026-03-17T16:31:25Z",
            "metadata": {
                "package_type": "container",
                "container": {"tags": []},
            },
        }
    ]
    mock_response.raise_for_status = MagicMock()
    mock_requests_get.return_value = mock_response

    result = get_latest_worker_manager_version()

    assert result is None
