from collections.abc import Callable
from http import HTTPStatus
from typing import Literal
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
import requests
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy.orm.attributes import flag_modified

from zimfarm_backend.api.routes.tasks import logic as tasks_module
from zimfarm_backend.api.token import generate_access_token
from zimfarm_backend.common import getnow
from zimfarm_backend.common.enums import TaskStatus
from zimfarm_backend.common.roles import RoleEnum
from zimfarm_backend.common.schemas.models import FileCreateUpdateSchema
from zimfarm_backend.db.models import RequestedTask, Task, User, Worker
from zimfarm_backend.db.tasks import create_or_update_task_file


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
@patch("zimfarm_backend.common.upload.requests.get")
def test_get_task_no_auth(
    mock_requests_get: Mock,
    client: TestClient,
    task: Task,
    hide_secrets: str,
):
    """Test successful retrieval of a single task"""
    mock_response = Mock()
    mock_response.json.return_value = {"urls": {}}
    mock_response.raise_for_status = Mock()
    mock_requests_get.return_value = mock_response

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
@patch("zimfarm_backend.common.upload.requests.get")
def test_get_task_with_auth(
    mock_requests_get: Mock,
    client: TestClient,
    task: Task,
    access_token: str,
    hide_secrets: Literal["true", "false"],
):
    """Test successful retrieval of a single task"""
    mock_response = Mock()
    mock_response.json.return_value = {"urls": {}}
    mock_response.raise_for_status = Mock()
    mock_requests_get.return_value = mock_response

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


@patch("zimfarm_backend.common.upload.requests.get")
def test_get_obsolete_task(
    mock_requests_get: Mock,
    client: TestClient,
    dbsession: OrmSession,
    create_user: Callable[..., User],
    create_task: Callable[..., Task],
):
    mock_response = Mock()
    mock_response.json.return_value = {"urls": {}}
    mock_response.raise_for_status = Mock()
    mock_requests_get.return_value = mock_response

    user = create_user(permission=RoleEnum.ADMIN)
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
    )
    task = create_task()
    task.config["offliner"]["mwUrl"] = None  # Unset mandatory field
    task.config["offliner"]["oldFlag"] = "anyValue"  # Set unknown field
    flag_modified(task, "config")
    dbsession.add(task)
    dbsession.flush()

    response = client.get(
        f"/v2/tasks/{task.id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.OK
    task_data = response.json()
    assert "config" in task_data
    assert "offliner" in task_data["config"]
    assert "mwUrl" in task_data["config"]["offliner"]
    assert task_data["config"]["offliner"]["mwUrl"] is None
    assert "oldFlag" in task_data["config"]["offliner"]
    assert task_data["config"]["offliner"]["oldFlag"] == "anyValue"


def test_create_task_no_permission(
    client: TestClient,
    create_user: Callable[..., User],
    requested_task: RequestedTask,
    worker: Worker,
):
    """Test that create_task raises ForbiddenError without permission"""
    user = create_user(permission=RoleEnum.PROCESSOR)
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
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
        issue_time=getnow(),
        user_id=str(user.id),
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
        issue_time=getnow(),
        user_id=str(user.id),
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
        issue_time=getnow(),
        user_id=str(user.id),
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
        issue_time=getnow(),
        user_id=str(user.id),
    )

    response = client.post(
        f"/v2/tasks/{task.id}/cancel",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.NO_CONTENT


@patch("zimfarm_backend.common.upload.requests.get")
def test_get_task_populate_zim_urls_disabled(
    mock_requests_get: Mock,
    client: TestClient,
    dbsession: OrmSession,
    task: Task,
    monkeypatch: pytest.MonkeyPatch,
):
    """Test that populate_zim_urls is not called when INFORM_CMS is disabled"""
    monkeypatch.setattr(tasks_module, "INFORM_CMS", False)

    create_or_update_task_file(
        dbsession,
        FileCreateUpdateSchema(
            task_id=task.id,
            name="test.zim",
            status="uploaded",
            info={"id": "test-zim-id-123"},
        ),
    )
    dbsession.flush()

    response = client.get(f"/v2/tasks/{task.id}")
    assert response.status_code == HTTPStatus.OK

    mock_requests_get.assert_not_called()

    data = response.json()
    assert "files" in data
    assert "test.zim" in data["files"]
    assert data["files"]["test.zim"]["zim_urls"] == []


@patch("zimfarm_backend.common.upload.requests.get")
def test_get_task_populate_zim_urls_enabled_no_files(
    mock_requests_get: Mock,
    client: TestClient,
    task: Task,
    monkeypatch: pytest.MonkeyPatch,
):
    """Test populate_zim_urls when INFORM_CMS is enabled but task has no files"""
    monkeypatch.setattr(tasks_module, "INFORM_CMS", True)

    mock_response = Mock()
    mock_response.json.return_value = {"urls": {}}
    mock_response.raise_for_status = Mock()
    mock_requests_get.return_value = mock_response

    response = client.get(f"/v2/tasks/{task.id}")
    assert response.status_code == HTTPStatus.OK

    mock_requests_get.assert_not_called()

    data = response.json()
    assert "files" in data
    assert len(data["files"]) == 0


@patch("zimfarm_backend.common.upload.requests.get")
def test_get_task_populate_zim_urls_enabled(
    mock_requests_get: Mock,
    client: TestClient,
    dbsession: OrmSession,
    task: Task,
    monkeypatch: pytest.MonkeyPatch,
):
    """Test populate_zim_urls successfully populates URLs for multiple files"""
    monkeypatch.setattr(tasks_module, "INFORM_CMS", True)

    zim_id_1 = str(uuid4())
    zim_id_2 = str(uuid4())

    create_or_update_task_file(
        dbsession,
        FileCreateUpdateSchema(
            task_id=task.id,
            name="file1.zim",
            status="uploaded",
            info={"id": zim_id_1},
        ),
    )
    create_or_update_task_file(
        dbsession,
        FileCreateUpdateSchema(
            task_id=task.id,
            name="file2.zim",
            status="uploaded",
            info={"id": zim_id_2},
        ),
    )
    # File without zim_id
    create_or_update_task_file(
        dbsession,
        FileCreateUpdateSchema(
            task_id=task.id,
            name="file3.zim",
            status="uploaded",
            info={},
        ),
    )
    dbsession.flush()

    mock_response = Mock()
    mock_response.json.return_value = {
        "urls": {
            zim_id_1: [
                {
                    "kind": "view",
                    "url": "https://library.kiwix.org/viewer#file1.zim",
                    "collection": "main",
                }
            ],
            zim_id_2: [
                {
                    "kind": "download",
                    "url": "https://download.kiwix.org/zim/file2.zim",
                    "collection": "archive",
                }
            ],
        }
    }
    mock_response.raise_for_status = Mock()
    mock_requests_get.return_value = mock_response

    response = client.get(f"/v2/tasks/{task.id}")
    assert response.status_code == HTTPStatus.OK

    mock_requests_get.assert_called_once()
    call_args = mock_requests_get.call_args
    zim_ids = call_args[1]["params"]["zim_ids"]
    assert sorted(zim_ids) == sorted([zim_id_1, zim_id_2])

    data = response.json()
    assert "files" in data

    # File 1 should have URLs
    assert "file1.zim" in data["files"]
    assert len(data["files"]["file1.zim"]["zim_urls"]) == 1
    assert data["files"]["file1.zim"]["zim_urls"][0]["kind"] == "view"

    # File 2 should have URLs
    assert "file2.zim" in data["files"]
    assert len(data["files"]["file2.zim"]["zim_urls"]) == 1
    assert data["files"]["file2.zim"]["zim_urls"][0]["kind"] == "download"

    # File 3 should not have URLs (no zim_id)
    assert "file3.zim" in data["files"]
    assert data["files"]["file3.zim"]["zim_urls"] == []


@patch("zimfarm_backend.common.upload.requests.get")
def test_get_task_populate_zim_urls_cms_api_error(
    mock_requests_get: Mock,
    client: TestClient,
    dbsession: OrmSession,
    task: Task,
    monkeypatch: pytest.MonkeyPatch,
):
    """Test populate_zim_urls handles CMS API errors gracefully"""
    monkeypatch.setattr(tasks_module, "INFORM_CMS", True)

    zim_id = str(uuid4())
    create_or_update_task_file(
        dbsession,
        FileCreateUpdateSchema(
            task_id=task.id,
            name="test.zim",
            status="uploaded",
            info={"id": zim_id},
        ),
    )
    dbsession.flush()

    mock_requests_get.side_effect = requests.exceptions.RequestException(
        "CMS API unavailable"
    )

    response = client.get(f"/v2/tasks/{task.id}")
    assert response.status_code == HTTPStatus.OK

    mock_requests_get.assert_called_once()

    data = response.json()
    assert "files" in data
    assert "test.zim" in data["files"]
    # When there's an error, zim_urls should remain empty
    assert data["files"]["test.zim"]["zim_urls"] == []
