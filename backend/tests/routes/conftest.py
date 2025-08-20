from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.db import gen_dbsession, gen_manual_dbsession
from zimfarm_backend.main import app


@pytest.fixture
def client(dbsession: OrmSession) -> TestClient:
    def test_dbsession() -> Generator[OrmSession]:
        yield dbsession

    # Replace the  database session with the test dbsession
    app.dependency_overrides[gen_dbsession] = test_dbsession
    app.dependency_overrides[gen_manual_dbsession] = test_dbsession

    return TestClient(app=app)
