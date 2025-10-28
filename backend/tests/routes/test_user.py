from http import HTTPStatus

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common import getnow
from zimfarm_backend.db.models import User
from zimfarm_backend.utils.token import generate_access_token


def test_list_users_no_auth(client: TestClient):
    response = client.get("/v2/users")
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.num_users(5)
def test_list_users_no_param(client: TestClient, users: list[User]):
    user = users[0]
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        scope=user.scope,
        email=user.email,
    )
    response = client.get(
        "/v2/users", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == HTTPStatus.OK

    response_json = response.json()
    assert "items" in response_json
    assert "meta" in response_json
    assert response_json["meta"]["count"] == 5
    assert len(response_json["items"]) == len(users)
    for item in response_json["items"]:
        assert set(item.keys()) == {"username", "email", "role", "scope"}


@pytest.mark.parametrize("skip, limit, expected", [(0, 1, 1), (1, 10, 4), (0, 100, 5)])
@pytest.mark.num_users(5)
def test_list_users_with_param(
    client: TestClient,
    users: list[User],
    skip: int,
    limit: int,
    expected: int,
):
    user = users[0]
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        scope=user.scope,
        email=user.email,
    )
    url = f"/v2/users?skip={skip}&limit={limit}"
    response = client.get(url, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == HTTPStatus.OK

    response_json = response.json()
    assert "items" in response_json
    assert "meta" in response_json
    assert response_json["meta"]["count"] == 5
    assert len(response_json["items"]) == expected


@pytest.mark.num_users(10)
def test_skip_deleted_users(
    dbsession: OrmSession,
    client: TestClient,
    users: list[User],
):
    user = users[0]
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        scope=user.scope,
        email=user.email,
    )
    for i in range(1, len(users)):
        users[i].deleted = True
        dbsession.add(users[i])
        dbsession.flush()

    url = f"/v2/users?skip={0}&limit={100}"
    response = client.get(url, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == HTTPStatus.OK

    response_json = response.json()
    assert "items" in response_json
    assert "meta" in response_json
    assert response_json["meta"]["count"] == 1  # skip deleted users
    assert len(response_json["items"]) == 1


def test_get_user_by_username(client: TestClient, user: User):
    url = f"/v2/users/{user.username}"
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        scope=user.scope,
        email=user.email,
    )
    response = client.get(url, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == HTTPStatus.OK

    response_json = response.json()
    assert response_json["username"] == user.username


def test_get_user_by_username_not_found(
    client: TestClient,
    user: User,
):
    url = f"/v2/users/{user.username}1"
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        scope=user.scope,
        email=user.email,
    )
    response = client.get(url, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_patch_user_email(client: TestClient, user: User):
    url = f"/v2/users/{user.username}"
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        scope=user.scope,
        email=user.email,
    )
    response = client.patch(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        json={"email": "test@test.com"},
    )
    assert response.status_code == HTTPStatus.NO_CONTENT


@pytest.mark.num_users(2)
def test_delete_user(client: TestClient, users: list[User]):
    user = users[0]
    url = f"/v2/users/{user.username}"
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        scope=user.scope,
        email=user.email,
    )
    response = client.delete(url, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == HTTPStatus.NO_CONTENT

    # We still shouldn't be able to create a user with same username
    user = users[1]
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        scope=user.scope,
        email=user.email,
    )
    response = client.post(
        "/v2/users",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "username": users[0].username,
            "email": "test@test.com",
            "password": "test",
            "role": "admin",
        },
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_create_user(client: TestClient, user: User):
    url = "/v2/users/"
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        scope=user.scope,
        email=user.email,
    )
    response = client.post(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "username": "test",
            "email": "test@test.com",
            "password": "test",
            "role": "admin",
        },
    )
    assert response.status_code == HTTPStatus.OK


def test_create_user_duplicate(client: TestClient, user: User):
    url = "/v2/users/"
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        scope=user.scope,
        email=user.email,
    )
    response = client.post(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "username": user.username,
            "email": "test@test.com",
            "password": "test",
            "role": "admin",
        },
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_list_user_keys(client: TestClient, user: User):
    """Test listing a user's SSH keys"""
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        scope=user.scope,
        email=user.email,
    )
    url = f"/v2/users/{user.username}/keys"
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


@pytest.mark.num_users(2, permission="editor")
def test_list_user_keys_unauthorized(client: TestClient, users: list[User]):
    """Test listing another user's SSH keys without permission"""
    user = users[0]
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        scope=user.scope,
        email=user.email,
    )
    url = f"/v2/users/{users[1].username}/keys"
    response = client.get(url, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_create_user_key(client: TestClient, user: User):
    """Test creating a new SSH key for a user"""
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        scope=user.scope,
        email=user.email,
    )
    new_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = new_key.public_key()
    rsa_public_key_data = public_key.public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH,
    )
    url = f"/v2/users/{user.username}/keys"
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


def test_create_user_key_invalid(client: TestClient, user: User):
    """Test creating an invalid SSH key"""
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        scope=user.scope,
        email=user.email,
    )
    url = f"/v2/users/{user.username}/keys"
    key_data = {"key": "invalid-key xxxxxxx test@localhost"}
    response = client.post(
        url, headers={"Authorization": f"Bearer {access_token}"}, json=key_data
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_create_user_key_duplicate(client: TestClient, user: User):
    """Test creating a duplicate SSH key"""
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        scope=user.scope,
        email=user.email,
    )
    url = f"/v2/users/{user.username}/keys"
    key_data = {"key": user.ssh_keys[0].key}
    response = client.post(
        url, headers={"Authorization": f"Bearer {access_token}"}, json=key_data
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_get_user_key(client: TestClient, user: User):
    """Test getting a specific SSH key"""
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        scope=user.scope,
        email=user.email,
    )
    fingerprint = user.ssh_keys[0].fingerprint
    url = f"/v2/users/{user.username}/keys/{fingerprint}"
    response = client.get(url, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == HTTPStatus.OK

    response_json = response.json()
    assert response_json["username"] == user.username
    assert response_json["key"] == user.ssh_keys[0].key
    assert response_json["name"] == user.ssh_keys[0].name
    assert response_json["type"] == user.ssh_keys[0].type


def test_get_user_key_not_found(client: TestClient, user: User):
    """Test getting a non-existent SSH key"""
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        scope=user.scope,
        email=user.email,
    )
    url = f"/v2/users/{user.username}/keys/non-existent-fingerprint"
    response = client.get(url, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_delete_user_key(client: TestClient, user: User):
    """Test deleting a user's SSH key"""
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        scope=user.scope,
        email=user.email,
    )
    fingerprint = user.ssh_keys[0].fingerprint
    url = f"/v2/users/{user.username}/keys/{fingerprint}"
    response = client.delete(url, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == HTTPStatus.NO_CONTENT

    # Verify the key is deleted
    response = client.get(url, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.num_users(2, permission="editor")
def test_delete_user_key_unauthorized(client: TestClient, users: list[User]):
    """Test deleting another user's SSH key without permission"""
    user = users[0]
    url = f"/v2/users/{users[1].username}/keys/some-fingerprint"
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        scope=user.scope,
        email=user.email,
    )
    response = client.delete(url, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_update_user_role(client: TestClient, user: User):
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        scope=user.scope,
        email=user.email,
    )
    url = f"/v2/users/{user.username}"
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
    assert data["username"] == user.username
    assert data["role"] == "editor"


def test_update_user_scope(client: TestClient, user: User):
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        scope=user.scope,
        email=user.email,
    )
    url = f"/v2/users/{user.username}"
    response = client.patch(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        json={"scope": {"schedules": {"read": True}}},
    )
    assert response.status_code == HTTPStatus.NO_CONTENT

    # Verify the role is updated and scope is None
    response = client.get(url, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["username"] == user.username


def test_update_user_role_and_scope(client: TestClient, user: User):
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        scope=user.scope,
        email=user.email,
    )
    url = f"/v2/users/{user.username}"
    response = client.patch(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        json={"scope": {"schedules": {"read": True}}, "role": "editor"},
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.num_users(2, permission="editor")
def test_update_user_password(client: TestClient, users: list[User]):
    """Test updating a user's password without permission"""
    user = users[0]
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        scope=user.scope,
        email=user.email,
    )
    response = client.patch(
        f"/v2/users/{users[1].username}/password",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"current": "test", "new": "test2"},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.parametrize(
    "current,new,expected",
    [
        ("invalid", "test2", HTTPStatus.BAD_REQUEST),
        (None, "test2", HTTPStatus.BAD_REQUEST),
        ("testpassword", "test2", HTTPStatus.NO_CONTENT),
    ],
)
@pytest.mark.num_users(1, permission="editor")
def test_update_user_password_invalid(
    client: TestClient, users: list[User], current: str, new: str, expected: HTTPStatus
):
    """Test updating a user's password with an invalid current password"""
    user = users[0]
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        scope=user.scope,
        email=user.email,
    )
    response = client.patch(
        f"/v2/users/{user.username}/password",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"current": current, "new": new},
    )
    assert response.status_code == expected
