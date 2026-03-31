from collections.abc import Callable
from http import HTTPStatus

from fastapi.testclient import TestClient

from zimfarm_backend.db.models import Recipe


def test_get_tags(client: TestClient, create_recipe: Callable[..., Recipe]):
    # Create recipes with different tags
    create_recipe(name="recipe1", tags=["tag1", "tag2"])
    create_recipe(name="recipe2", tags=["tag2", "tag3"])
    create_recipe(name="recipe3", tags=["tag3", "tag4"])
    create_recipe(name="recipe4", tags=["tag4", "tag5"])

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
