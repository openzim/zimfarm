from collections.abc import Callable
from uuid import UUID

import pytest
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common.enums import TaskStatus
from zimfarm_backend.db.exceptions import (
    RecordAlreadyExistsError,
    RecordDoesNotExistError,
)
from zimfarm_backend.db.models import RequestedTask, Task, Worker
from zimfarm_backend.db.requested_task import (
    _create_requested_task_full_schema,  # pyright: ignore[reportPrivateUsage]
)
from zimfarm_backend.db.tasks import (
    create_task,
    get_task_by_id,
    get_task_by_id_or_none,
    get_tasks,
)


def test_get_task_by_id_or_none(dbsession: OrmSession, task: Task):
    """Test that get_task_by_id_or_none returns the task if it exists"""
    result = get_task_by_id_or_none(dbsession, task.id)
    assert result is not None
    assert result.id == task.id


def test_get_task_by_id_or_none_not_found(dbsession: OrmSession):
    """Test that get_task_by_id_or_none returns None if task doesn't exist"""
    result = get_task_by_id_or_none(dbsession, UUID(int=0))
    assert result is None


def test_get_task_by_id(dbsession: OrmSession, task: Task):
    """Test that get_task_by_id returns the task if it exists"""
    result = get_task_by_id(dbsession, task.id)
    assert result.id == task.id


def test_get_task_by_id_not_found(dbsession: OrmSession):
    """Test that get_task_by_id raises an exception if task doesn't exist"""
    with pytest.raises(RecordDoesNotExistError):
        get_task_by_id(dbsession, UUID(int=0))


@pytest.mark.parametrize(
    "skip,limit,status,schedule_name,expected_nb_records",
    [
        # No filter
        (0, 5, None, None, 30),
        # Filter by status
        (0, 5, [TaskStatus.started], None, 10),
        (0, 5, [TaskStatus.started, TaskStatus.requested], None, 20),
        # Filter by schedule name
        (0, 5, None, "schedule_1", 10),
        (0, 5, None, "nonexistent", 0),
        # Combined filters
        (0, 5, [TaskStatus.requested], "schedule_1", 10),
    ],
    ids=[
        "no_filter",
        "filter_status_started",
        "filter_status_started_requested",
        "filter_schedule_name_schedule_1",
        "filter_schedule_name_nonexistent",
        "filter_status_requested_schedule_1",
    ],
)
def test_get_tasks(
    dbsession: OrmSession,
    create_task: Callable[..., Task],
    skip: int,
    limit: int,
    status: list[TaskStatus] | None,
    schedule_name: str | None,
    expected_nb_records: int,
):
    """Test that get_tasks returns the correct list of tasks"""

    # Create 10 tasks with status requested and schedule name "schedule_1"
    for _ in range(10):
        create_task(
            schedule_name="schedule_1",
            status=TaskStatus.requested,
        )

    # Create 10 tasks with status succeeded and schedule name "schedule_2"
    for _ in range(10):
        create_task(
            schedule_name="schedule_2",
            status=TaskStatus.succeeded,
        )

    # Create 10 tasks with status started and schedule name "schedule_3"
    for _ in range(10):
        create_task(
            schedule_name="schedule_3",
            status=TaskStatus.started,
        )

    result = get_tasks(
        session=dbsession,
        skip=skip,
        limit=limit,
        status=status,
        schedule_name=schedule_name,
    )
    assert result.nb_records == expected_nb_records
    assert len(result.tasks) <= limit


def test_create_task(
    dbsession: OrmSession,
    worker: Worker,
    create_requested_task: Callable[..., RequestedTask],
):
    """Test that create_task creates a task correctly"""

    requested_task = _create_requested_task_full_schema(
        dbsession, create_requested_task()
    )
    task = create_task(
        session=dbsession,
        requested_task=requested_task,
        worker_id=worker.id,
    )
    assert task.id == requested_task.id
    assert task.status == requested_task.status
    assert task.requested_by == requested_task.requested_by
    assert task.priority == requested_task.priority
    assert task.original_schedule_name == requested_task.original_schedule_name
    assert task.worker_name == worker.name


def test_create_task_already_exists(
    dbsession: OrmSession,
    worker: Worker,
    create_requested_task: Callable[..., RequestedTask],
):
    """Test that create_task raises an exception if task already exists"""
    requested_task = _create_requested_task_full_schema(
        dbsession, create_requested_task()
    )

    create_task(
        session=dbsession,
        requested_task=requested_task,
        worker_id=worker.id,
    )

    # Try to create the same task again
    with pytest.raises(RecordAlreadyExistsError):
        create_task(
            session=dbsession,
            requested_task=requested_task,
            worker_id=worker.id,
        )
