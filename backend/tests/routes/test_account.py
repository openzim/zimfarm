from collections.abc import Callable
from http import HTTPStatus

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.api.token import generate_access_token
from zimfarm_backend.common import getnow
from zimfarm_backend.db.models import Account


def test_list_accounts_no_auth(client: TestClient):
    response = client.get("/v2/accounts")
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.num_accounts(5)
def test_list_accounts_no_param(client: TestClient, accounts: list[Account]):
    account = accounts[0]
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    response = client.get(
        "/v2/accounts", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == HTTPStatus.OK

    response_json = response.json()
    assert "items" in response_json
    assert "meta" in response_json
    assert response_json["meta"]["count"] == 5
    assert len(response_json["items"]) == len(accounts)
    for item in response_json["items"]:
        item_keys = item.keys()
        assert "username" in item_keys
        assert "id" in item_keys
        assert "display_name" in item_keys
        assert "role" in item_keys
        assert "scope" in item_keys
        assert "idp_sub" in item_keys


@pytest.mark.parametrize("skip, limit, expected", [(0, 1, 1), (1, 10, 4), (0, 100, 5)])
@pytest.mark.num_accounts(5)
def test_list_accounts_with_param(
    client: TestClient,
    accounts: list[Account],
    skip: int,
    limit: int,
    expected: int,
):
    account = accounts[0]
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    url = f"/v2/accounts?skip={skip}&limit={limit}"
    response = client.get(url, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == HTTPStatus.OK

    response_json = response.json()
    assert "items" in response_json
    assert "meta" in response_json
    assert response_json["meta"]["count"] == 5
    assert len(response_json["items"]) == expected


@pytest.mark.num_accounts(10)
def test_skip_deleted_accounts(
    dbsession: OrmSession,
    client: TestClient,
    accounts: list[Account],
):
    account = accounts[0]
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    for i in range(1, len(accounts)):
        accounts[i].deleted = True
        dbsession.add(accounts[i])
        dbsession.flush()

    url = f"/v2/accounts?skip={0}&limit={100}"
    response = client.get(url, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == HTTPStatus.OK

    response_json = response.json()
    assert "items" in response_json
    assert "meta" in response_json
    assert response_json["meta"]["count"] == 1  # skip deleted accounts
    assert len(response_json["items"]) == 1


def test_get_account_by_username(client: TestClient, account: Account):
    url = f"/v2/accounts/{account.username}"
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    response = client.get(url, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == HTTPStatus.OK

    response_json = response.json()
    assert response_json["username"] == account.username


def test_get_account_by_username_not_found(
    client: TestClient,
    account: Account,
):
    url = f"/v2/accounts/{account.username}1"
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    response = client.get(url, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_create_account(client: TestClient, account: Account):
    url = "/v2/accounts/"
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    response = client.post(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "username": "test",
            "password": "test",
            "role": "admin",
        },
    )
    assert response.status_code == HTTPStatus.OK


def test_create_account_duplicate(client: TestClient, account: Account):
    url = "/v2/accounts/"
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    response = client.post(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "username": account.username,
            "password": "test",
            "role": "admin",
        },
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_list_account_keys(client: TestClient, account: Account):
    """Test listing an account's SSH keys"""
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    url = f"/v2/accounts/{account.username}/keys"
    response = client.get(url, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == HTTPStatus.OK

    response_json = response.json()
    assert "ssh_keys" in response_json
    assert len(response_json["ssh_keys"]) == 1
    key = response_json["ssh_keys"][0]
    assert set(key.keys()) == {
        "name",
        "fingerprint",
        "key",
        "type",
        "added",
    }


@pytest.mark.num_accounts(2, permission="editor")
def test_list_account_keys_forbidden(client: TestClient, accounts: list[Account]):
    """Test listing another account's SSH keys without permission"""
    account = accounts[0]
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    url = f"/v2/accounts/{accounts[1].username}/keys"
    response = client.get(url, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_create_account_key(client: TestClient, account: Account):
    """Test creating a new SSH key for an account"""
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
    url = f"/v2/accounts/{account.username}/keys"
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


def test_create_account_key_invalid(client: TestClient, account: Account):
    """Test creating an invalid SSH key"""
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    url = f"/v2/accounts/{account.username}/keys"
    key_data = {"key": "invalid-key xxxxxxx test@localhost"}
    response = client.post(
        url, headers={"Authorization": f"Bearer {access_token}"}, json=key_data
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_create_account_key_duplicate(client: TestClient, account: Account):
    """Test creating a duplicate SSH key"""
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    url = f"/v2/accounts/{account.username}/keys"
    key_data = {"key": account.ssh_keys[0].key}
    response = client.post(
        url, headers={"Authorization": f"Bearer {access_token}"}, json=key_data
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_get_account_key(client: TestClient, account: Account):
    """Test getting a specific SSH key"""
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    fingerprint = account.ssh_keys[0].fingerprint
    url = f"/v2/accounts/{account.username}/keys/{fingerprint}"
    response = client.get(url, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == HTTPStatus.OK

    response_json = response.json()
    assert response_json["username"] == account.username
    assert response_json["key"] == account.ssh_keys[0].key
    assert response_json["name"] == account.ssh_keys[0].name
    assert response_json["type"] == account.ssh_keys[0].type


def test_get_account_key_not_found(client: TestClient, account: Account):
    """Test getting a non-existent SSH key"""
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    url = f"/v2/accounts/{account.username}/keys/non-existent-fingerprint"
    response = client.get(url, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_delete_account_key(client: TestClient, account: Account):
    """Test deleting an account's SSH key"""
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    fingerprint = account.ssh_keys[0].fingerprint
    url = f"/v2/accounts/{account.username}/keys/{fingerprint}"
    response = client.delete(url, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == HTTPStatus.NO_CONTENT

    # Verify the key is deleted
    response = client.get(url, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.num_accounts(2, permission="editor")
def test_delete_account_key_forbidden(client: TestClient, accounts: list[Account]):
    """Test deleting another account's SSH key without permission"""
    account = accounts[0]
    url = f"/v2/accounts/{accounts[1].username}/keys/some-fingerprint"
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    response = client.delete(url, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_update_account_role(client: TestClient, account: Account):
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    url = f"/v2/accounts/{account.username}"
    response = client.patch(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        json={"role": "editor"},
    )
    assert response.status_code == HTTPStatus.NO_CONTENT

    # Verify the role is updated and scope is None
    response = client.get(url, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["username"] == account.username
    assert data["role"] == "editor"


def test_update_account_scope(client: TestClient, account: Account):
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    url = f"/v2/accounts/{account.username}"
    response = client.patch(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        json={"scope": {"recipes": {"read": True}}},
    )
    assert response.status_code == HTTPStatus.NO_CONTENT

    # Verify the role is updated and scope is None
    response = client.get(url, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["username"] == account.username


def test_update_account_role_and_scope(client: TestClient, account: Account):
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    url = f"/v2/accounts/{account.username}"
    response = client.patch(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        json={"scope": {"recipes": {"read": True}}, "role": "editor"},
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.num_accounts(2, permission="editor")
def test_update_account_password_wrong_permission(
    client: TestClient, accounts: list[Account]
):
    """Test updating an account's password without permission"""
    account = accounts[0]
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    response = client.patch(
        f"/v2/accounts/{accounts[1].username}/password",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"current": "test", "new": "test2"},
    )
    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.parametrize(
    "current,new,expected",
    [
        pytest.param(
            "invalid", "test2", HTTPStatus.BAD_REQUEST, id="invalid-current-password"
        ),
        pytest.param(None, "test2", HTTPStatus.BAD_REQUEST, id="no-current-password"),
        pytest.param(
            "testpassword", "test2", HTTPStatus.NO_CONTENT, id="change-password"
        ),
        pytest.param(
            "testpassword", None, HTTPStatus.NO_CONTENT, id="set-password-to-None"
        ),
    ],
)
def test_update_account_own_password(
    client: TestClient,
    create_account: Callable[..., Account],
    current: str,
    new: str,
    expected: HTTPStatus,
):
    """Test updating an account's own password"""
    account = create_account(permission="editor")
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    response = client.patch(
        f"/v2/accounts/{account.username}/password",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"current": current, "new": new},
    )
    assert response.status_code == expected
