import base64
from collections.abc import Callable
from http import HTTPStatus
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.api.token import generate_access_token
from zimfarm_backend.common import getnow
from zimfarm_backend.common.roles import RoleEnum
from zimfarm_backend.common.schemas.offliners.transformers import prepare_blob
from zimfarm_backend.db.blob import create_blob_schema
from zimfarm_backend.db.models import Account, Blob, Recipe


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
    recipe: Recipe,
    access_token: str,
    css_content: bytes,
    skip: int,
    limit: int,
    expected_results: int,
):
    for i in range(6):
        recipe.blobs.append(
            Blob(
                kind="css",
                flag_name="custom-css",
                url=None,
                checksum=f"{i}",
                content=css_content,
            )
        )
    dbsession.add(recipe)
    dbsession.flush()

    response = client.get(
        f"/v2/blobs/{recipe.name}?skip={skip}&limit={limit}",
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
        pytest.param(RoleEnum.PROCESSOR, HTTPStatus.FORBIDDEN, id="processor"),
    ],
)
def test_create_blob(
    client: TestClient,
    recipe: Recipe,
    create_account: Callable[..., Account],
    permission: RoleEnum,
    expected_status_code: HTTPStatus,
):
    account = create_account(permission=permission)
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )

    test_data = encode_test_data("test css content")
    payload = {
        "flag_name": "custom_css",
        "kind": "css",
        "data": test_data,
        "comments": "this is test data",
    }
    response = client.post(
        f"/v2/blobs/{recipe.name}",
        json=payload,
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == expected_status_code


def test_create_blob_returns_existing_if_already_uploaded(
    client: TestClient,
    dbsession: OrmSession,
    recipe: Recipe,
    access_token: str,
    css_content: bytes,
):
    test_data = encode_test_data("test content")
    prepared_blob = prepare_blob(
        blob_data=b"test content", flag_name="custom_css", kind="css"
    )
    blob = Blob(
        flag_name=prepared_blob.flag_name,
        kind=prepared_blob.kind,
        checksum=prepared_blob.checksum,
        content=css_content,
        url=None,
    )
    recipe.blobs.append(blob)
    dbsession.add(recipe)
    dbsession.flush()

    payload = {
        "flag_name": prepared_blob.flag_name,
        "kind": prepared_blob.kind,
        "data": test_data,
    }

    response = client.post(
        f"/v2/blobs/{recipe.name}",
        json=payload,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()

    assert data["checksum"] == prepared_blob.checksum
    assert data["url"] is not None
    assert data["kind"] == prepared_blob.kind
    assert data["flag_name"] == prepared_blob.flag_name


def test_update_blob_with_empty_payload(
    client: TestClient,
    dbsession: OrmSession,
    recipe: Recipe,
    access_token: str,
    css_content: bytes,
):
    blob = Blob(
        kind="css",
        flag_name="custom-css",
        url=None,
        checksum="checksum",
        content=css_content,
    )
    recipe.blobs.append(blob)
    dbsession.add(recipe)
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
    recipe: Recipe,
    access_token: str,
    css_content: bytes,
):
    blob = Blob(
        kind="css",
        flag_name="custom-css",
        checksum="checksum",
        content=css_content,
        url=None,
    )
    recipe.blobs.append(blob)
    dbsession.add(recipe)
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


def test_download_blob_success(
    client: TestClient,
    dbsession: OrmSession,
    recipe: Recipe,
    css_content: bytes,
):
    blob = Blob(
        kind="css",
        flag_name="custom-css",
        checksum="checksum",
        url=None,
        content=css_content,
    )
    recipe.blobs.append(blob)
    dbsession.add(recipe)
    dbsession.flush()

    blob_schema = create_blob_schema(blob)
    response = client.get(
        f"/v2/blobs/download/{blob_schema.filename}",
    )
    assert response.status_code == HTTPStatus.OK


def test_download_blob_wrong_extension(
    client: TestClient,
    dbsession: OrmSession,
    recipe: Recipe,
    css_content: bytes,
):
    blob = Blob(
        kind="css",
        flag_name="custom-css",
        checksum="checksum",
        url=None,
        content=css_content,
    )
    recipe.blobs.append(blob)
    dbsession.add(recipe)
    dbsession.flush()

    blob_schema = create_blob_schema(blob)
    response = client.get(
        f"/v2/blobs/download/{blob_schema.id}.jpg",
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
