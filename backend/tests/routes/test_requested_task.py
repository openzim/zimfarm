from collections.abc import Callable
from http import HTTPStatus
from ipaddress import IPv4Address

import pytest
from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common import getnow
from zimfarm_backend.common.roles import RoleEnum
from zimfarm_backend.common.schemas.models import ResourcesSchema, ScheduleConfigSchema
from zimfarm_backend.db.models import RequestedTask, Schedule, User, Worker
from zimfarm_backend.db.worker import get_worker
from zimfarm_backend.routes.requested_tasks import logic
from zimfarm_backend.utils.token import generate_access_token


def test_create_request_task_no_permission(
    client: TestClient,
    create_user: Callable[..., User],
):
    """Test that create_request_task raises ForbiddenError without permission"""
    user = create_user(permission=RoleEnum.PROCESSOR)
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        email=user.email,
        scope=user.scope,
    )

    response = client.post(
        "/v2/requested-tasks",
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
        "/v2/requested-tasks",
        json={"schedule_names": [schedule.name], "worker": worker.name, "priority": 1},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.parametrize(
    "worker_offliners,worker_contexts,worker_resource,schedule_resource,schedule_context,expected_status_code",
    [
        # our schedule is always going to be an mwoffliner
        pytest.param(
            ["mwoffliner"],
            ["general"],  # worker context
            ResourcesSchema(cpu=1, memory=1, disk=1),
            ResourcesSchema(cpu=1, memory=1, disk=1),
            "",  # schedule_context
            HTTPStatus.OK,
            id="worker-matches-schedule",
        ),
        pytest.param(
            ["mwoffliner"],
            [],
            ResourcesSchema(cpu=2, memory=2, disk=2),
            ResourcesSchema(cpu=1, memory=1, disk=1),
            "",
            HTTPStatus.OK,
            id="worker-exceeds-schedule",
        ),
        pytest.param(
            ["gutenberg"],
            [],
            ResourcesSchema(cpu=1, memory=1, disk=1),
            ResourcesSchema(cpu=1, memory=1, disk=1),
            "",
            HTTPStatus.BAD_REQUEST,
            id="worker-with-different-offliner",
        ),
        pytest.param(
            ["mwoffliner"],
            [],
            ResourcesSchema(cpu=1, memory=1, disk=1),
            ResourcesSchema(cpu=2, memory=1, disk=1),
            "",
            HTTPStatus.BAD_REQUEST,
            id="worker-does-not-match-schedule-cpu",
        ),
        pytest.param(
            ["mwoffliner"],
            [],
            ResourcesSchema(cpu=1, memory=1, disk=1),
            ResourcesSchema(cpu=1, memory=2, disk=1),
            "",
            HTTPStatus.BAD_REQUEST,
            id="worker-does-not-match-schedule-memory",
        ),
        pytest.param(
            ["mwoffliner"],
            [],
            ResourcesSchema(cpu=1, memory=1, disk=1),
            ResourcesSchema(cpu=1, memory=1, disk=2),
            "",
            HTTPStatus.BAD_REQUEST,
            id="worker-does-not-match-schedule-disk",
        ),
        pytest.param(
            ["mwoffliner"],
            ["general"],  # worker context
            ResourcesSchema(cpu=1, memory=1, disk=1),
            ResourcesSchema(cpu=1, memory=1, disk=1),
            "priority",  # schedule_context
            HTTPStatus.BAD_REQUEST,
            id="worker-context-does-not-match-schedule",
        ),
    ],
)
def test_create_request_task_success(
    client: TestClient,
    access_token: str,
    worker_offliners: list[str],
    worker_contexts: list[str],
    worker_resource: ResourcesSchema,
    schedule_resource: ResourcesSchema,
    create_worker: Callable[..., Worker],
    create_schedule: Callable[..., Schedule],
    create_schedule_config: Callable[..., ScheduleConfigSchema],
    schedule_context: str,
    expected_status_code: int,
):
    worker = create_worker(
        cpu=worker_resource.cpu,
        memory=worker_resource.memory,
        disk=worker_resource.disk,
        name="random-worker",
        offliners=worker_offliners,
        contexts=worker_contexts,
    )
    schedule = create_schedule(
        schedule_config=create_schedule_config(
            cpu=schedule_resource.cpu,
            memory=schedule_resource.memory,
            disk=schedule_resource.disk,
        ),
        context=schedule_context,
    )
    """Test successful creation of requested task"""
    response = client.post(
        "/v2/requested-tasks",
        json={"schedule_names": [schedule.name], "worker": worker.name, "priority": 1},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == expected_status_code


def test_get_requested_tasks_success(
    client: TestClient,
    access_token: str,
    create_requested_task: Callable[..., RequestedTask],
    worker: Worker,
):
    """Test successful retrieval of requested tasks"""
    # Create some requested tasks
    for i in range(30):
        create_requested_task(worker=worker, schedule_name=f"test_schedule_{i}")

    response = client.get(
        "/v2/requested-tasks?limit=5&worker_name=test-worker",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert "items" in data
    assert "meta" in data
    assert "count" in data["meta"]
    assert data["meta"]["count"] == 30
    assert len(data["items"]) == 5


def test_get_requested_tasks_for_worker_scheduler_disabled(
    client: TestClient,
    access_token: str,
    worker: Worker,
    monkeypatch: MonkeyPatch,
):
    """Test that response is empty when scheduler is disabled"""
    monkeypatch.setattr(logic, "ENABLED_SCHEDULER", False)

    response = client.get(
        f"/v2/requested-tasks/worker?worker_name={worker.name}&avail_cpu={worker.cpu}&avail_memory={worker.memory}&avail_disk={worker.disk}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-Forwarded-For": "127.0.0.1",
        },
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert "items" in data
    assert "meta" in data
    assert data["meta"]["count"] == 0
    assert len(data["items"]) == 0


def test_get_requested_tasks_for_worker_worker_not_found(
    client: TestClient,
    access_token: str,
):
    response = client.get(
        "/v2/requested-tasks/worker?worker_name=nonexistent-worker&avail_cpu=2&avail_memory=1024&avail_disk=1024",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-Forwarded-For": "127.0.0.1",
        },
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_get_requested_tasks_for_worker_success_no_ip_change(
    client: TestClient,
    access_token: str,
    dbsession: OrmSession,
    create_requested_task: Callable[..., RequestedTask],
    worker: Worker,
    monkeypatch: MonkeyPatch,
):
    """Test successful retrieval of requested tasks for a worker with no IP change"""
    # Create a task for the worker
    create_requested_task(worker=worker)

    # Mock record_ip_change to avoid external service calls
    def mock_record_ip_change(session: OrmSession, worker_name: str) -> None:
        pass

    monkeypatch.setattr(
        logic,
        "record_ip_change",
        mock_record_ip_change,
    )

    worker.last_ip = IPv4Address("127.0.0.1")
    dbsession.add(worker)
    dbsession.flush()

    response = client.get(
        f"/v2/requested-tasks/worker?worker_name={worker.name}&avail_cpu={worker.cpu}&avail_memory={worker.memory}&avail_disk={worker.disk}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-Forwarded-For": str(worker.last_ip) if worker.last_ip else "127.0.0.1",
        },
    )
    assert response.status_code == HTTPStatus.OK
    dbsession.expire(worker)
    worker = get_worker(dbsession, worker_name=worker.name)
    assert worker.last_ip == IPv4Address("127.0.0.1")


def test_get_requested_tasks_for_worker_success_with_ip_change(
    client: TestClient,
    access_token: str,
    create_requested_task: Callable[..., RequestedTask],
    worker: Worker,
    dbsession: OrmSession,
    monkeypatch: MonkeyPatch,
):
    """Test successful retrieval of requested tasks for a worker with IP change"""
    # Create a task for the worker
    create_requested_task(worker=worker)

    # Mock record_ip_change to avoid external service calls
    def mock_record_ip_change(session: OrmSession, worker_name: str) -> None:
        pass

    monkeypatch.setattr(
        logic,
        "record_ip_change",
        mock_record_ip_change,
    )
    monkeypatch.setattr(logic, "USES_WORKERS_IPS_WHITELIST", True)

    new_ip = "192.168.1.100"
    response = client.get(
        f"/v2/requested-tasks/worker?worker_name={worker.name}&avail_cpu={worker.cpu}&avail_memory={worker.memory}&avail_disk={worker.disk}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-Forwarded-For": new_ip,
        },
    )
    assert response.status_code == HTTPStatus.OK
    dbsession.expire(worker)
    worker = get_worker(dbsession, worker_name=worker.name)
    assert str(worker.last_ip) == new_ip


def test_get_requested_tasks_for_worker_ip_change_exception(
    client: TestClient,
    access_token: str,
    create_requested_task: Callable[..., RequestedTask],
    worker: Worker,
    dbsession: OrmSession,
    monkeypatch: MonkeyPatch,
):
    """Test that get_requested_tasks_for_worker handles IP change exceptions properly"""
    # Create a task for the worker
    create_requested_task(worker=worker)

    # Mock record_ip_change to raise an exception
    def mock_record_ip_change(session: OrmSession, worker_name: str) -> None:  #  noqa
        raise Exception("Wasabi connection failed")

    monkeypatch.setattr(
        logic,
        "record_ip_change",
        mock_record_ip_change,
    )
    monkeypatch.setattr(logic, "USES_WORKERS_IPS_WHITELIST", True)

    new_ip = "192.168.1.100"
    response = client.get(
        f"/v2/requested-tasks/worker?worker_name={worker.name}&avail_cpu={worker.cpu}&avail_memory={worker.memory}&avail_disk={worker.disk}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-Forwarded-For": new_ip,
        },
    )
    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE
    # Even though exception was raised, assert that the new ip was recorded
    dbsession.expire(worker)
    worker = get_worker(dbsession, worker_name=worker.name)
    assert str(worker.last_ip) == new_ip


def test_get_requested_tasks_for_worker_no_tasks_available(
    client: TestClient,
    access_token: str,
    worker: Worker,
    monkeypatch: MonkeyPatch,
):
    # Mock record_ip_change to avoid external service calls
    def mock_record_ip_change(session: OrmSession, worker_name: str) -> None:
        pass

    monkeypatch.setattr(
        logic,
        "record_ip_change",
        mock_record_ip_change,
    )

    response = client.get(
        f"/v2/requested-tasks/worker?worker_name={worker.name}&avail_cpu={worker.cpu}&avail_memory={worker.memory}&avail_disk={worker.disk}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-Forwarded-For": "127.0.0.1",
        },
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert "items" in data
    assert "meta" in data
    assert data["meta"]["count"] == 0
    assert len(data["items"]) == 0


@pytest.mark.parametrize("hide_secrets", ["true", "false"])
def test_get_requested_task_success(
    client: TestClient,
    access_token: str,
    requested_task: RequestedTask,
    hide_secrets: str,
):
    """Test successful retrieval of a single requested task"""
    response = client.get(
        f"/v2/requested-tasks/{requested_task.id}?hide_secrets={hide_secrets}",
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


def test_update_requested_task_no_permission(
    client: TestClient,
    access_token: str,
    requested_task: RequestedTask,
    create_user: Callable[..., User],
):
    """Test that update_requested_task raises ForbiddenError without permission"""
    user = create_user(permission=RoleEnum.EDITOR)
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        email=user.email,
        scope=user.scope,
    )

    response = client.patch(
        f"/v2/requested-tasks/{requested_task.id}",
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
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        email=user.email,
        scope=user.scope,
    )

    response = client.patch(
        f"/v2/requested-tasks/{requested_task.id}",
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
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        email=user.email,
        scope=user.scope,
    )

    response = client.delete(
        f"/v2/requested-tasks/{requested_task.id}",
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
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        email=user.email,
        scope=user.scope,
    )

    response = client.delete(
        f"/v2/requested-tasks/{requested_task.id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["deleted"] == 1
