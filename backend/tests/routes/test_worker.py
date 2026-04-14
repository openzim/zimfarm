import datetime
from collections.abc import Callable
from http import HTTPStatus
from ipaddress import IPv4Address, IPv6Address
from unittest.mock import MagicMock, patch

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from zimfarm_backend.api.token import generate_access_token
from zimfarm_backend.common import getnow
from zimfarm_backend.common.enums import TaskStatus
from zimfarm_backend.common.roles import RoleEnum
from zimfarm_backend.db.models import Account, Task, Worker
from zimfarm_backend.utils.github_registry import WorkerManagerVersion


def test_get_active_workers_success(
    client: TestClient,
    access_token: str,
    create_worker: Callable[..., Worker],
    create_account: Callable[..., Account],
):
    """Test successful retrieval of active workers"""
    # Create some workers
    for i in range(30):
        create_worker(account=create_account(), name=f"test-worker-{i}")

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


@patch("zimfarm_backend.api.routes.workers.logic.get_latest_worker_manager_version")
@patch("zimfarm_backend.api.routes.workers.logic.GITHUB_TOKEN", "test_token")
def test_check_in_worker_not_found(
    mock_get_version: MagicMock,
    client: TestClient,
    access_token: str,
):
    """Test that check_in_worker creates new worker when it does not exists"""
    mock_get_version.return_value = None

    response = client.put(
        "/v2/workers/a-new-worker/check-in",
        json={
            "selfish": True,
            "cpu": 1,
            "memory": 1024,
            "disk": 2048,
            "docker_image": {
                "hash": "test-image-id",
                "created_at": "2026-03-19T11:27:59Z",
            },
            "offliners": ["mwoffliner"],
            "platforms": None,
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


@patch("zimfarm_backend.api.routes.workers.logic.get_latest_worker_manager_version")
def test_check_in_worker_deleted(
    mock_get_version: MagicMock,
    client: TestClient,
    access_token: str,
    create_worker: Callable[..., Worker],
):
    """Test that check_in_worker raises BadRequestError for deleted worker"""
    mock_get_version.return_value = None
    worker = create_worker(deleted=True)

    response = client.put(
        f"/v2/workers/{worker.name}/check-in",
        json={
            "selfish": True,
            "cpu": 1,
            "memory": 1024,
            "disk": 2048,
            "docker_image": {
                "hash": "test-image-id",
                "created_at": "2026-03-19T11:27:59Z",
            },
            "offliners": ["mwoffliner"],
            "platforms": None,
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


@patch("zimfarm_backend.api.routes.workers.logic.get_latest_worker_manager_version")
def test_check_in_worker_impersonate_account(
    mock_get_version: MagicMock,
    client: TestClient,
    access_token: str,
    create_worker: Callable[..., Worker],
    create_account: Callable[..., Account],
):
    """Test that check_in_worker raises BadRequestError for deleted worker"""
    mock_get_version.return_value = None
    worker = create_worker(account=create_account())

    response = client.put(
        f"/v2/workers/{worker.name}/check-in",
        json={
            "selfish": True,
            "cpu": 1,
            "memory": 1024,
            "disk": 2048,
            "docker_image": {
                "hash": "test-image-id",
                "created_at": "2026-03-19T11:27:59Z",
            },
            "offliners": ["mwoffliner"],
            "platforms": None,
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


@patch("zimfarm_backend.api.routes.workers.logic.get_latest_worker_manager_version")
@patch("zimfarm_backend.api.routes.workers.logic.GITHUB_TOKEN", "test_token")
def test_check_in_worker_success(
    mock_get_version: MagicMock,
    client: TestClient,
    access_token: str,
    create_worker: Callable[..., Worker],
):
    """Test successful check-in of a worker"""
    worker = create_worker()

    mock_version = WorkerManagerVersion(
        hash="sha256:8ff3888516bfd2150a5e26fea2472e296da09d2de54fc91e2256e2e17c69769c",
        created_at=datetime.datetime(2026, 3, 19, 11, 27, 59),
    )
    mock_get_version.return_value = mock_version

    response = client.put(
        f"/v2/workers/{worker.name}/check-in",
        json={
            "selfish": True,
            "cpu": 1,
            "memory": 1024,
            "disk": 2048,
            "docker_image": {
                "hash": "test-image-id",
                "created_at": "2026-03-19T11:27:59Z",
            },
            "offliners": ["mwoffliner"],
            "platforms": None,
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert "worker_manager" in data
    assert data["worker_manager"] is not None
    assert (
        data["worker_manager"]["hash"]
        == "sha256:8ff3888516bfd2150a5e26fea2472e296da09d2de54fc91e2256e2e17c69769c"
    )
    assert "created_at" in data["worker_manager"]


def test_get_worker_metrics_no_tasks(client: TestClient, worker: Worker):
    """Worker metrics should be zero when no tasks exist."""
    response = client.get(f"/v2/workers/{worker.name}")
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

    response = client.get(f"/v2/workers/{worker.name}")
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
        [RoleEnum.PROCESSOR, {"general": None}, False, HTTPStatus.FORBIDDEN],
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
    create_account: Callable[..., Account],
    *,
    permission: RoleEnum,
    contexts: dict[str, IPv4Address | IPv6Address | None],
    expected_status: HTTPStatus,
    deleted: bool,
):
    """Test successful update of a worker's context"""
    account = create_account(permission=permission)
    worker = create_worker(account=account, deleted=deleted)

    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )

    response = client.put(
        f"/v2/workers/{worker.name}",
        json={"contexts": contexts},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == expected_status


def test_update_worker_context_not_found(
    client: TestClient,
    create_worker: Callable[..., Worker],
    create_account: Callable[..., Account],
):
    account = create_account(permission=RoleEnum.ADMIN)
    create_worker(account=account, deleted=False)

    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )

    response = client.put(
        "/v2/workers/non-existent",
        json={"contexts": {"priority": "127.0.0.1", "general": None}},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_update_worker_context_no_payload(
    client: TestClient,
    create_worker: Callable[..., Worker],
    create_account: Callable[..., Account],
):
    account = create_account(permission=RoleEnum.ADMIN)
    worker = create_worker(account=account, deleted=False)

    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )

    response = client.put(
        f"/v2/workers/{worker.name}",
        json={},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_list_worker_keys(client: TestClient, account: Account, worker: Worker):
    """Test listing a workers' SSH keys"""
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    url = f"/v2/workers/{worker.name}/keys"
    response = client.get(url, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == HTTPStatus.OK

    response_json = response.json()
    assert "meta" in response_json
    assert "items" in response_json
    assert len(response_json["items"]) == 1
    key = response_json["items"][0]
    assert set(key.keys()) == {
        "name",
        "fingerprint",
        "key",
        "type",
        "added",
    }


def test_list_worker_keys_forbidden(
    client: TestClient, create_account: Callable[..., Account], worker: Worker
):
    """Test listing a workers' SSH keys without permission"""
    account = create_account(permission="editor")
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    url = f"/v2/workers/{worker.name}/keys"
    response = client.get(url, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_create_worker_key(client: TestClient, account: Account, worker: Worker):
    """Test creating a new SSH key for a worker"""
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    new_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = new_key.public_key()
    rsa_public_key_data = public_key.public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH,
    )
    url = f"/v2/workers/{worker.name}/keys"
    # generated keys don't come with hostname but backend requires it
    key_data = {"key": rsa_public_key_data.decode(encoding="ascii") + " test@localhost"}
    response = client.post(
        url, headers={"Authorization": f"Bearer {access_token}"}, json=key_data
    )
    assert response.status_code == HTTPStatus.OK

    response_json = response.json()
    assert response_json["key"] == key_data["key"]
    assert "name" in response_json
    assert "fingerprint" in response_json
    assert "type" in response_json
    assert "added" in response_json


def test_create_worker_key_invalid(
    client: TestClient, account: Account, worker: Worker
):
    """Test creating an invalid SSH key"""
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    url = f"/v2/workers/{worker.name}/keys"
    key_data = {"key": "invalid-key xxxxxxx test@localhost"}
    response = client.post(
        url, headers={"Authorization": f"Bearer {access_token}"}, json=key_data
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_create_worker_key_duplicate(
    client: TestClient, account: Account, worker: Worker
):
    """Test creating a duplicate SSH key"""
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    url = f"/v2/workers/{worker.name}/keys"
    key_data = {"key": worker.ssh_keys[0].key}
    response = client.post(
        url, headers={"Authorization": f"Bearer {access_token}"}, json=key_data
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_get_worker_key(client: TestClient, account: Account, worker: Worker):
    """Test getting a specific SSH key"""
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    fingerprint = worker.ssh_keys[0].fingerprint
    url = f"/v2/workers/{worker.name}/keys/{fingerprint}"
    response = client.get(url, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == HTTPStatus.OK

    response_json = response.json()
    assert response_json["worker_name"] == worker.name
    assert response_json["key"] == worker.ssh_keys[0].key
    assert response_json["name"] == worker.ssh_keys[0].name
    assert response_json["type"] == worker.ssh_keys[0].type


def test_get_worker_key_not_found(client: TestClient, account: Account, worker: Worker):
    """Test getting a non-existent SSH key"""
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    url = f"/v2/workers/{worker.name}/keys/non-existent-fingerprint"
    response = client.get(url, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_delete_worker_key_different_owner(
    client: TestClient,
    account: Account,
    create_worker: Callable[..., Worker],
    create_account: Callable[..., Account],
):
    """Test deleting an SSH key for a worker belonging to a different account"""
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    worker = create_worker(account=create_account(username="newuser"))
    fingerprint = worker.ssh_keys[0].fingerprint
    url = f"/v2/workers/{worker.name}/keys/{fingerprint}"
    response = client.delete(url, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == HTTPStatus.NO_CONTENT

    # Verify the key is deleted
    response = client.get(url, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_delete_worker_key(
    client: TestClient,
    create_worker: Callable[..., Worker],
    create_account: Callable[..., Account],
):
    """Test deleting an SSH key for a worker even though owner doesn't have
    ssh permissions"""
    account = create_account(permission=RoleEnum.PROCESSOR)
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    worker = create_worker(account=account)
    fingerprint = worker.ssh_keys[0].fingerprint
    url = f"/v2/workers/{worker.name}/keys/{fingerprint}"
    response = client.delete(url, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == HTTPStatus.NO_CONTENT

    # Verify the key is deleted
    response = client.get(url, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_delete_account_key_forbidden(
    client: TestClient, create_account: Callable[..., Account], worker: Worker
):
    """Test deleting another account's SSH key without permission"""
    account = create_account(permission="editor")
    url = f"/v2/workers/{worker.name}/keys/some-fingerprint"
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    response = client.delete(url, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == HTTPStatus.FORBIDDEN
