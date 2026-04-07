from uuid import uuid4

import pytest
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.db.models import Account
from zimfarm_backend.db.ssh_key import (
    delete_ssh_key,
    get_ssh_key_by_fingerprint,
    get_ssh_key_by_fingerprint_or_none,
)


def test_get_ssh_key_by_fingerprint_or_none_not_found(dbsession: OrmSession):
    """Test getting a non-existent SSH key by fingerprint."""
    result = get_ssh_key_by_fingerprint_or_none(
        session=dbsession,
        fingerprint="non-existent-fingerprint",
    )

    assert result is None


@pytest.mark.num_accounts(1)
def test_get_ssh_key_by_fingerprint_found(
    dbsession: OrmSession, accounts: list[Account]
):
    """Test getting an existing SSH key by fingerprint."""
    result = get_ssh_key_by_fingerprint(
        session=dbsession,
        fingerprint=accounts[0].ssh_keys[0].fingerprint,
    )

    assert result is not None
    assert result.fingerprint == accounts[0].ssh_keys[0].fingerprint
    assert result.account is not None
    assert result.account.id == accounts[0].id


@pytest.mark.num_accounts(1)
def test_delete_ssh_key(dbsession: OrmSession, accounts: list[Account]):
    """Test deleting an SSH key."""
    delete_ssh_key(
        session=dbsession,
        fingerprint=accounts[0].ssh_keys[0].fingerprint,
        account_id=accounts[0].id,
    )

    # Verify the key is deleted
    result = get_ssh_key_by_fingerprint_or_none(
        session=dbsession,
        fingerprint=accounts[0].ssh_keys[0].fingerprint,
    )
    assert result is None


@pytest.mark.num_accounts(1)
def test_delete_ssh_key_wrong_account(dbsession: OrmSession, accounts: list[Account]):
    """Test deleting an SSH key with wrong account ID."""
    wrong_account_id = uuid4()
    delete_ssh_key(
        session=dbsession,
        fingerprint=accounts[0].ssh_keys[0].fingerprint,
        account_id=wrong_account_id,
    )

    # Verify the key still exists
    result = get_ssh_key_by_fingerprint_or_none(
        session=dbsession,
        fingerprint=accounts[0].ssh_keys[0].fingerprint,
    )
    assert result is not None
    assert result.fingerprint == accounts[0].ssh_keys[0].fingerprint
