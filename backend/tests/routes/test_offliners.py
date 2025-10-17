from collections.abc import Callable
from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient

from zimfarm_backend.common import getnow
from zimfarm_backend.common.roles import RoleEnum
from zimfarm_backend.common.schemas.offliners.models import OfflinerSpecSchema
from zimfarm_backend.common.schemas.orms import OfflinerDefinitionSchema, OfflinerSchema
from zimfarm_backend.db.models import User
from zimfarm_backend.utils.token import generate_access_token


def test_get_offliners(client: TestClient):
    response = client.get("/v2/offliners")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert "meta" in data
    assert "items" in data


def test_get_offliner_missing(
    client: TestClient,
):
    response = client.get("/v2/offliners/mwoffliner/initial")
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.parametrize(
    "permission,expected_status_code",
    [
        pytest.param(RoleEnum.ADMIN, HTTPStatus.CREATED, id="admin"),
        pytest.param(RoleEnum.PROCESSOR, HTTPStatus.UNAUTHORIZED, id="processor"),
    ],
)
def test_create_offliner(
    client: TestClient,
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
    response = client.post(
        "/v2/offliners",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "offliner_id": "ted",
            "base_model": "DashModel",
            "docker_image_name": "openzim/ted",
            "ci_secret_hash": "somerandomsecret",
            "command_name": "ted2zim",
        },
    )
    assert response.status_code == expected_status_code


def test_get_offliner(
    client: TestClient,
    mwoffliner: OfflinerSchema,
    mwoffliner_definition: OfflinerDefinitionSchema,  # noqa: ARG001
):
    response = client.get(f"/v2/offliners/{mwoffliner.id}/initial")
    assert response.status_code == HTTPStatus.OK


def test_get_offliner_versions(
    client: TestClient,
    mwoffliner: OfflinerSchema,
    mwoffliner_definition: OfflinerDefinitionSchema,  # noqa: ARG001
):
    response = client.get(f"/v2/offliners/{mwoffliner.id}/versions")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert "meta" in data
    assert "items" in data
    assert len(data["items"]) == 1
    assert data["items"][0] == "initial"


@pytest.mark.parametrize(
    "offliner_id,ci_secret,version,expected_status_code",
    [
        ("mwoffliner", "1234567890", "1.1", HTTPStatus.CREATED),
        ("mwoffliner", "wrong-hash", "1.1", HTTPStatus.UNAUTHORIZED),
        ("ted", "1234567890", "1.1", HTTPStatus.NOT_FOUND),
    ],
)
def test_update_offliner_definition(
    client: TestClient,
    mwoffliner: OfflinerSchema,  # noqa: ARG001
    mwoffliner_flags: OfflinerSpecSchema,
    offliner_id: str,
    ci_secret: str,
    version: str,
    expected_status_code: HTTPStatus,
):
    response = client.post(
        f"/v2/offliners/{offliner_id}/versions",
        json={
            "ci_secret": ci_secret,
            "version": version,
            "spec": mwoffliner_flags.model_dump(mode="json"),
        },
    )
    assert response.status_code == expected_status_code
