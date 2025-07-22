from collections.abc import Callable
from http import HTTPStatus

from fastapi.testclient import TestClient

from zimfarm_backend.db.models import Worker


def test_get_active_workers_success(
    client: TestClient,
    access_token: str,
    create_worker: Callable[..., Worker],
):
    """Test successful retrieval of active workers"""
    # Create some workers
    for i in range(30):
        create_worker(name=f"test-worker-{i}")

    response = client.get(
        "/v2/workers?limit=5&skip=0",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert "items" in data
    assert "meta" in data
    assert "count" in data["meta"]
    assert data["meta"]["count"] == 30
    assert len(data["items"]) == 5


def test_check_in_worker_not_found(
    client: TestClient,
    access_token: str,
):
    """Test that check_in_worker raises NotFoundError for non-existent worker"""
    response = client.put(
        "/v2/workers/non-existent/check-in",
        json={
            "selfish": True,
            "cpu": 1,
            "memory": 1024,
            "disk": 2048,
            "offliners": ["mwoffliner"],
            "platforms": None,
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_check_in_worker_deleted(
    client: TestClient,
    access_token: str,
    create_worker: Callable[..., Worker],
):
    """Test that check_in_worker raises BadRequestError for deleted worker"""
    worker = create_worker(deleted=True)

    response = client.put(
        f"/v2/workers/{worker.name}/check-in",
        json={
            "selfish": True,
            "cpu": 1,
            "memory": 1024,
            "disk": 2048,
            "offliners": ["mwoffliner"],
            "platforms": None,
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_check_in_worker_success(
    client: TestClient,
    access_token: str,
    create_worker: Callable[..., Worker],
):
    """Test successful check-in of a worker"""
    worker = create_worker()

    response = client.put(
        f"/v2/workers/{worker.name}/check-in",
        json={
            "selfish": True,
            "cpu": 1,
            "memory": 1024,
            "disk": 2048,
            "offliners": ["mwoffliner"],
            "platforms": None,
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.NO_CONTENT
