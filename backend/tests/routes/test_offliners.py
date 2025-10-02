from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient

from zimfarm_backend.common.schemas.offliners.models import OfflinerSpecSchema
from zimfarm_backend.common.schemas.orms import OfflinerDefinitionSchema, OfflinerSchema


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
