from uuid import uuid4

import pytest
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.db.exceptions import RecordDoesNotExistError
from zimfarm_backend.db.models import User
from zimfarm_backend.db.user import (
    get_user_by_id,
    get_user_by_id_or_none,
    get_user_by_username,
    get_user_by_username_or_none,
)


def test_get_user_by_id_or_none(dbsession: OrmSession):
    """Test that get_user_by_id_or_none returns None if the user does not exist"""
    user = get_user_by_id_or_none(dbsession, user_id=uuid4())
    assert user is None


def test_get_user_by_id_not_found(dbsession: OrmSession):
    """Test that get_user_by_id raises an exception if the user does not exist"""
    with pytest.raises(RecordDoesNotExistError):
        get_user_by_id(dbsession, user_id=uuid4())


def test_get_user_by_id(dbsession: OrmSession, user: User):
    """Test that get_user_by_id returns the user if the user exists"""
    db_user = get_user_by_id(dbsession, user_id=user.id)
    assert db_user is not None
    assert db_user.id == user.id


def test_get_user_by_username_or_none(dbsession: OrmSession):
    """Test that get_user_by_username_or_none returns None if the user does not exist"""
    user = get_user_by_username_or_none(dbsession, username="doesnotexist")
    assert user is None


def test_get_user_by_username_not_found(dbsession: OrmSession):
    """Test that get_user_by_username raises an exception if the user does not exist"""
    with pytest.raises(RecordDoesNotExistError):
        get_user_by_username(dbsession, username="doesnotexist")


def test_get_user_by_username(dbsession: OrmSession, user: User):
    """Test that get_user_by_username returns the user if the user exists"""
    db_user = get_user_by_username(dbsession, username=user.username)
    assert db_user is not None
    assert db_user.id == user.id
    assert db_user.username == user.username
