from ipaddress import IPv4Address

import pytest
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.db.exceptions import RecordDoesNotExistError
from zimfarm_backend.db.models import Worker
from zimfarm_backend.db.worker import get_worker, get_worker_or_none, update_worker


def test_get_worker_or_none(dbsession: OrmSession):
    """Test that get_worker_or_none returns None if the worker does not exist"""
    worker = get_worker_or_none(dbsession, worker_name="nonexistent")
    assert worker is None


def test_get_worker_not_found(dbsession: OrmSession):
    """Test that get_worker raises an exception if the worker does not exist"""
    with pytest.raises(RecordDoesNotExistError):
        get_worker(dbsession, worker_name="nonexistent")


def test_get_worker(dbsession: OrmSession, worker: Worker):
    """Test that get_worker returns the worker if it exists"""
    db_worker = get_worker(dbsession, worker_name=worker.name)
    assert db_worker is not None
    assert db_worker.name == worker.name


def test_update_worker_not_found(dbsession: OrmSession):
    """Test that update_worker raises an exception if the worker does not exist"""
    with pytest.raises(RecordDoesNotExistError):
        update_worker(dbsession, worker_name="nonexistent")


def test_update_worker(dbsession: OrmSession, worker: Worker):
    """Test that update_worker updates the worker's last_seen and last_ip"""
    original_last_seen = worker.last_seen
    original_last_ip = worker.last_ip
    new_ip = "192.168.1.1"

    updated_worker = update_worker(
        dbsession, worker_name=worker.name, ip_address=new_ip
    )

    assert updated_worker.name == worker.name
    assert updated_worker.last_seen is not None
    if original_last_seen is not None:
        assert updated_worker.last_seen > original_last_seen
    assert updated_worker.last_ip == IPv4Address(new_ip)
    assert updated_worker.last_ip != original_last_ip


def test_update_worker_without_ip(dbsession: OrmSession, worker: Worker):
    """Test that update_worker only updates last_seen when no IP is provided"""
    original_last_seen = worker.last_seen
    original_last_ip = worker.last_ip

    updated_worker = update_worker(dbsession, worker_name=worker.name)

    assert updated_worker.name == worker.name
    assert updated_worker.last_seen is not None
    if original_last_seen is not None:
        assert updated_worker.last_seen > original_last_seen
    assert updated_worker.last_ip == original_last_ip
