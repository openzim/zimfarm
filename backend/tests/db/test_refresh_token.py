import datetime
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common import getnow
from zimfarm_backend.db.exceptions import RecordDoesNotExistError
from zimfarm_backend.db.models import Refreshtoken, User
from zimfarm_backend.db.refresh_token import (
    create_refresh_token,
    delete_refresh_token,
    expire_refresh_tokens,
    get_refresh_token,
    get_refresh_token_or_none,
)


@pytest.fixture
@pytest.mark.num_users(1)
def refresh_token(dbsession: OrmSession, users: list[User]) -> Refreshtoken:
    """Create a refresh token for a user"""
    token = Refreshtoken(
        token=uuid4(),
        expire_time=getnow() + datetime.timedelta(seconds=1_000),
    )
    token.user = users[0]
    dbsession.add(token)
    dbsession.flush()
    return token


def test_get_refresh_token_or_none(dbsession: OrmSession):
    """Test db returns None if the refresh token does not exist"""
    refresh_token = get_refresh_token_or_none(dbsession, uuid4())
    assert refresh_token is None


@pytest.mark.num_users(1)
def test_create_refresh_token(dbsession: OrmSession, users: list[User]):
    """Test that create_refresh_token creates a refresh token"""
    refresh_token = create_refresh_token(dbsession, users[0].id)
    assert refresh_token is not None
    assert refresh_token.token is not None
    assert refresh_token.user_id == users[0].id
    assert refresh_token.expire_time is not None


def test_get_refresh_token(dbsession: OrmSession, refresh_token: Refreshtoken):
    """Test that get_refresh_token returns the refresh token"""
    db_refresh_token = get_refresh_token(dbsession, refresh_token.token)
    assert db_refresh_token is not None
    assert db_refresh_token.token == refresh_token.token


def test_delete_refresh_token(dbsession: OrmSession, refresh_token: Refreshtoken):
    """Test that delete_refresh_token deletes the refresh token"""
    delete_refresh_token(dbsession, refresh_token.token)
    assert get_refresh_token_or_none(dbsession, refresh_token.token) is None


def test_expire_refresh_tokens(dbsession: OrmSession, refresh_token: Refreshtoken):
    """Test that expire_refresh_tokens expires the refresh tokens"""
    expire_refresh_tokens(
        dbsession,
        getnow() + datetime.timedelta(seconds=2_000),
    )
    assert get_refresh_token_or_none(dbsession, refresh_token.token) is None


def test_delete_refresh_token_not_found(dbsession: OrmSession):
    """Test aises an exception if the refresh token does not exist"""
    with pytest.raises(RecordDoesNotExistError):
        delete_refresh_token(dbsession, uuid4())
