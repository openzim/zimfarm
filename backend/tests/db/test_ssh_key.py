import datetime
from uuid import uuid4

import pytest
from pytest import MonkeyPatch
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.db import ssh_key as db_ssh_key_module
from zimfarm_backend.db.models import User
from zimfarm_backend.db.ssh_key import (
    delete_ssh_key,
    get_ssh_key_by_fingerprint,
    get_ssh_key_by_fingerprint_or_none,
    has_ssh_key_expired,
)


def test_get_ssh_key_by_fingerprint_or_none_not_found(dbsession: OrmSession):
    """Test getting a non-existent SSH key by fingerprint."""
    result = get_ssh_key_by_fingerprint_or_none(
        session=dbsession,
        fingerprint="non-existent-fingerprint",
    )

    assert result is None


@pytest.mark.num_users(1)
def test_get_ssh_key_by_fingerprint_found(dbsession: OrmSession, users: list[User]):
    """Test getting an existing SSH key by fingerprint."""
    result = get_ssh_key_by_fingerprint(
        session=dbsession,
        fingerprint=users[0].ssh_keys[0].fingerprint,
    )

    assert result is not None
    assert result.fingerprint == users[0].ssh_keys[0].fingerprint
    assert result.user is not None
    assert result.user.id == users[0].id


@pytest.mark.num_users(1)
def test_delete_ssh_key(dbsession: OrmSession, users: list[User]):
    """Test deleting an SSH key."""
    delete_ssh_key(
        session=dbsession,
        fingerprint=users[0].ssh_keys[0].fingerprint,
        user_id=users[0].id,
    )

    # Verify the key is deleted
    result = get_ssh_key_by_fingerprint_or_none(
        session=dbsession,
        fingerprint=users[0].ssh_keys[0].fingerprint,
    )
    assert result is None


@pytest.mark.num_users(1)
def test_delete_ssh_key_wrong_user(dbsession: OrmSession, users: list[User]):
    """Test deleting an SSH key with wrong user ID."""
    wrong_user_id = uuid4()
    delete_ssh_key(
        session=dbsession,
        fingerprint=users[0].ssh_keys[0].fingerprint,
        user_id=wrong_user_id,
    )

    # Verify the key still exists
    result = get_ssh_key_by_fingerprint_or_none(
        session=dbsession,
        fingerprint=users[0].ssh_keys[0].fingerprint,
    )
    assert result is not None
    assert result.fingerprint == users[0].ssh_keys[0].fingerprint


@pytest.mark.num_users(1)
def test_has_ssh_key_expired(users: list[User], monkeypatch: MonkeyPatch):
    """Test checking if an SSH key has expired."""
    # Set the current time to 2 years in the future
    future_time = datetime.datetime.now(datetime.UTC).replace(
        tzinfo=None
    ) + datetime.timedelta(days=730)
    monkeypatch.setattr(db_ssh_key_module, "getnow", lambda: future_time)
    for key in users[0].ssh_keys:
        assert has_ssh_key_expired(key)


@pytest.mark.num_users(1)
def test_get_missing_expired_keys(
    dbsession: OrmSession, users: list[User], monkeypatch: MonkeyPatch
):
    """Test getting missing expired keys."""
    # Set the current time to 2 years in the future
    future_time = datetime.datetime.now(datetime.UTC).replace(
        tzinfo=None
    ) + datetime.timedelta(days=730)
    monkeypatch.setattr(db_ssh_key_module, "getnow", lambda: future_time)
    assert (
        get_ssh_key_by_fingerprint_or_none(
            session=dbsession,
            fingerprint=users[0].ssh_keys[0].fingerprint,
        )
        is None
    )
