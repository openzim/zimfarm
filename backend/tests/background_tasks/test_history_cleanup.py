from collections.abc import Callable

from pytest import MonkeyPatch
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.background_tasks import history_cleanup as history_cleanup_module
from zimfarm_backend.background_tasks.history_cleanup import history_cleanup
from zimfarm_backend.db import count_from_stmt
from zimfarm_backend.db.models import Schedule, Task


def test_history_cleanup_schedule_with_few_tasks(
    dbsession: OrmSession,
    create_schedule: Callable[..., Schedule],
    create_task: Callable[..., Task],
    monkeypatch: MonkeyPatch,
):
    """Test that history_cleanup doesn't delete tasks when count is below threshold"""
    schedule = create_schedule()

    monkeypatch.setattr(history_cleanup_module, "HISTORY_TASK_PER_SCHEDULE", 10)
    # Create 5 tasks (below the default threshold of 10)
    for _ in range(5):
        create_task(schedule_name=schedule.name)
    history_cleanup(dbsession)

    # No tasks should be deleted
    assert count_from_stmt(dbsession, select(Task.id)) == 5


def test_history_cleanup_schedule_with_many_tasks(
    dbsession: OrmSession,
    create_schedule: Callable[..., Schedule],
    create_task: Callable[..., Task],
    monkeypatch: MonkeyPatch,
):
    """Test that history_cleanup deletes old tasks when count exceeds threshold"""
    monkeypatch.setattr(history_cleanup_module, "HISTORY_TASK_PER_SCHEDULE", 10)
    schedule = create_schedule()

    # Create 15 tasks (above the default threshold of 10)
    for _ in range(15):
        create_task(schedule_name=schedule.name)

    history_cleanup(dbsession)

    assert count_from_stmt(dbsession, select(Task.id)) == 10


def test_history_cleanup_multiple_schedules(
    dbsession: OrmSession,
    create_schedule: Callable[..., Schedule],
    create_task: Callable[..., Task],
    monkeypatch: MonkeyPatch,
):
    """Test that history_cleanup handles multiple schedules correctly"""
    monkeypatch.setattr(history_cleanup_module, "HISTORY_TASK_PER_SCHEDULE", 10)
    schedule1 = create_schedule(name="schedule_1")
    schedule2 = create_schedule(name="schedule_2")
    schedule3 = create_schedule(name="schedule_3")

    # Schedule 1: 15 tasks (should be cleaned)
    for _ in range(15):
        create_task(schedule_name=schedule1.name)

    # Schedule 2: 5 tasks (should not be cleaned)
    for _ in range(5):
        create_task(schedule_name=schedule2.name)

    # Schedule 3: 12 tasks (should be cleaned)
    for _ in range(12):
        create_task(schedule_name=schedule3.name)

    history_cleanup(dbsession)

    # Check each schedule
    assert (
        count_from_stmt(
            dbsession, select(Task.id).where(Task.schedule_id == schedule1.id)
        )
        == 10
    )

    assert (
        count_from_stmt(
            dbsession, select(Task.id).where(Task.schedule_id == schedule2.id)
        )
        == 5
    )

    assert (
        count_from_stmt(
            dbsession, select(Task.id).where(Task.schedule_id == schedule3.id)
        )
        == 10
    )
