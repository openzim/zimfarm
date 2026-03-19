import datetime
import logging
from dataclasses import dataclass, field

import requests

from zimfarm_backend.common import getnow, to_naive_utc
from zimfarm_backend.common.constants import (
    GITHUB_API_VERSION,
    GITHUB_PACKAGE_REGISTRY_CACHE_DURATION,
    GITHUB_TOKEN,
    REQ_TIMEOUT_GHCR,
)

logger = logging.getLogger(__name__)


@dataclass
class WorkerManagerVersion:
    hash: str
    created_at: datetime.datetime


@dataclass
class CacheEntry:
    """Cache entry for worker manager version."""

    data: WorkerManagerVersion | None = None
    last_run: datetime.datetime = field(
        default_factory=lambda: datetime.datetime.fromtimestamp(0).replace(tzinfo=None)
    )

    @property
    def is_valid(self) -> bool:
        """Check if the cache is still valid (less than 5 minutes old)."""
        if self.data is None:
            return False

        return (getnow() - self.last_run) < GITHUB_PACKAGE_REGISTRY_CACHE_DURATION


_cache = CacheEntry()


def _fetch_latest_worker_manager_version() -> WorkerManagerVersion | None:
    """
    Fetch the latest worker manager version from GitHub Container Registry.
    """
    try:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
            "Authorization": f"token {GITHUB_TOKEN}",
        }

        response = requests.get(
            (
                "https://api.github.com/orgs/openzim/packages/container/"
                "zimfarm-worker-manager/versions"
            ),
            headers=headers,
            timeout=REQ_TIMEOUT_GHCR,
        )
        response.raise_for_status()

        versions = response.json()

        # Find the version tagged with "latest"
        for version in versions:
            tags = version.get("metadata", {}).get("container", {}).get("tags", [])
            if "latest" in tags:
                hash_value = version["name"]
                created_at = to_naive_utc(
                    datetime.datetime.fromisoformat(version["created_at"])
                )

                return WorkerManagerVersion(
                    hash=hash_value,
                    created_at=created_at,
                )

        logger.warning(
            "No zimfarm-worker-manager version with 'latest' tag found "
            "in GitHub registry"
        )
        return None
    except Exception:
        logger.exception("Failed to fetch latest zimfarm-worker-manager")
        return None


def get_latest_worker_manager_version() -> WorkerManagerVersion | None:
    """
    Get the latest worker manager version, using cache if available.
    """

    if _cache.is_valid:
        logger.debug("Using cached worker manager version")
        if _cache.data is None:
            raise ValueError("Cache has no data but is marked as valid.")
        return _cache.data

    logger.info("Fetching latest worker manager version from GitHub")
    version = _fetch_latest_worker_manager_version()
    if version is not None:
        _cache.data = version
        _cache.last_run = getnow()

    return version
