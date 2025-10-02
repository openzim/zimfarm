from http import HTTPStatus

from fastapi.testclient import TestClient

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
