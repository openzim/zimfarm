from uuid import uuid4

import pytest
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common.roles import ROLES, RoleEnum
from zimfarm_backend.db.exceptions import (
    RecordAlreadyExistsError,
    RecordDoesNotExistError,
)
from zimfarm_backend.db.models import User
from zimfarm_backend.db.user import (
    create_user,
    delete_user,
    get_user_by_id,
    get_user_by_id_or_none,
    get_user_by_username,
    get_user_by_username_or_none,
    get_users,
    update_user,
)


def test_get_user_by_id_or_none(dbsession: OrmSession):
    """Test that get_user_by_id_or_none returns None if the user does not exist"""
    user = get_user_by_id_or_none(dbsession, user_id=uuid4())
    assert user is None


def test_get_user_by_id_not_found(dbsession: OrmSession):
    """Test that get_user_by_id raises an exception if the user does not exist"""
    with pytest.raises(RecordDoesNotExistError):
        get_user_by_id(dbsession, user_id=uuid4())


@pytest.mark.num_users(1)
def test_get_user_by_id(dbsession: OrmSession, users: list[User]):
    """Test that get_user_by_id returns the user if the user exists"""
    db_user = get_user_by_id(dbsession, user_id=users[0].id)
    assert db_user is not None
    assert db_user.id == users[0].id


def test_get_user_by_username_or_none(dbsession: OrmSession):
    """Test that get_user_by_username_or_none returns None if the user does not exist"""
    user = get_user_by_username_or_none(dbsession, username="doesnotexist")
    assert user is None


def test_get_user_by_username_not_found(dbsession: OrmSession):
    """Test that get_user_by_username raises an exception if the user does not exist"""
    with pytest.raises(RecordDoesNotExistError):
        get_user_by_username(dbsession, username="doesnotexist")


@pytest.mark.num_users(1)
def test_get_user_by_username(dbsession: OrmSession, users: list[User]):
    """Test that get_user_by_username returns the user if the user exists"""
    db_user = get_user_by_username(dbsession, username=users[0].username)
    assert db_user is not None
    assert db_user.id == users[0].id
    assert db_user.username == users[0].username


@pytest.mark.num_users(10)
def test_get_users_pagination(dbsession: OrmSession, users: list[User]):
    """Test that get_users pagination works correctly"""
    # Test first page
    result = get_users(dbsession, skip=0, limit=1)
    assert result.nb_records == len(users)
    assert len(result.users) == 1


def test_create_user(dbsession: OrmSession):
    """Test that create_user creates a new user"""
    user = create_user(
        dbsession,
        username="newuser",
        email="new@example.com",
        password_hash="hash",
        scope=None,
        role=RoleEnum.EDITOR,
    )
    assert user.username == "newuser"
    assert user.email == "new@example.com"
    assert user.password_hash == "hash"
    assert user.role == "editor"
    assert not user.deleted


def test_create_user_with_non_custom_role_and_scope(dbsession: OrmSession):
    with pytest.raises(ValueError):
        create_user(
            dbsession,
            username="newuser",
            email="new@example.com",
            password_hash="hash",
            scope=ROLES["editor"],
            role="editor",
        )


@pytest.mark.num_users(1)
def test_create_user_duplicate(dbsession: OrmSession, users: list[User]):
    """Test that create_user raises an exception if username already exists"""
    with pytest.raises(RecordAlreadyExistsError):
        create_user(
            dbsession,
            username=users[0].username,
            email="new@example.com",
            password_hash="hash",
            scope={},
            role="custom",
        )


@pytest.mark.num_users(1)
def test_update_user(dbsession: OrmSession, users: list[User]):
    """Test that update_user updates user fields"""
    update_user(
        dbsession,
        user_id=users[0].id,
        email="updated@example.com",
        role=RoleEnum.EDITOR,
    )
    dbsession.refresh(users[0])
    assert users[0].email == "updated@example.com"
    assert users[0].role == RoleEnum.EDITOR


@pytest.mark.num_users(1)
def test_update_user_partial(dbsession: OrmSession, users: list[User]):
    """Test that update_user can update partial fields"""
    original_email = users[0].email
    update_user(
        dbsession,
        user_id=users[0].id,
        email=None,
        role=RoleEnum.EDITOR,
    )
    dbsession.refresh(users[0])
    assert users[0].email == original_email
    assert users[0].role == RoleEnum.EDITOR


@pytest.mark.num_users(1)
def test_delete_user(dbsession: OrmSession, users: list[User]):
    """Test that delete_user marks user as deleted"""
    delete_user(dbsession, user_id=users[0].id)
    dbsession.refresh(users[0])
    assert users[0].deleted
