from collections.abc import Generator

import pytest
from sqlalchemy.orm import Session as OrmSession
from werkzeug.security import generate_password_hash

from zimfarm_backend.db import Session
from zimfarm_backend.db.models import Base, User


@pytest.fixture
def dbsession() -> Generator[OrmSession]:
    with Session.begin() as session:
        # Ensure we are starting with an empty database
        engine = session.get_bind()
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        yield session
        session.rollback()


@pytest.fixture
def user(dbsession: OrmSession) -> User:
    """Create a user for testing"""
    user = User(
        username="testuser",
        password_hash=generate_password_hash("testpassword"),
        email="testuser@example.com",
        scope={"test": "test"},
    )
    dbsession.add(user)
    dbsession.flush()
    return user


# @pytest.fixture
# def set_default_publisher() -> Generator[Callable]:
#     def _set_default_publisher(publisher: str):
#         constants.DEFAULT_PUBLISHER = publisher
#
#     yield _set_default_publisher
#     constants.DEFAULT_PUBLISHER = None  # Reset to default after test
