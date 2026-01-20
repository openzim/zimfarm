"""Pytest configuration and shared fixtures for healthcheck tests."""

import os
from collections.abc import Generator

import pytest
from pytest import MonkeyPatch

# Set required environment variables for tests
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("REQUESTS_TIMEOUT", "1m")
os.environ.setdefault("ZIMFARM_API_URL", "http://test-api.example.com")
os.environ.setdefault("ZIMFARM_FRONTEND_URL", "http://test-frontend.example.com")
os.environ.setdefault("ZIMFARM_USERNAME", "test_user")
os.environ.setdefault("ZIMFARM_PASSWORD", "test_password")
os.environ.setdefault(
    "ZIMFARM_DATABASE_URL", "postgresql://test:test@localhost/test_db"
)


@pytest.fixture
def mock_env_vars(monkeypatch: MonkeyPatch) -> Generator[dict[str, str]]:
    """Fixture to provide mock environment variables."""
    env_vars = {
        "DEBUG": "false",
        "REQUESTS_TIMEOUT": "1m",
        "ZIMFARM_API_URL": "http://test-api.example.com",
        "ZIMFARM_FRONTEND_URL": "http://test-frontend.example.com",
        "ZIMFARM_USERNAME": "test_user",
        "ZIMFARM_PASSWORD": "test_password",
        "ZIMFARM_DATABASE_URL": "postgresql://test:test@localhost/test_db",
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    yield env_vars
