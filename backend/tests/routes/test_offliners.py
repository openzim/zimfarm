from http import HTTPStatus

from fastapi.testclient import TestClient

from zimfarm_backend.common.schemas.orms import OfflinerDefinitionSchema


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
    mwoffliner_definition: OfflinerDefinitionSchema,  # noqa: ARG001
):
    response = client.get("/v2/offliners/mwoffliner/initial")
    assert response.status_code == HTTPStatus.OK
