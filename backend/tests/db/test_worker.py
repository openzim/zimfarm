import datetime
from collections.abc import Callable
from ipaddress import IPv4Address, IPv6Address
from uuid import uuid4

import pytest
from pytest import MonkeyPatch
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common import getnow
from zimfarm_backend.common.schemas.orms import BaseWorkerSchema, OfflinerSchema
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
        docker_image_hash=str(uuid4()),
        docker_image_created_at=getnow(),
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
        docker_image_hash=str(uuid4()),
        docker_image_created_at=getnow(),
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
    "ip_address, contexts, update_last_seen, admin_disabled, "
    "avail_disk, avail_memory, avail_cpu",
    [
        pytest.param(None, None, True, None, None, None, None, id="all_none"),
        pytest.param(
            "192.168.1.100", None, True, None, None, None, None, id="ip_address_set"
        ),
        pytest.param(None, None, True, None, None, None, None, id="ip_address_none"),
        pytest.param(
            None,
            {"priority": None, "general": None},
            True,
            None,
            None,
            None,
            None,
            id="contexts_set",
        ),
        pytest.param(
            None,
            {"priority": IPv4Address("10.0.0.1")},
            True,
            None,
            None,
            None,
            None,
            id="contexts_with_ip",
        ),
        pytest.param(None, None, True, None, None, None, None, id="contexts_none"),
        pytest.param(
            None, None, True, None, None, None, None, id="update_last_seen_true"
        ),
        pytest.param(
            None, None, False, None, None, None, None, id="update_last_seen_false"
        ),
        pytest.param(
            None, None, True, True, None, None, None, id="admin_disabled_true"
        ),
        pytest.param(
            None, None, True, False, None, None, None, id="admin_disabled_false"
        ),
        pytest.param(
            None, None, True, None, None, None, None, id="admin_disabled_none"
        ),
        pytest.param(None, None, True, None, 1024, None, None, id="avail_disk_set"),
        pytest.param(None, None, True, None, None, None, None, id="avail_disk_none"),
        pytest.param(None, None, True, None, None, 2048, None, id="avail_memory_set"),
        pytest.param(None, None, True, None, None, None, None, id="avail_memory_none"),
        pytest.param(None, None, True, None, None, None, 8, id="avail_cpu_set"),
        pytest.param(None, None, True, None, None, None, None, id="avail_cpu_none"),
        pytest.param(
            "192.168.1.200",
            {"test": None},
            True,
            True,
            2048,
            4096,
            16,
            id="multiple_params",
        ),
    ],
)
def test_update_worker(
    dbsession: OrmSession,
    worker: Worker,
    *,
    ip_address: str | None,
    contexts: dict[str, IPv4Address | IPv6Address | None] | None,
    update_last_seen: bool,
    admin_disabled: bool | None,
    avail_disk: int | None,
    avail_memory: int | None,
    avail_cpu: int | None,
):
    # Store original values
    original_last_seen = worker.last_seen
    original_last_ip = worker.last_ip
    original_contexts = worker.contexts.copy()
    original_admin_disabled = worker.admin_disabled
    original_disk = worker.disk
    original_memory = worker.memory
    original_cpu = worker.cpu

    updated_worker = update_worker(
        dbsession,
        worker_name=worker.name,
        ip_address=ip_address,
        contexts=contexts,
        update_last_seen=update_last_seen,
        admin_disabled=admin_disabled,
        avail_disk=avail_disk,
        avail_memory=avail_memory,
        avail_cpu=avail_cpu,
    )

    if update_last_seen:
        assert updated_worker.last_seen is not None
        if original_last_seen is not None:
            assert updated_worker.last_seen >= original_last_seen
    else:
        assert updated_worker.last_seen == original_last_seen

    if ip_address is not None:
        assert updated_worker.last_ip == IPv4Address(ip_address)
    else:
        assert updated_worker.last_ip == original_last_ip

    if contexts is not None:
        assert list(updated_worker.contexts.keys()) == list(contexts.keys())
    else:
        assert updated_worker.contexts == original_contexts

    if admin_disabled is not None:
        assert updated_worker.admin_disabled == admin_disabled
    else:
        assert updated_worker.admin_disabled == original_admin_disabled

    if avail_disk is not None:
        assert updated_worker.disk == avail_disk
    else:
        assert updated_worker.disk == original_disk

    if avail_memory is not None:
        assert updated_worker.memory == avail_memory
    else:
        assert updated_worker.memory == original_memory

    if avail_cpu is not None:
        assert updated_worker.cpu == avail_cpu
    else:
        assert updated_worker.cpu == original_cpu


@pytest.mark.parametrize(
    "contexts, last_ip, ip_changed",
    [
        pytest.param(
            {"wikipedia": None},
            None,
            False,
            id="context-and-worker-no-ip",
        ),
        pytest.param(
            {"wikipedia": IPv4Address("127.0.0.1")},
            None,
            True,
            id="worker-no-ip-context-ip",
        ),
        pytest.param(
            {"wikipedia": IPv4Address("127.0.0.1")},
            IPv4Address("127.0.0.1"),
            False,
            id="worker-and-context-same-ip",
        ),
        pytest.param(
            {"wikipedia": IPv4Address("127.0.0.1")},
            IPv4Address("127.0.0.2"),
            True,
            id="worker-and-context-different-ip",
        ),
        pytest.param(
            {"wikipedia": None},
            IPv4Address("127.0.0.2"),
            False,
            id="worker-has-ip-context-no-ip",
        ),
    ],
)
def test_worker_ip_changed(
    contexts: dict[str, IPv4Address | IPv6Address | None],
    last_ip: IPv4Address | None,
    *,
    ip_changed: bool,
):
    worker = BaseWorkerSchema(
        id=uuid4(),
        platforms={},
        name="test_worker",
        offliners=["mwoffliner"],
        cordoned=False,
        admin_disabled=False,
        contexts=contexts,
        last_ip=last_ip,
        selfish=False,
        docker_image=None,
    )
    assert worker.ip_changed is ip_changed
