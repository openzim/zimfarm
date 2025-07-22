from collections.abc import Callable
from http import HTTPStatus

from fastapi.testclient import TestClient

from zimfarm_backend.db.models import Schedule


def test_get_tags(client: TestClient, create_schedule: Callable[..., Schedule]):
    # Create schedules with different tags
    create_schedule(name="schedule1", tags=["tag1", "tag2"])
    create_schedule(name="schedule2", tags=["tag2", "tag3"])
    create_schedule(name="schedule3", tags=["tag3", "tag4"])
    create_schedule(name="schedule4", tags=["tag4", "tag5"])

    response = client.get("/v2/tags?skip=0&limit=2")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert "meta" in data
    assert "items" in data
    assert data["meta"]["skip"] == 0
    assert data["meta"]["limit"] == 2
    assert data["meta"]["page_size"] == 2
    assert data["meta"]["count"] == 5
    assert data["items"] == ["tag1", "tag2"]
