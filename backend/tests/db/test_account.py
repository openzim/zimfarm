from uuid import uuid4

import pytest
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common.roles import ROLES, RoleEnum, merge_scopes
from zimfarm_backend.common.schemas.models import AccountUpdateSchema
from zimfarm_backend.db.account import (
    create_account,
    delete_account,
    get_account_by_id,
    get_account_by_id_or_none,
    get_account_by_username,
    get_account_by_username_or_none,
    get_accounts,
    update_account,
)
from zimfarm_backend.db.exceptions import (
    RecordAlreadyExistsError,
    RecordDoesNotExistError,
)
from zimfarm_backend.db.models import Account


def test_get_account_by_id_or_none(dbsession: OrmSession):
    """Test that get_account_by_id_or_none returns None if the account does not exist"""
    account = get_account_by_id_or_none(dbsession, account_id=uuid4())
    assert account is None


def test_get_account_by_id_not_found(dbsession: OrmSession):
    """Test that get_account_by_id raises an exception if the account does not exist"""
    with pytest.raises(RecordDoesNotExistError):
        get_account_by_id(dbsession, account_id=uuid4())


def test_get_account_by_id(dbsession: OrmSession, account: Account):
    """Test that get_account_by_id returns the account if the account exists"""
    db_account = get_account_by_id(dbsession, account_id=account.id)
    assert db_account is not None
    assert db_account.id == account.id


def test_get_account_by_username_or_none(dbsession: OrmSession):
    account = get_account_by_username_or_none(dbsession, username="doesnotexist")
    assert account is None


def test_get_account_by_username_not_found(dbsession: OrmSession):
    with pytest.raises(RecordDoesNotExistError):
        get_account_by_username(dbsession, username="doesnotexist")


def test_get_account_by_username(dbsession: OrmSession, account: Account):
    """Test that get_account_by_username returns the account if the account exists"""
    db_account = get_account_by_username(dbsession, username=account.display_name)
    assert db_account is not None
    assert db_account.id == account.id
    assert db_account.username == account.username


@pytest.mark.num_accounts(10)
def test_get_accounts_pagination(dbsession: OrmSession, accounts: list[Account]):
    """Test that get_accounts pagination works correctly"""
    # Test first page
    result = get_accounts(dbsession, skip=0, limit=1)
    assert result.nb_records == len(accounts)
    assert len(result.accounts) == 1


def test_create_account(dbsession: OrmSession):
    """Test that create_account creates a new account"""
    account = create_account(
        dbsession,
        username="newuser",
        display_name="New Account",
        password_hash="hash",
        scope=None,
        role=RoleEnum.EDITOR,
    )
    assert account.username == "newuser"
    assert account.password_hash == "hash"
    assert account.display_name == "New Account"
    assert account.role == "editor"
    assert not account.deleted


def test_create_account_with_non_custom_role_and_scope(dbsession: OrmSession):
    with pytest.raises(ValueError):
        create_account(
            dbsession,
            username="newuser",
            display_name="New Account",
            password_hash="hash",
            scope=ROLES["editor"],
            role="editor",
        )


def test_create_account_duplicate(dbsession: OrmSession, account: Account):
    """Test that create_account raises an exception if username already exists"""
    with pytest.raises(RecordAlreadyExistsError):
        create_account(
            dbsession,
            username=account.display_name,
            display_name=account.display_name,
            password_hash="hash",
            scope={},
            role="custom",
        )


def test_update_account_role(dbsession: OrmSession, account: Account):
    update_account(
        dbsession,
        account_id=account.id,
        request=AccountUpdateSchema(role=RoleEnum.EDITOR),
    )
    dbsession.refresh(account)
    assert account.role == RoleEnum.EDITOR
    assert account.scope is None


def test_update_account_scope(dbsession: OrmSession, account: Account):
    scope = {"recipes": {"create": True, "delete": False, "update": True}}
    update_account(
        dbsession,
        account_id=account.id,
        request=AccountUpdateSchema(
            role=None,
            scope=scope,
        ),
    )
    dbsession.refresh(account)
    assert account.role == "custom"
    assert account.scope == scope


@pytest.mark.parametrize(
    ["custom_scope", "all_scopes", "expected"],
    [
        (
            {"recipes": {"read": True}},
            {
                "recipes": {"read": True, "write": True},
                "accounts": {"read": True, "write": True},
            },
            {
                "recipes": {"read": True, "write": False},
                "accounts": {"read": False, "write": False},
            },
        ),
        (
            {},
            {
                "recipes": {"read": True, "write": True},
                "accounts": {"read": True, "write": True},
            },
            {
                "recipes": {"read": False, "write": False},
                "accounts": {"read": False, "write": False},
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


def test_update_account_scope_and_role(dbsession: OrmSession, account: Account):
    scope = {"recipes": {"create": True, "delete": False, "update": True}}
    with pytest.raises(ValueError):
        update_account(
            dbsession,
            account_id=account.id,
            request=AccountUpdateSchema(
                role=RoleEnum.EDITOR,
                scope=scope,
            ),
        )


def test_update_account_partial(dbsession: OrmSession, account: Account):
    """Test that update_account can update partial fields"""
    update_account(
        dbsession,
        account_id=account.id,
        request=AccountUpdateSchema(role=RoleEnum.EDITOR, display_name="newdisplay"),
    )
    dbsession.refresh(account)
    assert account.role == RoleEnum.EDITOR
    assert account.scope is None
    assert account.display_name == "newdisplay"


def test_update_account_no_display_name(dbsession: OrmSession, account: Account):
    with pytest.raises(ValueError, match="Account must have a display name."):
        update_account(
            dbsession,
            account_id=account.id,
            request=AccountUpdateSchema(display_name=None),
        )


def test_update_account_with_password_set_blank_username(
    dbsession: OrmSession, account: Account
):
    with pytest.raises(ValueError, match="Account with password must have a username"):
        update_account(
            dbsession, account_id=account.id, request=AccountUpdateSchema(username=None)
        )


def test_update_account_with_no_password_set_blank_username(
    dbsession: OrmSession, account: Account
):
    account.password_hash = None
    dbsession.add(account)

    dbsession.flush()
    update_account(
        dbsession, account_id=account.id, request=AccountUpdateSchema(username=None)
    )
    dbsession.refresh(account)
    assert account.username is None


def test_delete_account(dbsession: OrmSession, account: Account):
    """Test that delete_account marks account as deleted"""
    delete_account(dbsession, account_id=account.id)
    dbsession.refresh(account)
    assert account.deleted
