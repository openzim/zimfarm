import ipaddress
from collections.abc import Callable
from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient

from zimfarm_backend.db.models import Account, Recipe, Worker


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
    create_recipe: Callable[..., Recipe],
    create_worker: Callable[..., Worker],
    create_account: Callable[..., Account],
):
    """Test that get_contexts returns unique contexts from both recipes and workers"""
    # Create recipes with contexts
    create_recipe(name="recipe1", context="priority")
    create_recipe(name="recipe2", context="general")

    # Create workers with contexts (some overlapping)
    create_worker(
        account=create_account(),
        name="worker1",
        contexts={"priority": ipaddress.ip_address("127.0.0.1"), "fast": None},
    )
    create_worker(
        account=create_account(),
        name="worker2",
        contexts={"general": None, "slow": None},
    )

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
    create_recipe: Callable[..., Recipe],
    create_worker: Callable[..., Worker],
    create_account: Callable[..., Account],
    skip: int,
    limit: int,
    expected_results: int,
):
    """Test that get_contexts pagination works correctly"""
    # Create recipes and workers with contexts
    create_recipe(name="recipe1", context="context1")
    create_recipe(name="recipe2", context="context2")
    create_worker(
        account=create_account(),
        name="worker1",
        contexts={"context3": None, "context4": None},
    )
    create_worker(
        account=create_account(),
        name="worker2",
        contexts={"context5": None, "context6": None},
    )

    # Test first page
    response = client.get(f"/v2/contexts?skip={skip}&limit={limit}")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["meta"]["skip"] == skip
    assert data["meta"]["limit"] == limit
    assert data["meta"]["page_size"] == expected_results
    assert data["meta"]["count"] == 6
    assert len(data["items"]) == expected_results
