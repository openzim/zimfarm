import datetime
from collections.abc import Callable

import pytest
from pytest import MonkeyPatch
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.background_tasks import cancel_tasks as cancel_tasks_module
from zimfarm_backend.background_tasks.cancel_tasks import cancel_incomplete_tasks
from zimfarm_backend.common import getnow
from zimfarm_backend.common.enums import TaskStatus
from zimfarm_backend.db.models import Task, User, Worker


def test_cancel_incomplete_tasks_stale_task(
    dbsession: OrmSession,
    create_task: Callable[..., Task],
    create_user: Callable[..., User],
    worker: Worker,
    monkeypatch: MonkeyPatch,
):
    """Test that cancel_incomplete_tasks requests cancellation for stale tasks"""
    now = getnow()
    monkeypatch.setattr(
        cancel_tasks_module,
        "STALLED_GONE_TIMEOUT",
        datetime.timedelta(hours=1).total_seconds(),
    )
    old_time = now - datetime.timedelta(hours=2)
    create_user(username="periodic-task-gone")

    task = create_task(status=TaskStatus.started)
    task.worker_id = worker.id
    task.updated_at = old_time
    worker.last_seen = now
    dbsession.add_all([task, worker])

    cancel_incomplete_tasks(dbsession)

    # Task should now have cancel_requested status
    dbsession.refresh(task)
    assert task.status == TaskStatus.cancel_requested


@pytest.mark.parametrize(
    "status",
    [
        TaskStatus.succeeded,
        TaskStatus.failed,
        TaskStatus.canceled,
    ],
    ids=["succeeded", "failed", "canceled"],
)
def test_cancel_incomplete_tasks_excludes_complete_statuses(
    dbsession: OrmSession,
    create_task: Callable[..., Task],
    worker: Worker,
    status: TaskStatus,
    monkeypatch: MonkeyPatch,
):
    """Test that cancel_incomplete_tasks excludes all complete task statuses"""
    now = getnow()
    monkeypatch.setattr(
        cancel_tasks_module,
        "STALLED_GONE_TIMEOUT",
        datetime.timedelta(hours=1).total_seconds(),
    )
    old_time = now - datetime.timedelta(hours=2)

    task = create_task(status=status)
    task.worker_id = worker.id
    task.updated_at = old_time
    worker.last_seen = now
    dbsession.add_all([task, worker])

    cancel_incomplete_tasks(dbsession)

    # Task should remain in its complete status
    dbsession.refresh(task)
    assert task.status == status


@pytest.mark.parametrize(
    "status",
    [
        TaskStatus.started,
        TaskStatus.reserved,
        TaskStatus.scraper_started,
        TaskStatus.scraper_running,
    ],
    ids=["started", "reserved", "scraper_started", "scraper_running"],
)
def test_cancel_incomplete_tasks_handles_various_incomplete_statuses(
    dbsession: OrmSession,
    create_task: Callable[..., Task],
    create_user: Callable[..., User],
    worker: Worker,
    status: TaskStatus,
    monkeypatch: MonkeyPatch,
):
    """Test that cancel_incomplete_tasks handles various incomplete statuses"""
    now = getnow()
    monkeypatch.setattr(
        cancel_tasks_module,
        "STALLED_GONE_TIMEOUT",
        datetime.timedelta(hours=1).total_seconds(),
    )
    old_time = now - datetime.timedelta(hours=2)
    create_user(username="periodic-task-gone")

    task = create_task(status=status)
    task.worker_id = worker.id
    task.updated_at = old_time
    worker.last_seen = now
    dbsession.add_all([task, worker])

    cancel_incomplete_tasks(dbsession)

    # Task should have cancel_requested status
    dbsession.refresh(task)
    assert task.status == TaskStatus.cancel_requested
    assert task.canceled_by is not None
    assert task.canceled_by.username == "periodic-task-gone"
