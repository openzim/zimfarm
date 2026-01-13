import base64
from collections.abc import Callable
from http import HTTPStatus
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.api.routes.blobs import logic as blob_logic
from zimfarm_backend.api.token import generate_access_token
from zimfarm_backend.common import getnow
from zimfarm_backend.common.roles import RoleEnum
from zimfarm_backend.common.schemas.offliners import transformers
from zimfarm_backend.common.schemas.offliners.models import PreparedBlob
from zimfarm_backend.common.schemas.offliners.transformers import prepare_blob
from zimfarm_backend.db.models import Blob, Schedule, User


@pytest.fixture(autouse=True)
def mock_upload_blob(monkeypatch: MonkeyPatch):
    def _mock_upload_blob(prepared_blob: PreparedBlob):
        pass

    monkeypatch.setattr(blob_logic, "upload_blob", _mock_upload_blob)


@pytest.fixture(autouse=True)
def set_env(monkeypatch: MonkeyPatch):
    monkeypatch.setattr(
        transformers, "BLOB_PRIVATE_STORAGE_URL", "http://www.example.com"
    )
    monkeypatch.setattr(
        transformers, "BLOB_PUBLIC_STORAGE_URL", "http://www.example.com"
    )


def test_get_blobs_empty(client: TestClient):
    response = client.get("/v2/contexts?skip=0&limit=10")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert "meta" in data
    assert "items" in data
    assert data["meta"]["skip"] == 0
    assert data["meta"]["limit"] == 10
    assert data["meta"]["page_size"] == 0
    assert data["meta"]["count"] == 0
    assert data["items"] == []


@pytest.mark.parametrize(
    "skip,limit,expected_results",
    [
        pytest.param(0, 3, 3, id="first-page"),
        pytest.param(3, 3, 3, id="second-page"),
        pytest.param(0, 1, 1, id="first-page-with-low-limit"),
        pytest.param(0, 10, 6, id="first-page-with-high-limit"),
        pytest.param(10, 10, 0, id="page-num-too-high-no-results"),
    ],
)
def test_get_blobs_pagination(
    dbsession: OrmSession,
    client: TestClient,
    schedule: Schedule,
    access_token: str,
    skip: int,
    limit: int,
    expected_results: int,
):
    for i in range(6):
        schedule.blobs.append(
            Blob(
                kind="css",
                flag_name="custom-css",
                url=f"https://www.example.com/style{i}.css",
                checksum=f"{i}",
            )
        )
    dbsession.add(schedule)
    dbsession.flush()

    response = client.get(
        f"/v2/blobs/{schedule.name}?skip={skip}&limit={limit}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["meta"]["skip"] == skip
    assert data["meta"]["limit"] == limit
    assert data["meta"]["page_size"] == expected_results
    assert len(data["items"]) == expected_results


def encode_test_data(content: str) -> str:
    """Encode test content as base64 string"""
    return base64.b64encode(content.encode()).decode()


@pytest.mark.parametrize(
    "permission,expected_status_code",
    [
        pytest.param(RoleEnum.ADMIN, HTTPStatus.OK, id="admin"),
        pytest.param(RoleEnum.PROCESSOR, HTTPStatus.UNAUTHORIZED, id="processor"),
    ],
)
def test_create_blob(
    client: TestClient,
    schedule: Schedule,
    create_user: Callable[..., User],
    permission: RoleEnum,
    expected_status_code: HTTPStatus,
):
    user = create_user(permission=permission)
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        email=user.email,
        scope=user.scope,
    )

    test_data = encode_test_data("test css content")
    payload = {
        "flag_name": "custom_css",
        "kind": "css",
        "data": test_data,
        "comments": "this is test data",
    }
    response = client.post(
        f"/v2/blobs/{schedule.name}",
        json=payload,
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == expected_status_code


def test_create_blob_returns_existing_if_already_uploaded(
    client: TestClient,
    dbsession: OrmSession,
    schedule: Schedule,
    access_token: str,
):
    test_data = encode_test_data("test content")
    prepared_blob = prepare_blob(
        blob_data=b"test content", flag_name="custom_css", kind="css"
    )
    blob = Blob(
        flag_name=prepared_blob.flag_name,
        kind=prepared_blob.kind,
        checksum=prepared_blob.checksum,
        url=str(prepared_blob.public_url),
    )
    schedule.blobs.append(blob)
    dbsession.add(schedule)
    dbsession.flush()

    payload = {
        "flag_name": prepared_blob.flag_name,
        "kind": prepared_blob.kind,
        "data": test_data,
    }

    response = client.post(
        f"/v2/blobs/{schedule.name}",
        json=payload,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()

    assert data["checksum"] == prepared_blob.checksum
    assert data["url"] == str(prepared_blob.public_url)
    assert data["kind"] == prepared_blob.kind
    assert data["flag_name"] == prepared_blob.flag_name


def test_update_blob_with_empty_payload(
    client: TestClient,
    dbsession: OrmSession,
    schedule: Schedule,
    access_token: str,
):
    blob = Blob(
        kind="css",
        flag_name="custom-css",
        url="https://www.example.com/style.css",
        checksum="checksum",
    )
    schedule.blobs.append(blob)
    dbsession.add(schedule)
    dbsession.flush()

    payload = {}

    response = client.patch(
        f"/v2/blobs/{blob.id}",
        json=payload,
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_delete_blob_success(
    client: TestClient,
    dbsession: OrmSession,
    schedule: Schedule,
    access_token: str,
):
    blob = Blob(
        kind="css",
        flag_name="custom-css",
        url="https://www.example.com/style.css",
        checksum="checksum",
    )
    schedule.blobs.append(blob)
    dbsession.add(schedule)
    dbsession.flush()

    blob_id = blob.id

    response = client.delete(
        f"/v2/blobs/{blob_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == HTTPStatus.NO_CONTENT


def test_delete_blob_not_found(
    client: TestClient,
    access_token: str,
):
    response = client.delete(
        f"/v2/blobs/{uuid4()}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
