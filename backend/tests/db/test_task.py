from collections.abc import Callable
from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common import getnow
from zimfarm_backend.common.enums import TaskStatus
from zimfarm_backend.common.schemas.models import FileCreateUpdateSchema
from zimfarm_backend.db.exceptions import (
    RecordAlreadyExistsError,
    RecordDoesNotExistError,
)
from zimfarm_backend.db.models import File, RequestedTask, Task, Worker
from zimfarm_backend.db.requested_task import (
    create_requested_task_full_schema,  # pyright: ignore[reportPrivateUsage]
)
from zimfarm_backend.db.tasks import (
    create_or_update_task_file,
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
        (0, 5, None, None, 3),
        # Filter by status
        (0, 5, [TaskStatus.started], None, 1),
        (0, 5, [TaskStatus.started, TaskStatus.requested], None, 2),
        # Filter by schedule name
        (0, 5, None, "schedule_1", 1),
        (0, 5, None, "nonexistent", 0),
        # Combined filters
        (0, 5, [TaskStatus.requested], "schedule_1", 1),
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

    create_task(
        schedule_name="schedule_1",
        status=TaskStatus.requested,
    )

    create_task(
        schedule_name="schedule_2",
        status=TaskStatus.succeeded,
    )

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

    requested_task = create_requested_task_full_schema(
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
    requested_task = create_requested_task_full_schema(
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


def test_create_or_update_task_file_create_minimal(dbsession: OrmSession, task: Task):
    """Test creating a new file with minimal required fields"""
    create_or_update_task_file(
        dbsession,
        FileCreateUpdateSchema(
            task_id=task.id,
            name="test_file.zim",
            status="created",
        ),
    )
    dbsession.flush()

    # Verify the file was created
    result = dbsession.execute(
        select(File).where(File.task_id == task.id, File.name == "test_file.zim")
    ).scalar_one()

    assert result.name == "test_file.zim"
    assert result.status == "created"
    assert result.size is None
    assert result.info == {}


def test_create_or_update_task_file_create_with_all_fields(
    dbsession: OrmSession, task: Task
):
    """Test creating a new file with all fields populated"""
    now = getnow()
    create_or_update_task_file(
        dbsession,
        FileCreateUpdateSchema(
            task_id=task.id,
            name="complete_file.zim",
            status="uploaded",
            size=1024000,
            cms_on=now,
            cms_notified=True,
            created_timestamp=now,
            uploaded_timestamp=now,
            failed_timestamp=None,
            check_timestamp=now,
            check_result=0,
            check_log="All checks passed",
            check_details={"validation": "success"},
            info={"custom": "data"},
        ),
    )
    dbsession.flush()

    # Verify all fields were set
    result = dbsession.execute(
        select(File).where(File.task_id == task.id, File.name == "complete_file.zim")
    ).scalar_one()

    assert result.name == "complete_file.zim"
    assert result.status == "uploaded"
    assert result.size == 1024000
    assert result.cms_on == now
    assert result.cms_notified is True
    assert result.created_timestamp == now
    assert result.uploaded_timestamp == now
    assert result.failed_timestamp is None
    assert result.check_timestamp == now
    assert result.check_result == 0
    assert result.check_log == "All checks passed"
    assert result.check_details == {"validation": "success"}
    assert result.info == {"custom": "data"}


def test_create_or_update_task_file_update_existing(dbsession: OrmSession, task: Task):
    """Test updating an existing file"""
    # Create initial file
    create_or_update_task_file(
        dbsession,
        FileCreateUpdateSchema(
            task_id=task.id,
            name="update_test.zim",
            status="created",
            size=1000,
            info={"version": "1"},
            cms_notified=False,
        ),
    )
    dbsession.flush()

    # Update the file
    create_or_update_task_file(
        dbsession,
        FileCreateUpdateSchema(
            task_id=task.id,
            name="update_test.zim",
            status="uploaded",
            info={"version": "2"},
        ),
    )
    dbsession.flush()

    # Verify the file was updated with unset fields unchanged
    result = dbsession.execute(
        select(File).where(File.task_id == task.id, File.name == "update_test.zim")
    ).scalar_one()

    assert result.cms_notified is False
    assert result.size == 1000
    assert result.status == "uploaded"
    assert result.info == {"version": "2"}
