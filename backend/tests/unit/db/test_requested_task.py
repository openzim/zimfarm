from uuid import UUID, uuid4

import pytest
from pytest import MonkeyPatch
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common import getnow
from zimfarm_backend.common.enums import TaskStatus
from zimfarm_backend.db.exceptions import RecordDoesNotExistError
from zimfarm_backend.db.models import RequestedTask, Schedule, Task, User, Worker
from zimfarm_backend.db.requested_task import (
    RequestedTaskWithDuration,
    RunningTask,
    compute_requested_task_rank,
    delete_requested_task,
    does_platform_allow_worker_to_run,
    find_requested_task_for_worker,
    get_currently_running_tasks,
    get_requested_task_by_id,
    get_requested_task_by_id_or_none,
    get_requested_tasks,
    get_tasks_doable_by_worker,
    request_task,
    update_requested_task_priority,
)


@pytest.fixture(autouse=True)
def set_worker_platform_limit(monkeypatch: MonkeyPatch, worker: Worker) -> None:
    """Set environment variables for worker platform limits"""
    for platform in worker.offliners:
        monkeypatch.setenv(f"PLATFORM_{platform}_MAX_TASKS_PER_WORKER", "10")
        monkeypatch.setenv(f"PLATFORM_{platform}_MAX_TASKS_TOTAL", "100")


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


def test_compute_requested_task_rank_with_multiple_tasks(
    dbsession: OrmSession, requested_task: RequestedTask
):
    """Test that compute_requested_task_rank works with multiple tasks"""
    # Create another task with different priority
    new_task = RequestedTask(
        status="requested",
        timestamp={"requested": getnow(), "reserved": getnow()},
        events=[{"code": "requested", "timestamp": getnow()}],
        requested_by="testuser2",
        priority=requested_task.priority + 1,  # Higher priority
        config=requested_task.config,
        upload=requested_task.upload,
        notification={},
        updated_at=getnow(),
        original_schedule_name=requested_task.schedule.name,  # pyright: ignore[reportOptionalMemberAccess]
    )
    new_task.schedule = requested_task.schedule
    new_task.worker = requested_task.worker
    dbsession.add(new_task)
    dbsession.flush()

    # Original task should have rank 1 (lower priority)
    assert compute_requested_task_rank(dbsession, requested_task.id) == 1
    # New task should have rank 0 (higher priority)
    assert compute_requested_task_rank(dbsession, new_task.id) == 0


def test_get_currently_running_tasks(dbsession: OrmSession, worker: Worker):
    """Test that get_currently_running_tasks returns correct list of tasks"""
    # Create a running task
    task = Task(
        status=TaskStatus.started,
        debug={},
        canceled_by=None,
        container={},
        files={},
        timestamp={"started": getnow(), "reserved": getnow()},
        events=[{"code": TaskStatus.started, "timestamp": getnow()}],
        requested_by="testuser",
        priority=0,
        config={
            "task_name": "test_task",
            "resources": {"cpu": 1, "memory": 1, "disk": 1},
        },
        upload={},
        notification={},
        updated_at=getnow(),
        original_schedule_name="test_schedule",
    )
    task.worker = worker
    dbsession.add(task)
    dbsession.flush()

    running_tasks = get_currently_running_tasks(dbsession, worker)
    assert len(running_tasks) == 1
    assert running_tasks[0].worker_name == worker.name


def test_get_tasks_doable_by_worker(dbsession: OrmSession, worker: Worker):
    """Test that get_tasks_doable_by_worker returns correct list of tasks"""
    # Create a task that matches worker's capabilities
    task = RequestedTask(
        status=TaskStatus.requested,
        timestamp={"requested": getnow(), "reserved": getnow()},
        events=[{"code": TaskStatus.requested, "timestamp": getnow()}],
        requested_by="testuser",
        priority=0,
        config={
            "task_name": worker.offliners[0],
            "resources": {
                "cpu": worker.cpu,
                "memory": worker.memory,
                "disk": worker.disk,
            },
        },
        upload={},
        notification={},
        updated_at=getnow(),
        original_schedule_name="test_schedule",
    )
    task.worker = worker
    dbsession.add(task)
    dbsession.flush()

    doable_tasks = get_tasks_doable_by_worker(dbsession, worker)
    assert len(doable_tasks) == 1
    assert doable_tasks[0].worker_name == worker.name


def test_does_platform_allow_worker_to_run(worker: Worker):
    """Test to check that platform correctly validates platform constraints"""
    # Create a task with platform constraints
    task = RequestedTaskWithDuration(
        id=uuid4(),
        status=TaskStatus.requested,
        config={"platform": worker.offliners[0]},
        timestamp={"requested": getnow(), "reserved": getnow()},
        requested_by="testuser",
        priority=0,
        schedule_name="test_schedule",
        original_schedule_name="test_schedule",
        worker_name=worker.name,
        duration={"value": 3600},
        updated_at=getnow(),
    )

    # Test with no running tasks
    assert does_platform_allow_worker_to_run(
        worker=worker,
        all_running_tasks=[],
        running_tasks=[],
        task=task,
    )

    # Test with platform limit reached
    running_task = RunningTask(
        config={"platform": worker.offliners[0]},
        schedule_name="test_schedule",
        timestamp={"started": getnow(), "reserved": getnow()},
        worker_name=worker.name,
        duration={"value": 3600},
        remaining=1800,
        eta=getnow(),
    )
    assert not does_platform_allow_worker_to_run(
        worker=worker,
        all_running_tasks=[running_task]
        * 1000,  # Set to exceed the platform limit from fixture
        running_tasks=[running_task] * 1000,
        task=task,
    )


def test_find_requested_task_for_worker(
    dbsession: OrmSession, worker: Worker, user: User
):
    """Test that find_requested_task_for_worker finds the optimal task for a worker"""

    # Create a task that matches worker's capabilities
    task = RequestedTask(
        status="requested",
        timestamp={"requested": getnow(), "reserved": getnow()},
        events=[{"code": "requested", "timestamp": getnow()}],
        requested_by="testuser",
        priority=0,
        config={
            "task_name": worker.offliners[0] if worker.offliners else "test_task",
            "resources": {
                "cpu": worker.cpu,
                "memory": worker.memory,
                "disk": worker.disk,
            },
        },
        upload={},
        notification={},
        updated_at=getnow(),
        original_schedule_name="test_schedule",
    )
    task.worker = worker
    dbsession.add(task)
    dbsession.flush()

    # Test finding task with sufficient resources
    found_task = find_requested_task_for_worker(
        session=dbsession,
        username=user.username,
        worker_name=worker.name,
        avail_cpu=worker.cpu,
        avail_memory=worker.memory,
        avail_disk=worker.disk,
    )
    assert found_task is not None
    assert found_task.id == task.id

    # Test finding task with insufficient resources
    found_task = find_requested_task_for_worker(
        session=dbsession,
        username="testuser",
        worker_name=worker.name,
        avail_cpu=0,
        avail_memory=0,
        avail_disk=0,
    )
    assert found_task is None

    # Test with non-existent worker
    with pytest.raises(RecordDoesNotExistError):
        find_requested_task_for_worker(
            session=dbsession,
            username="testuser",
            worker_name="nonexistent",
            avail_cpu=worker.cpu,
            avail_memory=worker.memory,
            avail_disk=worker.disk,
        )
