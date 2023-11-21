from typing import Generator

import pytest
from sqlalchemy.orm import Session as OrmSession

from db import Session


@pytest.fixture
def dbsession() -> Generator[OrmSession, None, None]:
    with Session.begin() as session:
        yield session
