from collections.abc import Callable
from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient

from zimfarm_backend.db.models import Schedule, Worker


def test_get_contexts_empty(client: TestClient):
    """Test that get_contexts returns empty list when no contexts exist"""
    response = client.get("/v2/contexts?skip=0&limit=10")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert "meta" in data
    assert "items" in data
    assert data["meta"]["skip"] == 0
    assert data["meta"]["limit"] == 10
    assert data["meta"]["page_size"] == 0
    assert data["meta"]["count"] == 0
    assert data["items"] == []


def test_get_contexts(
    client: TestClient,
    create_schedule: Callable[..., Schedule],
    create_worker: Callable[..., Worker],
):
    """Test that get_contexts returns unique contexts from both schedules and workers"""
    # Create schedules with contexts
    create_schedule(name="schedule1", context="priority")
    create_schedule(name="schedule2", context="general")

    # Create workers with contexts (some overlapping)
    create_worker(name="worker1", contexts=["priority", "fast"])
    create_worker(name="worker2", contexts=["general", "slow"])

    response = client.get("/v2/contexts?skip=0&limit=10")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["meta"]["count"] == 4
    assert data["items"] == ["fast", "general", "priority", "slow"]


@pytest.mark.parametrize(
    "skip,limit,expected_results",
    [
        pytest.param(0, 3, 3, id="first-page"),
        pytest.param(3, 3, 3, id="second-page"),
        pytest.param(0, 1, 1, id="first-page-with-low-limit"),
        pytest.param(0, 10, 6, id="first-page-with-high-limit"),
        pytest.param(10, 10, 0, id="page-num-too-high-no-results"),
    ],
)
def test_get_contexts_pagination(
    client: TestClient,
    create_schedule: Callable[..., Schedule],
    create_worker: Callable[..., Worker],
    skip: int,
    limit: int,
    expected_results: int,
):
    """Test that get_contexts pagination works correctly"""
    # Create schedules and workers with contexts
    create_schedule(name="schedule1", context="context1")
    create_schedule(name="schedule2", context="context2")
    create_worker(name="worker1", contexts=["context3", "context4"])
    create_worker(name="worker2", contexts=["context5", "context6"])

    # Test first page
    response = client.get(f"/v2/contexts?skip={skip}&limit={limit}")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["meta"]["skip"] == skip
    assert data["meta"]["limit"] == limit
    assert data["meta"]["page_size"] == expected_results
    assert data["meta"]["count"] == 6
    assert len(data["items"]) == expected_results
