import base64
import datetime
import uuid
from collections.abc import Callable
from http import HTTPStatus

import pytest
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.api.token import generate_access_token
from zimfarm_backend.common import getnow
from zimfarm_backend.common.roles import RoleEnum
from zimfarm_backend.db.models import User
from zimfarm_backend.db.refresh_token import create_refresh_token, expire_refresh_tokens
from zimfarm_backend.utils.cryptography import (
    sign_message_with_rsa_key,
)


@pytest.mark.num_users(1)
def test_auth_with_credentials(client: TestClient, users: list[User]):
    response = client.post(
        "/v2/auth/authorize",
        json={"username": users[0].username, "password": "testpassword"},
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["access_token"] is not None
    assert data["refresh_token"] is not None
    assert (
        datetime.datetime.fromisoformat(data["expires_time"]).replace(tzinfo=None)
        > getnow()
    )


def test_auth_with_credentials_invalid_credentials(client: TestClient):
    response = client.post(
        "/v2/auth/authorize",
        json={"username": "testuser", "password": "invalidpassword"},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.num_users(1)
def test_refresh_access_token(
    client: TestClient, users: list[User], dbsession: OrmSession
):
    token = create_refresh_token(session=dbsession, user_id=users[0].id)
    response = client.post(
        "/v2/auth/refresh",
        json={"refresh_token": str(token.token)},
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["access_token"] is not None
    assert data["refresh_token"] is not None
    assert (
        datetime.datetime.fromisoformat(data["expires_time"]).replace(tzinfo=None)
        > getnow()
    )


def test_refresh_access_token_invalid_token(client: TestClient):
    response = client.post(
        "/v2/auth/refresh",
        json={"refresh_token": str(uuid.uuid4())},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.num_users(1)
def test_refresh_access_token_expired_token(
    client: TestClient, users: list[User], dbsession: OrmSession
):
    token = create_refresh_token(session=dbsession, user_id=users[0].id)
    expire_refresh_tokens(
        session=dbsession,
        expire_time=getnow() + datetime.timedelta(seconds=1),
    )
    response = client.post(
        "/v2/auth/refresh",
        json={"refresh_token": str(token.token)},
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["access_token"] is not None
    assert data["refresh_token"] is not None
    assert (
        datetime.datetime.fromisoformat(data["expires_time"]).replace(tzinfo=None)
        > getnow()
    )


@pytest.mark.parametrize(
    ["datetime_str", "expected_status", "expected_response_contents"],
    [
        (
            datetime.datetime.fromtimestamp(0, tz=datetime.UTC)
            .replace(tzinfo=None)
            .isoformat(),
            HTTPStatus.UNAUTHORIZED,
            [],
        ),
        (
            "hello",
            HTTPStatus.BAD_REQUEST,
            [],
        ),
        (
            # Before CI fully sets up, default timer has expired, so, add
            # additional 5 minutes
            (getnow() + datetime.timedelta(minutes=5)).isoformat(),
            HTTPStatus.OK,
            ["access_token", "token_type", "expires_time"],
        ),
    ],
)
@pytest.mark.num_users(1)
def test_authenticate_user(
    client: TestClient,
    users: list[User],
    rsa_private_key: RSAPrivateKey,
    datetime_str: str,
    expected_status: int,
    expected_response_contents: list[str],
):
    message = f"{users[0].username}:{datetime_str}"
    signature = sign_message_with_rsa_key(
        rsa_private_key, bytes(message, encoding="ascii")
    )
    x_sshauth_signature = base64.b64encode(signature).decode()
    response = client.post(
        "/v2/auth/ssh-authorize",
        headers={
            "Content-type": "application/json",
            "X-SSHAuth-Message": message,
            "X-SSHAuth-Signature": x_sshauth_signature,
        },
    )
    assert response.status_code == expected_status
    data = response.text
    for content in expected_response_contents:
        assert content in data


def test_authentication_token(
    client: TestClient,
    create_user: Callable[..., User],
):
    """Test that authentication token is valid."""
    user = create_user(permission=RoleEnum.PROCESSOR)
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
    )

    response = client.get(
        "/v2/auth/test",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.NO_CONTENT


def test_get_current_user(client: TestClient, user: User):
    url = "/v2/auth/me"
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
    )
    response = client.get(url, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == HTTPStatus.OK

    response_json = response.json()
    assert response_json["username"] == user.username
