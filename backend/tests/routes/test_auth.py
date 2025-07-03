import base64
import datetime
import uuid
from http import HTTPStatus

import pytest
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common import constants
from zimfarm_backend.db.models import User
from zimfarm_backend.db.refresh_token import create_refresh_token, expire_refresh_tokens
from zimfarm_backend.utils.token import sign_message


@pytest.mark.num_users(1)
def test_auth_with_credentials(client: TestClient, users: list[User]):
    response = client.post(
        "/api/v2/auth/authorize",
        json={"username": users[0].username, "password": "testpassword"},
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["access_token"] is not None
    assert data["refresh_token"] is not None
    assert data["expires_in"] == constants.JWT_TOKEN_EXPIRY_DURATION


def test_auth_with_credentials_invalid_credentials(client: TestClient):
    response = client.post(
        "/api/v2/auth/authorize",
        json={"username": "testuser", "password": "invalidpassword"},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.num_users(1)
def test_refresh_access_token(
    client: TestClient, users: list[User], dbsession: OrmSession
):
    token = create_refresh_token(session=dbsession, user_id=users[0].id)
    response = client.post(
        "/api/v2/auth/refresh",
        json={"refresh_token": str(token.token)},
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["access_token"] is not None
    assert data["refresh_token"] is not None
    assert data["expires_in"] == constants.JWT_TOKEN_EXPIRY_DURATION


def test_refresh_access_token_invalid_token(client: TestClient):
    response = client.post(
        "/api/v2/auth/refresh",
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
        expire_time=datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=1),
    )
    response = client.post(
        "/api/v2/auth/refresh",
        json={"refresh_token": str(token.token)},
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["access_token"] is not None
    assert data["refresh_token"] is not None
    assert data["expires_in"] == constants.JWT_TOKEN_EXPIRY_DURATION


@pytest.mark.parametrize(
    ["datetime_str", "expected_status", "expected_response_contents"],
    [
        (
            datetime.datetime.fromtimestamp(0, tz=datetime.UTC).isoformat(),
            HTTPStatus.UNAUTHORIZED,
            [],
        ),
        (
            "hello",
            HTTPStatus.BAD_REQUEST,
            [],
        ),
        (
            datetime.datetime.now(datetime.UTC).isoformat(),
            HTTPStatus.OK,
            ["access_token", "token_type", "expires_in"],
        ),
    ],
)
@pytest.mark.num_users(1)
def test_authenticate_user(
    client: TestClient,
    users: list[User],
    private_key: RSAPrivateKey,
    datetime_str: str,
    expected_status: int,
    expected_response_contents: list[str],
):
    message = f"{users[0].username}:{datetime_str}"
    signature = sign_message(private_key, bytes(message, encoding="ascii"))
    x_sshauth_signature = base64.b64encode(signature).decode()
    response = client.post(
        "/api/v2/auth/ssh-authorize",
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
