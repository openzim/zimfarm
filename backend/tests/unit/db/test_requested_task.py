from uuid import UUID

import pytest
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.db.exceptions import RecordDoesNotExistError
from zimfarm_backend.db.models import RequestedTask, Schedule, Worker
from zimfarm_backend.db.requested_task import (
    compute_requested_task_rank,
    delete_requested_task,
    get_requested_task_by_id,
    get_requested_task_by_id_or_none,
    get_requested_tasks,
    request_task,
    update_requested_task_priority,
)


def test_request_task_nonexistent_schedule(dbsession: OrmSession, worker: Worker):
    """Test that request_task returns None for non-existent schedule"""
    result = request_task(
        session=dbsession,
        schedule_name="nonexistent",
        requested_by="testuser",
        worker_name=worker.name,
    )
    assert result is None


def test_request_task_nonexistent_worker(dbsession: OrmSession, schedule: Schedule):
    """Test that request_task returns None for non-existent worker"""
    result = request_task(
        session=dbsession,
        schedule_name=schedule.name,
        requested_by="testuser",
        worker_name="nonexistent",
    )
    assert result is None


def test_request_task_disabled_schedule(
    dbsession: OrmSession, schedule: Schedule, worker: Worker
):
    """Test that request_task returns None for disabled schedule"""
    schedule.enabled = False
    dbsession.add(schedule)
    dbsession.flush()

    result = request_task(
        session=dbsession,
        schedule_name=schedule.name,
        requested_by="testuser",
        worker_name=worker.name,
    )
    assert result is None


def test_get_requested_tasks(dbsession: OrmSession, requested_task: RequestedTask):
    """Test that get_requested_tasks returns the correct list of tasks"""
    result = get_requested_tasks(
        session=dbsession,
        skip=0,
        limit=10,
    )
    assert result.nb_records == 1
    assert len(result.requested_tasks) == 1
    task = result.requested_tasks[0]
    assert task.id == requested_task.id
    assert task.status == requested_task.status
    assert task.requested_by == requested_task.requested_by
    assert (
        task.worker.name
        == requested_task.worker.name  # pyright: ignore[reportOptionalMemberAccess]
    )
    assert task.schedule_name == requested_task.schedule.name


def test_get_requested_task_by_id_or_none(
    dbsession: OrmSession, requested_task: RequestedTask
):
    """Test that get_requested_task_by_id_or_none returns the task if it exists"""
    result = get_requested_task_by_id_or_none(dbsession, requested_task.id)
    assert result is not None
    assert result.id == requested_task.id


def test_get_requested_task_by_id_or_none_not_found(dbsession: OrmSession):
    """Test that get_requested_task_by_id_or_none returns None if task doesn't exist"""
    result = get_requested_task_by_id_or_none(dbsession, UUID(int=0))
    assert result is None


def test_get_requested_task_by_id(dbsession: OrmSession, requested_task: RequestedTask):
    """Test that get_requested_task_by_id returns the task if it exists"""
    result = get_requested_task_by_id(dbsession, requested_task.id)
    assert result.id == requested_task.id


def test_get_requested_task_by_id_not_found(dbsession: OrmSession):
    """Test that get_requested_task_by_id raises an exception if task doesn't exist"""
    with pytest.raises(RecordDoesNotExistError):
        get_requested_task_by_id(dbsession, UUID(int=0))


def test_compute_requested_task_rank(
    dbsession: OrmSession, requested_task: RequestedTask
):
    """Test that compute_requested_task_rank returns the correct rank"""
    rank = compute_requested_task_rank(dbsession, requested_task.id)
    assert rank == 0  # Should be first since it's the only task


def test_update_requested_task_priority(
    dbsession: OrmSession, requested_task: RequestedTask
):
    """Test that update_requested_task_priority updates the priority correctly"""
    new_priority = 5
    result = update_requested_task_priority(dbsession, requested_task.id, new_priority)
    assert result.priority == new_priority


def test_delete_requested_task(dbsession: OrmSession, requested_task: RequestedTask):
    """Test that delete_requested_task deletes the task"""
    delete_requested_task(dbsession, requested_task.id)
    result = get_requested_task_by_id_or_none(dbsession, requested_task.id)
    assert result is None
