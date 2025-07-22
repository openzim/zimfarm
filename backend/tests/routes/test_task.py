from collections.abc import Callable
from http import HTTPStatus
from typing import Literal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common.enums import TaskStatus
from zimfarm_backend.common.roles import RoleEnum
from zimfarm_backend.db.models import RequestedTask, Task, User, Worker
from zimfarm_backend.utils.token import generate_access_token


def test_get_tasks(
    client: TestClient,
    access_token: str,
    create_task: Callable[..., Task],
):
    """Test successful retrieval of tasks"""
    # Create some tasks
    for _ in range(30):
        create_task()

    response = client.get(
        "/v2/tasks?limit=5&skip=0",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert "items" in data
    assert "meta" in data
    assert "count" in data["meta"]
    assert data["meta"]["count"] == 30
    assert len(data["items"]) == 5


@pytest.mark.parametrize("hide_secrets", ["true", "false"])
def test_get_task_no_auth(
    client: TestClient,
    task: Task,
    hide_secrets: bool,  # noqa: FBT001
):
    """Test successful retrieval of a single task"""
    response = client.get(
        f"/v2/tasks/{task.id}?hide_secrets={hide_secrets}",
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert "config" in data
    config = data["config"]
    assert "offliner" in config
    assert "offliner_id" in config["offliner"]
    assert "mwPassword" in config["offliner"]

    for char in config["offliner"]["mwPassword"]:
        assert char == "*"


@pytest.mark.parametrize("hide_secrets", ["true", "false"])
def test_get_task_with_auth(
    client: TestClient,
    task: Task,
    access_token: str,
    hide_secrets: Literal["true", "false"],
):
    """Test successful retrieval of a single task"""
    response = client.get(
        f"/v2/tasks/{task.id}?hide_secrets={hide_secrets}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert "config" in data
    config = data["config"]
    assert "offliner" in config
    assert "offliner_id" in config["offliner"]
    assert "mwPassword" in config["offliner"]

    if hide_secrets == "true":
        for char in config["offliner"]["mwPassword"]:
            assert char == "*"
    else:
        assert config["offliner"]["mwPassword"] == "test-password"


def test_create_task_no_permission(
    client: TestClient,
    create_user: Callable[..., User],
    requested_task: RequestedTask,
    worker: Worker,
):
    """Test that create_task raises ForbiddenError without permission"""
    user = create_user(permission=RoleEnum.PROCESSOR)
    access_token = generate_access_token(
        user_id=str(user.id),
        username=user.username,
        email=user.email,
        scope=user.scope,
    )

    response = client.post(
        f"/v2/tasks/{requested_task.id}",
        json={"worker_name": worker.name},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_create_task_no_requested_task(
    client: TestClient,
    access_token: str,
    worker: Worker,
):
    """Test that create_task raises NotFoundError with non-existent requested task"""
    uuid = uuid4()
    response = client.post(
        f"/v2/tasks/{uuid}",
        json={"worker_name": worker.name},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_create_task_no_worker(
    client: TestClient,
    access_token: str,
    requested_task: RequestedTask,
):
    """Test that create_task raises NotFoundError with non-existent worker"""
    response = client.post(
        f"/v2/tasks/{requested_task.id}",
        json={"worker_name": "nonexistent-worker"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_create_task_success(
    client: TestClient,
    access_token: str,
    requested_task: RequestedTask,
    worker: Worker,
):
    """Test successful creation of task"""
    response = client.post(
        f"/v2/tasks/{requested_task.id}",
        json={"worker_name": worker.name},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    assert data["id"] == str(requested_task.id)


def test_update_task_no_permission(
    client: TestClient,
    access_token: str,
    task: Task,
    create_user: Callable[..., User],
):
    """Test that update_task raises ForbiddenError without permission"""
    user = create_user(permission=RoleEnum.EDITOR)
    access_token = generate_access_token(
        user_id=str(user.id),
        username=user.username,
        email=user.email,
        scope=user.scope,
    )

    response = client.patch(
        f"/v2/tasks/{task.id}",
        json={"event": TaskStatus.started.value, "payload": {"worker": "test-worker"}},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_update_task_not_found(
    client: TestClient,
    access_token: str,
):
    """Test that update_task raises NotFoundError with non-existent task"""
    response = client.patch(
        "/v2/tasks/00000000-0000-0000-0000-000000000000",
        json={"event": TaskStatus.started.value, "payload": {"worker": "test-worker"}},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_update_task_success(
    client: TestClient,
    access_token: str,
    task: Task,
    worker: Worker,
    create_user: Callable[..., User],
):
    """Test successful update of task"""
    user = create_user(permission=RoleEnum.ADMIN)
    access_token = generate_access_token(
        user_id=str(user.id),
        username=user.username,
        email=user.email,
        scope=user.scope,
    )

    response = client.patch(
        f"/v2/tasks/{task.id}",
        json={"event": TaskStatus.started.value, "payload": {"worker": worker.name}},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.NO_CONTENT


def test_cancel_task_no_permission(
    client: TestClient,
    access_token: str,
    task: Task,
    create_user: Callable[..., User],
):
    """Test that cancel_task raises ForbiddenError without permission"""
    user = create_user(permission=RoleEnum.EDITOR)
    access_token = generate_access_token(
        user_id=str(user.id),
        username=user.username,
        email=user.email,
        scope=user.scope,
    )

    response = client.post(
        f"/v2/tasks/{task.id}/cancel",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_cancel_task_not_found(
    client: TestClient,
    access_token: str,
):
    """Test that cancel_task raises NotFoundError with non-existent task"""
    response = client.post(
        "/v2/tasks/00000000-0000-0000-0000-000000000000/cancel",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_cancel_task_completed(
    dbsession: OrmSession,
    client: TestClient,
    access_token: str,
    task: Task,
):
    """Test that cancel_task raises NotFoundError for completed task"""
    task.status = TaskStatus.succeeded
    dbsession.add(task)
    dbsession.flush()
    response = client.post(
        f"/v2/tasks/{task.id}/cancel",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_cancel_task_success(
    client: TestClient,
    access_token: str,
    task: Task,
    create_user: Callable[..., User],
):
    """Test successful cancellation of task"""
    user = create_user(permission=RoleEnum.ADMIN)
    access_token = generate_access_token(
        user_id=str(user.id),
        username=user.username,
        email=user.email,
        scope=user.scope,
    )

    response = client.post(
        f"/v2/tasks/{task.id}/cancel",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.NO_CONTENT
