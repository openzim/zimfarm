from collections.abc import Callable
from uuid import UUID, uuid4

import pytest
from pytest import MonkeyPatch
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common import getnow
from zimfarm_backend.common.enums import TaskStatus
from zimfarm_backend.common.schemas.models import ScheduleConfigSchema
from zimfarm_backend.common.schemas.orms import ScheduleDurationSchema
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
from zimfarm_backend.utils.offliners import expanded_config
from zimfarm_backend.utils.timestamp import get_timestamp_for_status


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


def test_request_task_already_requested(
    dbsession: OrmSession,
    create_requested_task: Callable[..., RequestedTask],
    worker: Worker,
    schedule: Schedule,
):
    """Test that request_task returns None for already requested task"""
    # Create a requested task
    create_requested_task(
        worker=worker,
        schedule_name=schedule.name,
    )
    result = request_task(
        session=dbsession,
        schedule_name=schedule.name,
        requested_by="testuser",
        worker_name=worker.name,
    )
    assert result is None


def test_request_task_if_worker_has_no_requested_task(
    dbsession: OrmSession,
    worker: Worker,
    schedule: Schedule,
):
    """Test that request_task returns the task if it's not already requested"""
    result = request_task(
        session=dbsession,
        schedule_name=schedule.name,
        requested_by="testuser",
        worker_name=worker.name,
    )
    assert result is not None


@pytest.mark.parametrize(
    [
        "worker_name",
        "matching_offliners",
        "schedule_name",
        "priority",
        "cpu",
        "memory",
        "disk",
        "expeted_nb_records",
    ],
    [
        # No filter
        pytest.param(
            None,  # worker_name
            None,  # matching_offliners
            None,  # schedule_name
            None,  # priority
            None,  # cpu
            None,  # memory
            None,  # disk
            30,  # expected nb records
            id="no_filter",
        ),
        # Filter by worker name
        pytest.param(
            "nonexistent",  # worker_name
            None,  # matching_offliners
            None,  # schedule_name
            None,  # priority
            None,  # cpu
            None,  # memory
            None,  # disk
            0,  # expected nb records
            id="filter_nonexistent_worker_name",
        ),
        # Filter by matching offliners
        pytest.param(
            None,
            ["mwoffliner"],
            None,  # schedule_name
            None,  # priority
            None,  # cpu
            None,  # memory
            None,  # disk
            30,  # expected nb records
            id="filter_matching_offliner_mwoffliner",
        ),
        pytest.param(
            None,  # worker_name
            ["youtube"],
            None,  # schedule_name
            None,  # priority
            None,  # cpu
            None,  # memory
            None,  # disk
            0,  # expected nb records
            id="filter_matching_offliner_youtube",
        ),
        pytest.param(
            None,  # worker_name
            ["youtube", "mwoffliner"],
            None,  # schedule_name
            None,  # priority
            None,  # cpu
            None,  # memory
            None,  # disk
            30,  # expected nb records
            id="filter_matching_offliner_youtube_mwoffliner",
        ),
        # Filter by schedule name
        pytest.param(
            None,  # worker_name
            ["mwoffliner"],  # matching_offliners
            ["schedule_1"],  # schedule_name
            None,  # priority
            None,  # cpu
            None,  # memory
            None,  # disk
            10,  # expected nb records
            id="filter_schedule_name_schedule_1_mw_offliner",
        ),
        pytest.param(
            None,  # worker_name
            ["mwoffliner"],  # matching_offliners
            ["schedule_2", "schedule_3"],  # schedule_name
            None,  # priority
            None,  # cpu
            None,  # memory
            None,  # disk
            20,
            id="filter_schedule_name_schedule_2_3_mw_offliner",
        ),
        pytest.param(
            None,  # worker_name
            ["mwoffliner"],  # matching_offliners
            ["schedule_5"],  # schedule_name
            None,  # priority
            None,  # cpu
            None,  # memory
            None,  # disk
            0,  # expected nb records
            id="filter_schedule_name_schedule_5_mw_offliner",
        ),
        # Filter by
        pytest.param(
            None,
            None,
            None,
            1,  # priority
            None,  # cpu
            None,  # memory
            None,  # disk
            10,  # expected nb records
            id="filter_priority_1",
        ),
        # Filter by resource keys
        pytest.param(
            None,
            None,
            None,
            None,  # priority
            1,  # cpu
            None,  # memory
            None,  # disk
            20,  # expected nb records
            id="filter_resource_keys_cpu_1",
        ),
        pytest.param(
            None,
            None,
            None,
            None,  # priority
            2,  # cpu
            None,  # memory
            None,  # disk
            30,  # expected nb records
            id="filter_resource_keys_cpu_2",
        ),
        pytest.param(
            None,
            ["mwoffliner"],
            ["schedule_3"],
            1,
            1,
            1024,
            1024,
            10,
            id="filter_resource_keys_cpu_1_memory_1_disk_1_mw_offliner",
        ),
    ],
)
def test_get_requested_tasks(
    dbsession: OrmSession,
    create_requested_task: Callable[..., RequestedTask],
    create_schedule_config: Callable[..., ScheduleConfigSchema],
    worker_name: str | None,
    matching_offliners: list[str] | None,
    schedule_name: list[str] | None,
    priority: int | None,
    cpu: int | None,
    memory: int | None,
    disk: int | None,
    expeted_nb_records: int,
):
    """Test that get_requested_tasks returns the correct list of tasks"""

    # Create 20 requested tasks with cpu 2, memory 2GB, disk 2GB with schedule
    # name of "schedule_1"
    requested_tasks: list[RequestedTask] = []
    schedule_config = create_schedule_config(cpu=2, memory=2 * 1024, disk=2 * 1024)
    for _ in range(10):
        requested_tasks.append(
            create_requested_task(
                schedule_config=schedule_config, schedule_name="schedule_1", priority=0
            )
        )

    # Create 10 requested tasks with cpu 1, memory 1GB, disk 1GB
    # with schedule name of "schedule_2"
    schedule_config = create_schedule_config(cpu=1, memory=1 * 1024, disk=1 * 1024)
    for _ in range(10):
        requested_tasks.append(
            create_requested_task(
                schedule_config=schedule_config, schedule_name="schedule_2", priority=0
            )
        )

    # Create 10 requested tasks with cpu 1, memory 1GB, disk 1GB, and priority 1
    # with schedule name of "schedule_3"
    schedule_config = create_schedule_config(cpu=1, memory=1 * 1024, disk=1 * 1024)
    for _ in range(10):
        requested_tasks.append(
            create_requested_task(
                schedule_config=schedule_config, schedule_name="schedule_3", priority=1
            )
        )

    limit = 5
    result = get_requested_tasks(
        session=dbsession,
        skip=0,
        limit=limit,
        worker_name=worker_name,
        matching_offliners=matching_offliners,
        schedule_name=schedule_name,
        priority=priority,
        cpu=cpu,
        memory=memory,
        disk=disk,
    )
    assert len(requested_tasks) == 30
    assert result.nb_records == expeted_nb_records
    assert len(result.requested_tasks) <= limit

    # simulate the filtering as it is done in the get_requested_tasks function
    if worker_name is not None:
        requested_tasks = [
            task
            for task in requested_tasks
            if task.worker.name  # pyright: ignore[reportOptionalMemberAccess]
            == worker_name
        ]
    if matching_offliners is not None:
        requested_tasks = [
            task
            for task in requested_tasks
            if task.config["offliner"]["offliner_id"] in matching_offliners
        ]
    if schedule_name is not None:
        requested_tasks = [
            task
            for task in requested_tasks
            if task.schedule.name  # pyright: ignore[reportOptionalMemberAccess]
            in schedule_name
        ]
    if priority is not None:
        requested_tasks = [
            task for task in requested_tasks if task.priority >= priority
        ]
    if cpu is not None:
        requested_tasks = [
            task for task in requested_tasks if task.config["resources"]["cpu"] <= cpu
        ]
    if memory is not None:
        requested_tasks = [
            task
            for task in requested_tasks
            if task.config["resources"]["memory"] <= memory
        ]
    if disk is not None:
        requested_tasks = [
            task for task in requested_tasks if task.config["resources"]["disk"] <= disk
        ]

    # Sort the tasks as they are done in the get_requested_tasks function
    requested_tasks.sort(
        key=lambda x: (
            -x.priority,
            get_timestamp_for_status(x.timestamp, TaskStatus.reserved),
            get_timestamp_for_status(x.timestamp, TaskStatus.requested),
        )
    )

    for task, requested_task in zip(
        result.requested_tasks, requested_tasks, strict=False
    ):
        assert task.id == requested_task.id
        assert task.status == requested_task.status
        assert task.requested_by == requested_task.requested_by
        assert (
            task.worker_name
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
        timestamp=[("requested", getnow()), ("reserved", getnow())],
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


def test_get_currently_running_tasks(
    dbsession: OrmSession, worker: Worker, create_task: Callable[..., Task]
):
    """Test that get_currently_running_tasks returns correct list of tasks"""
    # Create a running task
    create_task(worker=worker)
    running_tasks = get_currently_running_tasks(dbsession, worker)
    assert len(running_tasks) == 1
    assert running_tasks[0].worker_name == worker.name


def test_get_tasks_doable_by_worker(
    dbsession: OrmSession,
    worker: Worker,
    create_schedule_config: Callable[..., ScheduleConfigSchema],
):
    """Test that get_tasks_doable_by_worker returns correct list of tasks"""
    # Create a task that matches worker's capabilities
    schedule_config = create_schedule_config(
        cpu=worker.cpu, memory=worker.memory, disk=worker.disk
    )
    task = RequestedTask(
        status=TaskStatus.requested,
        timestamp=[("requested", getnow()), ("reserved", getnow())],
        events=[{"code": TaskStatus.requested, "timestamp": getnow()}],
        requested_by=worker.user.username,
        priority=0,
        config=expanded_config(schedule_config).model_dump(
            mode="json", context={"show_secrets": True}
        ),
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


def test_does_platform_allow_worker_to_run(
    worker: Worker,
    create_schedule_config: Callable[..., ScheduleConfigSchema],
):
    """Test to check that platform correctly validates platform constraints"""
    # Create a task with platform constraints
    schedule_config = create_schedule_config(
        cpu=worker.cpu, memory=worker.memory, disk=worker.disk
    )
    task = RequestedTaskWithDuration(
        id=uuid4(),
        status=TaskStatus.requested,
        config=expanded_config(schedule_config),
        timestamp=[("requested", getnow()), ("reserved", getnow())],
        requested_by=worker.user.username,
        priority=0,
        schedule_name="test_schedule",
        original_schedule_name="test_schedule",
        worker_name=worker.name,
        context="",
        duration=ScheduleDurationSchema(
            value=3600,
            on=getnow(),
            default=True,
            worker_name=worker.name,
        ),
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
        config=expanded_config(schedule_config),
        schedule_name="test_schedule",
        timestamp=[("started", getnow()), ("reserved", getnow())],
        worker_name=worker.name,
        duration=ScheduleDurationSchema(
            value=3600,
            on=getnow(),
            default=True,
            worker_name=worker.name,
        ),
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
    dbsession: OrmSession,
    worker: Worker,
    user: User,
    create_schedule_config: Callable[..., ScheduleConfigSchema],
):
    """Test that find_requested_task_for_worker finds the optimal task for a worker"""

    # Create a task that matches worker's capabilities
    schedule_config = create_schedule_config(
        cpu=worker.cpu, memory=worker.memory, disk=worker.disk
    )
    task = RequestedTask(
        status="requested",
        timestamp=[("requested", getnow()), ("reserved", getnow())],
        events=[{"code": "requested", "timestamp": getnow()}],
        requested_by=worker.user.username,
        priority=0,
        config=expanded_config(schedule_config).model_dump(
            mode="json", context={"show_secrets": True}
        ),
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
        username=worker.user.username,
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
            username=worker.user.username,
            worker_name="nonexistent",
            avail_cpu=worker.cpu,
            avail_memory=worker.memory,
            avail_disk=worker.disk,
        )


@pytest.mark.parametrize(
    "schedule_context,worker_contexts,found",
    [
        # worker has priority context, schedule has priority context
        # so the task should be assigned to worker
        pytest.param(
            "priority",
            ["priority", "general"],
            True,
            id="schedule-priority-worker-priority-general",
        ),
        # schedule has priority context, worker has general context
        # so the task should not be assigned to worker
        pytest.param(
            "priority",
            ["general"],
            False,
            id="schedule-priority-worker-general",
        ),
        # schedule has no context but worker has contexts, worker should still
        # be assigned to the task
        pytest.param(
            "",
            ["priority", "general"],
            True,
            id="schedule-no-context-worker-priority-general",
        ),
        # schedule has context while worker does not have context, so worker should
        # not be assigned to the task
        pytest.param(
            "priority",
            [],
            False,
            id="schedule-priority-worker-no-context",
        ),
        # both schedule and worker have no context, so the task should be assigned
        # to worker
        pytest.param(
            "",
            [],
            True,
            id="schedule-no-context-worker-no-context",
        ),
    ],
)
def test_find_requested_task_for_worker_with_schedule_(
    dbsession: OrmSession,
    worker: Worker,
    user: User,
    create_schedule_config: Callable[..., ScheduleConfigSchema],
    schedule_context: str,
    worker_contexts: list[str],
    *,
    found: bool,
):
    # Create a task that matches worker's capabilities
    schedule_config = create_schedule_config(
        cpu=worker.cpu, memory=worker.memory, disk=worker.disk
    )
    # Create a requested tag with specific tags
    task = RequestedTask(
        status="requested",
        timestamp=[("requested", getnow()), ("reserved", getnow())],
        events=[{"code": "requested", "timestamp": getnow()}],
        requested_by=worker.user.username,
        priority=0,
        config=expanded_config(schedule_config).model_dump(
            mode="json", context={"show_secrets": True}
        ),
        upload={},
        notification={},
        updated_at=getnow(),
        original_schedule_name="test_schedule",
        context=schedule_context,
    )
    worker.contexts = worker_contexts
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
    assert bool(found_task) == found
