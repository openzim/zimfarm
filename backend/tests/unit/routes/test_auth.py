import datetime
import uuid
from http import HTTPStatus

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.db.models import User
from zimfarm_backend.db.refresh_token import create_refresh_token, expire_refresh_tokens
from zimfarm_backend.settings import Settings


def test_auth_with_credentials(client: TestClient, user: User):
    response = client.post(
        "/auth/authorize",
        json={"username": user.username, "password": "testpassword"},
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["access_token"] is not None
    assert data["refresh_token"] is not None
    assert data["expires_in"] == Settings.JWT_TOKEN_EXPIRY_DURATION


def test_auth_with_credentials_invalid_credentials(client: TestClient):
    response = client.post(
        "/auth/authorize",
        json={"username": "testuser", "password": "invalidpassword"},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_refresh_access_token(client: TestClient, user: User, dbsession: OrmSession):
    token = create_refresh_token(session=dbsession, user_id=user.id)
    response = client.post(
        "/auth/refresh",
        headers={"refresh-token": str(token.token)},
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["access_token"] is not None
    assert data["refresh_token"] is not None
    assert data["expires_in"] == Settings.JWT_TOKEN_EXPIRY_DURATION


def test_refresh_access_token_invalid_token(client: TestClient):
    response = client.post(
        "/auth/refresh",
        headers={"refresh-token": str(uuid.uuid4())},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_refresh_access_token_expired_token(
    client: TestClient, user: User, dbsession: OrmSession
):
    token = create_refresh_token(session=dbsession, user_id=user.id)
    expire_refresh_tokens(
        session=dbsession,
        expire_time=datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=1),
    )
    response = client.post(
        "/auth/refresh",
        headers={"refresh-token": str(token.token)},
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["access_token"] is not None
    assert data["refresh_token"] is not None
    assert data["expires_in"] == Settings.JWT_TOKEN_EXPIRY_DURATION
