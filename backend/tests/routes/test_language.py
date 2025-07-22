from http import HTTPStatus

from fastapi.testclient import TestClient


def test_get_languages_default_pagination(client: TestClient):
    """Test getting languages with default pagination parameters."""
    response = client.get("/v2/languages")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert "meta" in data
    assert "items" in data
    assert isinstance(data["items"], list)
    assert "count" in data["meta"]
    assert "skip" in data["meta"]
    assert "limit" in data["meta"]
    assert "page_size" in data["meta"]


def test_get_languages_custom_pagination(client: TestClient):
    """Test getting languages with custom pagination parameters."""
    response = client.get("/v2/languages?skip=10&limit=20")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert "meta" in data
    assert "items" in data
    assert isinstance(data["items"], list)
    assert data["meta"]["skip"] == 10
    assert data["meta"]["limit"] == 20
    assert data["meta"]["page_size"] <= 20


def test_get_languages_invalid_pagination(client: TestClient):
    """Test getting languages with invalid pagination parameters."""
    # Test with negative skip
    response = client.get("/v2/languages?skip=-1")
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    # Test with negative limit
    response = client.get("/v2/languages?limit=-1")
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    # Test with limit exceeding maximum
    response = client.get("/v2/languages?limit=501")
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
