from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.db.models import Blob, Schedule


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
    response = client.get(f"/v2/blobs/{schedule.name}?skip={skip}&limit={limit}")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["meta"]["skip"] == skip
    assert data["meta"]["limit"] == limit
    assert data["meta"]["page_size"] == expected_results
    assert len(data["items"]) == expected_results
