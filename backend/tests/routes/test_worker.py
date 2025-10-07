from collections.abc import Callable
from http import HTTPStatus
from ipaddress import IPv4Address, IPv6Address

import pytest
from fastapi.testclient import TestClient

from zimfarm_backend.common import getnow
from zimfarm_backend.common.enums import TaskStatus
from zimfarm_backend.common.roles import RoleEnum
from zimfarm_backend.db.models import Task, User, Worker
from zimfarm_backend.utils.token import generate_access_token


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
    """Test that check_in_worker creates new worker when it does not exists"""
    response = client.put(
        "/v2/workers/a-new-worker/check-in",
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


def test_check_in_worker_impersonate_user(
    client: TestClient,
    access_token: str,
    create_worker: Callable[..., Worker],
    create_user: Callable[..., User],
):
    """Test that check_in_worker raises BadRequestError for deleted worker"""
    worker = create_worker(user=create_user())

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


def test_get_worker_metrics_no_tasks(client: TestClient, worker: Worker):
    """Worker metrics should be zero when no tasks exist."""
    response = client.get(f"/v2/workers/{worker.name}/metrics")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["name"] == worker.name
    assert data["nb_tasks_total"] == 0
    assert data["nb_tasks_completed"] == 0
    assert data["nb_tasks_succeeded"] == 0
    assert data["nb_tasks_failed"] == 0
    assert isinstance(data["running_tasks"], list)
    assert len(data["running_tasks"]) == 0


def test_get_worker_metrics_with_tasks(
    client: TestClient,
    worker: Worker,
    create_task: Callable[..., Task],
):
    """Worker metrics should reflect counts of total, completed, succeeded, failed."""
    # Create tasks across statuses
    for _ in range(3):
        create_task(status=TaskStatus.succeeded)
    for _ in range(2):
        create_task(status=TaskStatus.failed)
    for _ in range(1):
        create_task(status=TaskStatus.canceled)
    for _ in range(2):
        create_task(status=TaskStatus.started)
    for _ in range(1):
        create_task(status=TaskStatus.requested)

    response = client.get(f"/v2/workers/{worker.name}/metrics")
    assert response.status_code == HTTPStatus.OK
    data = response.json()

    # Totals
    assert data["nb_tasks_total"] == 9
    assert data["nb_tasks_completed"] == 6  # 3 succeeded + 2 failed + 1 canceled
    assert data["nb_tasks_succeeded"] == 3
    assert data["nb_tasks_failed"] == 2

    # Running tasks are non-complete
    assert isinstance(data["running_tasks"], list)
    assert len(data["running_tasks"]) == 3  # 2 started + 1 requested


@pytest.mark.parametrize(
    "permission,contexts,deleted,expected_status",
    [
        [
            RoleEnum.ADMIN,
            {"priority": "127.0.0.1", "general": None},
            False,
            HTTPStatus.NO_CONTENT,
        ],
        [RoleEnum.PROCESSOR, {"general": None}, False, HTTPStatus.UNAUTHORIZED],
        [
            RoleEnum.ADMIN,
            {"priority": "127.0.0.1", "general": None},
            True,
            HTTPStatus.BAD_REQUEST,
        ],
    ],
)
def test_update_worker_context(
    client: TestClient,
    create_worker: Callable[..., Worker],
    create_user: Callable[..., User],
    *,
    permission: RoleEnum,
    contexts: dict[str, IPv4Address | IPv6Address | None],
    expected_status: HTTPStatus,
    deleted: bool,
):
    """Test successful update of a worker's context"""
    user = create_user(permission=permission)
    worker = create_worker(user=user, deleted=deleted)

    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        email=user.email,
        scope=user.scope,
    )

    response = client.put(
        f"/v2/workers/{worker.name}/context",
        json={"contexts": contexts},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == expected_status


def test_update_worker_context_not_found(
    client: TestClient,
    create_worker: Callable[..., Worker],
    create_user: Callable[..., User],
):
    user = create_user(permission=RoleEnum.ADMIN)
    create_worker(user=user, deleted=False)

    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        email=user.email,
        scope=user.scope,
    )

    response = client.put(
        "/v2/workers/non-existent/context",
        json={"contexts": {"priority": "127.0.0.1", "general": None}},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_update_worker_context_no_payload(
    client: TestClient,
    create_worker: Callable[..., Worker],
    create_user: Callable[..., User],
):
    user = create_user(permission=RoleEnum.ADMIN)
    worker = create_worker(user=user, deleted=False)

    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        email=user.email,
        scope=user.scope,
    )

    response = client.put(
        f"/v2/workers/{worker.name}/context",
        json={},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
