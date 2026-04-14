from uuid import uuid4

from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.db.models import Worker
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


def test_get_ssh_key_by_fingerprint_found(dbsession: OrmSession, worker: Worker):
    """Test getting an existing SSH key by fingerprint."""
    result = get_ssh_key_by_fingerprint(
        session=dbsession,
        fingerprint=worker.ssh_keys[0].fingerprint,
    )

    assert result is not None
    assert result.fingerprint == worker.ssh_keys[0].fingerprint
    assert result.worker is not None
    assert result.worker.id == worker.id


def test_delete_ssh_key(dbsession: OrmSession, worker: Worker):
    """Test deleting an SSH key."""
    delete_ssh_key(
        session=dbsession,
        fingerprint=worker.ssh_keys[0].fingerprint,
        worker_id=worker.id,
    )

    # Verify the key is deleted
    result = get_ssh_key_by_fingerprint_or_none(
        session=dbsession,
        fingerprint=worker.ssh_keys[0].fingerprint,
    )
    assert result is None


def test_delete_ssh_key_wrong_account(dbsession: OrmSession, worker: Worker):
    """Test deleting an SSH key with wrong account ID."""
    wrong_account_id = uuid4()
    delete_ssh_key(
        session=dbsession,
        fingerprint=worker.ssh_keys[0].fingerprint,
        worker_id=wrong_account_id,
    )

    # Verify the key still exists
    result = get_ssh_key_by_fingerprint_or_none(
        session=dbsession,
        fingerprint=worker.ssh_keys[0].fingerprint,
    )
    assert result is not None
    assert result.fingerprint == worker.ssh_keys[0].fingerprint
