import datetime
from collections.abc import Callable
from unittest.mock import patch

import pytest
from pytest import MonkeyPatch
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.background_tasks import cancel_tasks as cancel_tasks_module
from zimfarm_backend.background_tasks.cancel_tasks import (
    cancel_stale_tasks,
    cancel_stale_tasks_with_status,
    close_scraper_completed_tasks,
    remove_old_tasks,
)
from zimfarm_backend.background_tasks.constants import PERIODIC_TASK_NAME
from zimfarm_backend.common import getnow
from zimfarm_backend.common.enums import TaskStatus
from zimfarm_backend.db import count_from_stmt
from zimfarm_backend.db.models import Task, User


def test_cancel_stale_task_with_status(
    dbsession: OrmSession,
    create_task: Callable[..., Task],
    create_user: Callable[..., User],
):
    """Test that cancel_stale_tasks cancels tasks stuck in cancel_requested status"""
    now = getnow()
    create_user(username=PERIODIC_TASK_NAME)
    delta = datetime.timedelta(hours=1)
    old_time = now - delta
    task = create_task(status=TaskStatus.started)
    task.timestamp = [(TaskStatus.started, old_time)]
    dbsession.add(task)
    dbsession.flush()

    cancel_stale_tasks_with_status(
        dbsession, TaskStatus.started, now, delta.total_seconds()
    )

    # Task should now be canceled
    dbsession.refresh(task)
    assert task.status == TaskStatus.canceled
    assert task.canceled_by is not None
    assert task.canceled_by.username == PERIODIC_TASK_NAME


@pytest.mark.parametrize(
    "exit_code, expected_status", [(0, TaskStatus.succeeded), (1, TaskStatus.failed)]
)
def test_close_stale_scraper_completed_tasks(
    dbsession: OrmSession,
    create_task: Callable[..., Task],
    monkeypatch: MonkeyPatch,
    exit_code: int,
    expected_status: TaskStatus,
):
    """Test that stale scraper_completed tasks success status is updated"""
    now = getnow()
    monkeypatch.setattr(
        cancel_tasks_module,
        "STALLED_COMPLETED_TIMEOUT",
        datetime.timedelta(days=1).total_seconds(),
    )
    old_time = now - datetime.timedelta(days=2)

    task = create_task(status=TaskStatus.scraper_completed)
    task.timestamp = [(TaskStatus.scraper_completed, old_time)]
    task.container = {"exit_code": exit_code}
    dbsession.add(task)
    dbsession.flush()

    close_scraper_completed_tasks(dbsession, now)

    # Task should now be succeeded
    dbsession.refresh(task)
    assert task.status == expected_status


def test_cancel_stale_tasks(
    dbsession: OrmSession,
    create_user: Callable[..., User],
    create_task: Callable[..., Task],
    monkeypatch: MonkeyPatch,
):
    """Test that cancel_stale_tasks cancels tasks with stale statuses"""
    create_user(username=PERIODIC_TASK_NAME)
    now = getnow()
    monkeypatch.setattr(
        cancel_tasks_module,
        "STALLED_STARTED_TIMEOUT",
        datetime.timedelta(minutes=30).total_seconds(),
    )
    monkeypatch.setattr(
        cancel_tasks_module,
        "STALLED_RESERVED_TIMEOUT",
        datetime.timedelta(minutes=30).total_seconds(),
    )
    old_time = now - datetime.timedelta(hours=1)

    # Create tasks with different stale statuses
    task1 = create_task(status=TaskStatus.started)
    task1.timestamp = [(TaskStatus.started, old_time)]

    task2 = create_task(status=TaskStatus.reserved)
    task2.timestamp = [(TaskStatus.reserved, old_time)]

    dbsession.add_all([task1, task2])
    dbsession.flush()

    cancel_stale_tasks(dbsession)

    # Both tasks should be canceled
    dbsession.refresh(task1)
    dbsession.refresh(task2)
    assert task1.status == TaskStatus.canceled
    assert task2.status == TaskStatus.canceled


def test_cancel_stale_tasks_continues_on_error(
    dbsession: OrmSession,
    create_task: Callable[..., Task],
    monkeypatch: MonkeyPatch,
):
    """Test that cancel_stale_tasks continues processing even if one status fails"""
    now = getnow()
    monkeypatch.setattr(
        cancel_tasks_module,
        "STALLED_RESERVED_TIMEOUT",
        datetime.timedelta(minutes=30).total_seconds(),
    )
    old_time = now - datetime.timedelta(hours=1)

    # Create a task that should be canceled
    task = create_task(status=TaskStatus.reserved)
    task.timestamp = [(TaskStatus.reserved, old_time)]
    dbsession.add(task)
    dbsession.flush()

    # Mock one of the cancel functions to raise an exception
    with patch(
        "zimfarm_backend.background_tasks.cancel_tasks.cancel_stale_tasks_with_status"
    ) as mock_cancel:
        # First call (started) raises exception, second call (reserved) works normally
        mock_cancel.side_effect = [
            Exception("Test error"),
            None,  # This would be the reserved status call
            None,  # This would be the canceled status call
        ]

        # Should not raise despite the error
        cancel_stale_tasks(dbsession)


def test_remove_old_tasks_disabled(
    dbsession: OrmSession,
    create_task: Callable[..., Task],
    monkeypatch: MonkeyPatch,
):
    """Test that remove_old_tasks does nothing when deletion is disabled"""
    monkeypatch.setattr(cancel_tasks_module, "OLD_TASK_DELETION_ENABLED", False)
    monkeypatch.setattr(
        cancel_tasks_module,
        "OLD_TASK_DELETION_THRESHOLD",
        datetime.timedelta(days=10),
    )

    now = getnow()
    old_time = now - datetime.timedelta(days=15)

    task = create_task(status=TaskStatus.succeeded)
    task.updated_at = old_time
    dbsession.add(task)
    dbsession.flush()

    remove_old_tasks(dbsession)

    # Task should still exist
    dbsession.refresh(task)
    assert task is not None


def test_remove_old_tasks_enabled(
    dbsession: OrmSession,
    create_task: Callable[..., Task],
    monkeypatch: MonkeyPatch,
):
    """Test that remove_old_tasks deletes old tasks when enabled"""
    monkeypatch.setattr(cancel_tasks_module, "OLD_TASK_DELETION_ENABLED", True)
    monkeypatch.setattr(
        cancel_tasks_module,
        "OLD_TASK_DELETION_THRESHOLD",
        datetime.timedelta(days=10),
    )

    now = getnow()
    old_time = now - datetime.timedelta(days=15)

    task = create_task(status=TaskStatus.succeeded)
    task.updated_at = old_time
    task_id = task.id
    dbsession.add(task)
    dbsession.flush()

    remove_old_tasks(dbsession)
    dbsession.flush()

    assert count_from_stmt(dbsession, select(Task).where(Task.id == task_id)) == 0
