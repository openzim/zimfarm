from collections.abc import Callable
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common.roles import ROLES, RoleEnum, merge_scopes
from zimfarm_backend.common.schemas.models import UserUpdateSchema
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
    get_user_by_idp_sub,
    get_user_by_idp_sub_or_none,
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


def test_get_user_by_idp_sub_or_none(dbsession: OrmSession):
    user = get_user_by_idp_sub_or_none(dbsession, idp_sub=uuid4(), fetch_ssh_keys=True)
    assert user is None


def test_get_user_by_idp_sub_not_found(dbsession: OrmSession):
    with pytest.raises(RecordDoesNotExistError):
        get_user_by_idp_sub(dbsession, idp_sub=uuid4(), fetch_ssh_keys=True)


def test_get_user_by_idp_sub(dbsession: OrmSession, create_user: Callable[..., User]):
    user = create_user(idp_sub=uuid4())
    assert user.idp_sub is not None
    db_user = get_user_by_idp_sub(dbsession, idp_sub=user.idp_sub, fetch_ssh_keys=True)
    assert db_user is not None
    assert db_user.id == user.id


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


def test_create_user_duplicate(dbsession: OrmSession, user: User):
    """Test that create_user raises an exception if username already exists"""
    with pytest.raises(RecordAlreadyExistsError):
        create_user(
            dbsession,
            username=user.username,
            email="new@example.com",
            password_hash="hash",
            scope={},
            role="custom",
        )


def test_update_user_role(dbsession: OrmSession, user: User):
    update_user(
        dbsession,
        user_id=user.id,
        request=UserUpdateSchema(email="updated@example.com", role=RoleEnum.EDITOR),
    )
    dbsession.refresh(user)
    assert user.email == "updated@example.com"
    assert user.role == RoleEnum.EDITOR
    assert user.scope is None


def test_update_user_scope(dbsession: OrmSession, user: User):
    scope = {"schedules": {"create": True, "delete": False, "update": True}}
    update_user(
        dbsession,
        user_id=user.id,
        request=UserUpdateSchema(
            email="updated@example.com",
            role=None,
            scope=scope,
        ),
    )
    dbsession.refresh(user)
    assert user.email == "updated@example.com"
    assert user.role == "custom"
    assert user.scope == scope


@pytest.mark.parametrize(
    ["custom_scope", "all_scopes", "expected"],
    [
        (
            {"schedules": {"read": True}},
            {
                "schedules": {"read": True, "write": True},
                "users": {"read": True, "write": True},
            },
            {
                "schedules": {"read": True, "write": False},
                "users": {"read": False, "write": False},
            },
        ),
        (
            {},
            {
                "schedules": {"read": True, "write": True},
                "users": {"read": True, "write": True},
            },
            {
                "schedules": {"read": False, "write": False},
                "users": {"read": False, "write": False},
            },
        ),
    ],
)
def test_merge_scopes(
    custom_scope: dict[str, dict[str, bool]],
    all_scopes: dict[str, dict[str, bool]],
    expected: dict[str, dict[str, bool]],
):
    assert merge_scopes(custom_scope, all_scopes) == expected


def test_update_user_scope_and_role(dbsession: OrmSession, user: User):
    scope = {"schedules": {"create": True, "delete": False, "update": True}}
    with pytest.raises(ValueError):
        update_user(
            dbsession,
            user_id=user.id,
            request=UserUpdateSchema(
                email="updated@example.com",
                role=RoleEnum.EDITOR,
                scope=scope,
            ),
        )


def test_update_user_partial(dbsession: OrmSession, user: User):
    """Test that update_user can update partial fields"""
    original_email = user.email
    update_user(
        dbsession,
        user_id=user.id,
        request=UserUpdateSchema(role=RoleEnum.EDITOR),
    )
    dbsession.refresh(user)
    assert user.email == original_email
    assert user.role == RoleEnum.EDITOR
    assert user.scope is None


def test_delete_user(dbsession: OrmSession, user: User):
    """Test that delete_user marks user as deleted"""
    delete_user(dbsession, user_id=user.id)
    dbsession.refresh(user)
    assert user.deleted
