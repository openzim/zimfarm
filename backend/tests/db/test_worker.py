import datetime
from collections.abc import Callable
from ipaddress import IPv4Address

import pytest
from pytest import MonkeyPatch
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common import getnow
from zimfarm_backend.common.schemas.orms import OfflinerSchema
from zimfarm_backend.db import worker as worker_module
from zimfarm_backend.db.exceptions import RecordDoesNotExistError
from zimfarm_backend.db.models import User, Worker
from zimfarm_backend.db.worker import (
    check_in_worker,
    get_worker,
    get_worker_or_none,
    get_workers,
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


def test_get_workers_empty(dbsession: OrmSession):
    """Test that get_workers returns empty list when no workers exist"""
    result = get_workers(dbsession, skip=0, limit=10)
    assert result.nb_records == 0
    assert len(result.workers) == 0


def test_get_workers_pagination(
    dbsession: OrmSession, create_worker: Callable[..., Worker]
):
    # create 30 workers
    workers = [create_worker(name=f"worker-{i}") for i in range(30)]
    # disable 10 workers
    for worker in workers[:10]:
        worker.deleted = True
        dbsession.add(worker)
    dbsession.flush()

    limit = 10
    result = get_workers(dbsession, skip=0, limit=limit)
    assert result.nb_records == 20
    assert len(result.workers) == limit


@pytest.mark.parametrize("hide_offlines,nb_records", [(True, 20), (False, 30)])
def test_get_workers_hide_offlines(
    dbsession: OrmSession,
    create_worker: Callable[..., Worker],
    monkeypatch: MonkeyPatch,
    *,
    hide_offlines: bool,
    nb_records: int,
):
    "Test that only online workers are returned."
    # create 30 workers that are currently active
    workers = [create_worker(name=f"worker-{i}") for i in range(30)]
    # change the last seen of the last 10 workers to 1 hour ago
    for worker in workers[:10]:
        worker.last_seen = getnow() - datetime.timedelta(hours=1)
        dbsession.add(worker)
    dbsession.flush()

    # set last seen duration to 30 minutes
    monkeypatch.setattr(worker_module, "WORKER_OFFLINE_DELAY_DURATION", 60 * 30)

    result = get_workers(dbsession, skip=0, limit=1000, hide_offlines=hide_offlines)
    assert result.nb_records == nb_records
    if hide_offlines:
        for worker in result.workers:
            assert worker.status == "online"
    else:
        for worker in result.workers:
            assert worker.status in ["online", "offline"]


def test_check_in_new_worker(
    dbsession: OrmSession, user: User, mwoffliner: OfflinerSchema
):
    """Test that check_in_worker creates a new worker"""
    worker_name = "newworker"
    check_in_worker(
        session=dbsession,
        worker_name=worker_name,
        cpu=4,
        memory=2048,
        disk=2048,
        selfish=True,
        offliners=[mwoffliner.id],
        user_id=user.id,
        cordoned=False,
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
    assert worker.cordoned is False
    assert worker.admin_disabled is False


def test_check_in_worker_update(
    dbsession: OrmSession,
    worker: Worker,
    mwoffliner: OfflinerSchema,
    ted_offliner: OfflinerSchema,
):
    """Test that check_in_worker updates an existing worker"""

    original_last_seen = worker.last_seen
    original_last_ip = worker.last_ip
    original_user_id = worker.user_id
    original_worker_name = worker.name

    check_in_worker(
        session=dbsession,
        worker_name=worker.name,
        cpu=8,
        memory=4096,
        disk=4096,
        selfish=True,
        offliners=[mwoffliner.id, ted_offliner.id],
        platforms=worker.platforms,
        user_id=worker.user_id,
        cordoned=True,
    )

    # Expire the worker to force a reload of the worker
    dbsession.expire(worker)
    updated_worker = get_worker(dbsession, worker_name=worker.name)

    assert updated_worker.name == original_worker_name
    assert updated_worker.cpu == 8
    assert updated_worker.memory == 4096
    assert updated_worker.disk == 4096
    assert updated_worker.selfish is True
    assert updated_worker.offliners == [mwoffliner.id, ted_offliner.id]
    assert updated_worker.platforms == worker.platforms
    assert updated_worker.user_id == original_user_id
    assert updated_worker.last_seen is not None
    assert original_last_seen is not None
    assert updated_worker.last_seen > original_last_seen
    assert updated_worker.last_ip == original_last_ip
    assert updated_worker.cordoned is True


def test_update_worker_context(dbsession: OrmSession, worker: Worker):
    """Test that update_worker_context updates the worker's context"""

    updated_worker = update_worker(
        dbsession, worker_name=worker.name, contexts={"priority": None, "general": None}
    )
    assert list(updated_worker.contexts.keys()) == ["priority", "general"]


@pytest.mark.parametrize(
    "admin_disabled, expected_admin_disabled",
    [
        pytest.param(True, True, id="True"),
        pytest.param(False, False, id="False"),
        pytest.param(None, False, id="None"),
    ],
)
def test_update_worker_scheduling_disabled(
    dbsession: OrmSession,
    worker: Worker,
    *,
    admin_disabled: bool | None,
    expected_admin_disabled: bool,
):
    updated_worker = update_worker(
        dbsession, worker_name=worker.name, admin_disabled=admin_disabled
    )
    assert updated_worker.admin_disabled is expected_admin_disabled
