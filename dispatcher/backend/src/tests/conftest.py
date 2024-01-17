from typing import Callable, Generator

import pytest
from sqlalchemy.orm import Session as OrmSession

from common import constants
from db import Session


@pytest.fixture
def dbsession() -> Generator[OrmSession, None, None]:
    with Session.begin() as session:
        yield session


@pytest.fixture
def set_default_publisher() -> Generator[Callable, None, None]:
    def _set_default_publisher(publisher: str):
        constants.DEFAULT_PUBLISHER = publisher

    yield _set_default_publisher
    constants.DEFAULT_PUBLISHER = None  # Reset to default after test
