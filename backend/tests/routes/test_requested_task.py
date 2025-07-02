from collections.abc import Callable
from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common.roles import RoleEnum
from zimfarm_backend.db.models import RequestedTask, Schedule, User, Worker
from zimfarm_backend.utils.token import generate_access_token


def test_create_request_task_no_permission(
    client: TestClient,
    create_user: Callable[..., User],
):
    """Test that create_request_task raises ForbiddenError without permission"""
    user = create_user(permission=RoleEnum.PROCESSOR)
    access_token = generate_access_token(
        user_id=str(user.id),
        username=user.username,
        email=user.email,
        scope=user.scope,
    )

    response = client.post(
        "/api/v2/requested-tasks",
        json={
            "schedule_names": ["test-schedule"],
            "worker": "test-worker",
            "priority": 1,
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_create_request_task_no_enabled_schedules(
    client: TestClient,
    dbsession: OrmSession,
    access_token: str,
    schedule: Schedule,
    worker: Worker,
):
    """Test that create_request_task raises NotFoundError with no enabled schedules"""
    schedule.enabled = False
    dbsession.add(schedule)
    dbsession.flush()

    response = client.post(
        "/api/v2/requested-tasks",
        json={"schedule_names": [schedule.name], "worker": worker.name, "priority": 1},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_create_request_task_success(
    client: TestClient,
    access_token: str,
    schedule: Schedule,
    worker: Worker,
):
    """Test successful creation of requested task"""
    response = client.post(
        "/api/v2/requested-tasks",
        json={"schedule_names": [schedule.name], "worker": worker.name, "priority": 1},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert "requested" in data
    assert len(data["requested"]) == 1


def test_get_requested_tasks_success(
    client: TestClient,
    access_token: str,
    create_requested_task: Callable[..., RequestedTask],
    worker: Worker,
):
    """Test successful retrieval of requested tasks"""
    # Create some requested tasks
    for _ in range(30):
        create_requested_task(worker=worker)

    response = client.get(
        "/api/v2/requested-tasks?limit=5&worker_name=test-worker",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert "items" in data
    assert "meta" in data
    assert "count" in data["meta"]
    assert data["meta"]["count"] == 30
    assert len(data["items"]) == 5


@pytest.mark.skip(
    reason="The route calls commit on the db session, which is not supported in tests"
)
def test_get_requested_tasks_for_worker_success(
    client: TestClient,
    access_token: str,
    create_requested_task: Callable[..., RequestedTask],
    worker: Worker,
):
    """Test successful retrieval of requested tasks for a worker"""
    # Create a task for the worker
    create_requested_task(worker=worker)

    response = client.get(
        f"/api/v2/requested-tasks/worker?worker_name={worker.name}&avail_cpu={worker.cpu}&avail_memory={worker.memory}&avail_disk={worker.disk}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-Forwarded-For": "127.0.0.1",
        },
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert "items" in data
    assert "meta" in data
    assert "count" in data["meta"]
    assert data["meta"]["count"] == 1
    assert len(data["items"]) == 1


@pytest.mark.parametrize("hide_secrets", ["true", "false"])
def test_get_requested_task_success(
    client: TestClient,
    access_token: str,
    requested_task: RequestedTask,
    hide_secrets: bool,  # noqa: FBT001
):
    """Test successful retrieval of a single requested task"""
    response = client.get(
        f"/api/v2/requested-tasks/{requested_task.id}?hide_secrets={hide_secrets}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert "config" in data
    config = data["config"]
    assert "offliner" in config
    assert "offliner_id" in config["offliner"]
    assert "mwPassword" in config["offliner"]

    if hide_secrets:
        for char in config["offliner"]["mwPassword"]:
            assert char == "*"
    else:
        assert config["offliner"]["mwPassword"] == "test-password"


def test_update_requested_task_no_permission(
    client: TestClient,
    access_token: str,
    requested_task: RequestedTask,
    create_user: Callable[..., User],
):
    """Test that update_requested_task raises ForbiddenError without permission"""
    user = create_user(permission=RoleEnum.EDITOR)
    access_token = generate_access_token(
        user_id=str(user.id),
        username=user.username,
        email=user.email,
        scope=user.scope,
    )

    response = client.patch(
        f"/api/v2/requested-tasks/{requested_task.id}",
        json={"priority": 1},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_update_requested_task_success(
    client: TestClient,
    access_token: str,
    requested_task: RequestedTask,
    create_user: Callable[..., User],
):
    """Test successful update of requested task priority"""
    user = create_user(permission=RoleEnum.ADMIN)
    access_token = generate_access_token(
        user_id=str(user.id),
        username=user.username,
        email=user.email,
        scope=user.scope,
    )

    response = client.patch(
        f"/api/v2/requested-tasks/{requested_task.id}",
        json={"priority": 1},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["priority"] == 1


def test_delete_requested_task_no_permission(
    client: TestClient,
    requested_task: RequestedTask,
    create_user: Callable[..., User],
):
    """Test that delete_requested_task raises ForbiddenError without permission"""
    user = create_user(permission=RoleEnum.EDITOR)
    access_token = generate_access_token(
        user_id=str(user.id),
        username=user.username,
        email=user.email,
        scope=user.scope,
    )

    response = client.delete(
        f"/api/v2/requested-tasks/{requested_task.id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_delete_requested_task_success(
    client: TestClient,
    requested_task: RequestedTask,
    create_user: Callable[..., User],
):
    """Test successful deletion of requested task"""
    user = create_user(permission=RoleEnum.ADMIN)
    access_token = generate_access_token(
        user_id=str(user.id),
        username=user.username,
        email=user.email,
        scope=user.scope,
    )

    response = client.delete(
        f"/api/v2/requested-tasks/{requested_task.id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["deleted"] == 1
