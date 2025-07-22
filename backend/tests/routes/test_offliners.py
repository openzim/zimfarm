from http import HTTPStatus

from fastapi.testclient import TestClient

from zimfarm_backend.common.enums import Offliner


def test_get_offliners(client: TestClient):
    response = client.get("/v2/offliners")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert "meta" in data
    assert "items" in data
    for item in Offliner.all():
        assert item in data["items"]


def test_get_offliner(client: TestClient):
    response = client.get("/v2/offliners/mwoffliner")
    assert response.status_code == HTTPStatus.OK
