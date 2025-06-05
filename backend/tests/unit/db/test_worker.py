import datetime
from ipaddress import IPv4Address

import pytest
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.db.exceptions import RecordDoesNotExistError
from zimfarm_backend.db.models import User, Worker
from zimfarm_backend.db.worker import (
    check_in_worker,
    get_active_workers,
    get_worker,
    get_worker_or_none,
    update_worker,
)


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


def test_get_active_workers_empty(dbsession: OrmSession):
    """Test that get_active_workers returns empty list when no workers exist"""
    result = get_active_workers(dbsession, skip=0, limit=10)
    assert result.nb_records == 0
    assert len(result.workers) == 0


def test_get_active_workers_single(dbsession: OrmSession, worker: Worker):
    """Test that get_active_workers returns a single worker"""
    result = get_active_workers(dbsession, skip=0, limit=10)
    assert result.nb_records == 1
    assert len(result.workers) == 1
    assert result.workers[0].name == worker.name
    assert result.workers[0].username == worker.user.username
    assert result.workers[0].resources.cpu == worker.cpu
    assert result.workers[0].resources.memory == worker.memory
    assert result.workers[0].resources.disk == worker.disk


def test_get_active_workers_pagination(dbsession: OrmSession, user: User):
    """Test that get_active_workers pagination works correctly"""
    # Create multiple workers
    workers: list[Worker] = []
    for i in range(5):
        worker = Worker(
            name=f"testworker{i}",
            selfish=False,
            cpu=2,
            memory=1024,
            disk=1024,
            offliners=["mwoffliner"],
            platforms={},
            last_seen=datetime.datetime.now(datetime.UTC).replace(tzinfo=None),
            last_ip=None,
        )
        worker.user_id = user.id
        dbsession.add(worker)
        workers.append(worker)
    dbsession.flush()

    # Test first page
    result = get_active_workers(dbsession, skip=0, limit=2)
    assert result.nb_records == 5
    assert len(result.workers) == 2
    assert result.workers[0].name == workers[0].name
    assert result.workers[1].name == workers[1].name

    # Test second page
    result = get_active_workers(dbsession, skip=2, limit=2)
    assert result.nb_records == 5
    assert len(result.workers) == 2
    assert result.workers[0].name == workers[2].name
    assert result.workers[1].name == workers[3].name

    # Test last page
    result = get_active_workers(dbsession, skip=4, limit=2)
    assert result.nb_records == 5
    assert len(result.workers) == 1
    assert result.workers[0].name == workers[4].name


def test_get_active_workers_excludes_deleted(dbsession: OrmSession, worker: Worker):
    """Test that get_active_workers excludes deleted workers"""
    # Delete the worker
    worker.deleted = True
    dbsession.flush()

    result = get_active_workers(dbsession, skip=0, limit=10)
    assert result.nb_records == 0
    assert len(result.workers) == 0


def test_check_in_worker_new(dbsession: OrmSession, user: User):
    """Test that check_in_worker creates a new worker"""
    worker_name = "newworker"
    check_in_worker(
        session=dbsession,
        worker_name=worker_name,
        cpu=4,
        memory=2048,
        disk=2048,
        selfish=True,
        offliners=["mwoffliner"],
        platforms={},
        user_id=user.id,
    )

    worker = get_worker(dbsession, worker_name=worker_name)
    assert worker.name == worker_name
    assert worker.cpu == 4
    assert worker.memory == 2048
    assert worker.disk == 2048
    assert worker.selfish is True
    assert worker.offliners == ["mwoffliner"]
    assert worker.platforms == {}
    assert worker.user_id == user.id
    assert worker.last_seen is not None
    assert worker.last_ip is None


def test_check_in_worker_update(dbsession: OrmSession, worker: Worker):
    """Test that check_in_worker updates an existing worker"""

    check_in_worker(
        session=dbsession,
        worker_name=worker.name,
        cpu=8,
        memory=4096,
        disk=4096,
        selfish=True,
        offliners=["mwoffliner", "youtube"],
        platforms={},
        user_id=worker.user_id,
    )
    original_last_seen = worker.last_seen
    original_last_ip = worker.last_ip
    original_user_id = worker.user_id
    original_worker_name = worker.name

    # Expire the worker to force a reload of the worker
    dbsession.expire(worker)
    updated_worker = get_worker(dbsession, worker_name=worker.name)

    assert updated_worker.name == original_worker_name
    assert updated_worker.cpu == 8
    assert updated_worker.memory == 4096
    assert updated_worker.disk == 4096
    assert updated_worker.selfish is True
    assert updated_worker.offliners == ["mwoffliner", "youtube"]
    assert updated_worker.platforms == {}
    assert updated_worker.user_id == original_user_id
    assert updated_worker.last_seen is not None
    assert original_last_seen is not None
    assert updated_worker.last_seen > original_last_seen
    assert updated_worker.last_ip == original_last_ip
