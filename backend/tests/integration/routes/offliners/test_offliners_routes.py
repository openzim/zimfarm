import pytest

from common.enum import Offliner


def test_list_offliners(client):
    url = "/offliners/"
    response = client.get(url)
    assert response.status_code == 200
    response_json = response.get_json()
    assert "items" in response_json
    assert "meta" in response_json
    assert "count" in response_json["meta"]
    assert len(response_json["items"]) == response_json["meta"]["count"]


@pytest.mark.parametrize("offliner", Offliner.all())
def test_get_offliner(client, offliner):
    url = f"/offliners/{offliner}"
    response = client.get(url)
    assert response.status_code == 200
    response_json = response.get_json()
    assert "flags" in response_json
    assert "help" in response_json
    assert (
        response_json["help"]
        == f"https://github.com/openzim/{offliner}/wiki/Frequently-Asked-Questions"
    )
