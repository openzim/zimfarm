import datetime
from collections.abc import Callable

import pytest
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common.enums import (
    ScheduleCategory,
    SchedulePeriodicity,
    TaskStatus,
)
from zimfarm_backend.common.schemas.models import ScheduleConfigSchema
from zimfarm_backend.common.schemas.orms import LanguageSchema
from zimfarm_backend.db.exceptions import RecordDoesNotExistError
from zimfarm_backend.db.models import (
    RequestedTask,
    Schedule,
    Task,
    Worker,
)
from zimfarm_backend.db.schedule import (
    DEFAULT_SCHEDULE_DURATION,
    count_enabled_schedules,
    create_schedule,
    create_schedule_full_schema,
    delete_schedule,
    get_all_schedules,
    get_schedule,
    get_schedule_duration,
    get_schedule_or_none,
    get_schedules,
    update_schedule,
    update_schedule_duration,
)


def test_get_schedule_or_none(dbsession: OrmSession):
    """Test that get_schedule_or_none returns None if the schedule does not exist"""
    schedule = get_schedule_or_none(dbsession, schedule_name="nonexistent")
    assert schedule is None


def test_get_schedule_not_found(dbsession: OrmSession):
    """Test that get_schedule raises an exception if the schedule does not exist"""
    with pytest.raises(RecordDoesNotExistError):
        get_schedule(dbsession, schedule_name="nonexistent")


def test_get_schedule(dbsession: OrmSession, schedule: Schedule):
    """Test that get_schedule returns the schedule if it exists"""
    db_schedule = get_schedule(dbsession, schedule_name=schedule.name)
    assert db_schedule is not None
    assert db_schedule.name == schedule.name


@pytest.mark.parametrize(
    "schedule_name, expected_count",
    [(["nonexistent"], 0), (["testschedule"], 1), (["testschedule", "nonexistent"], 1)],
)
def test_count_enabled_schedules(
    dbsession: OrmSession,
    schedule: Schedule,  # noqa: ARG001
    schedule_name: list[str],
    expected_count: int,
):
    """Test that count_enabled_schedules returns the correct count"""
    count = count_enabled_schedules(dbsession, schedule_name)
    assert count == expected_count


def test_get_schedule_duration_default(dbsession: OrmSession, worker: Worker):
    """Test that returns default duration when no specific duration exists"""
    duration = get_schedule_duration(
        dbsession, schedule_name="nonexistent", worker=worker
    )
    assert duration.value > 0
    assert duration.worker_name is None
    assert isinstance(duration.on, datetime.datetime)


def test_get_schedule_duration_with_worker(
    dbsession: OrmSession,
    create_schedule: Callable[..., Schedule],
    worker: Worker,
):
    """Returns worker-specific duration when schedule exists"""
    schedule = create_schedule(worker=worker)
    duration = get_schedule_duration(
        dbsession, schedule_name=schedule.name, worker=worker
    )
    assert duration.value == schedule.durations[0].value
    assert duration.worker_name is not None
    assert duration.worker_name == worker.name
    assert duration.on == schedule.durations[0].on


def test_create_schedule(
    dbsession: OrmSession, create_schedule_config: Callable[..., ScheduleConfigSchema]
):
    """Test that create_schedule creates a schedule with the correct duration"""
    schedule_config = create_schedule_config(cpu=1, memory=2**10, disk=2**10)
    schedule = create_schedule(
        session=dbsession,
        name="test_schedule",
        category=ScheduleCategory.other,
        language=LanguageSchema(code="en", name_en="English", name_native="English"),
        config=schedule_config,
        tags=["test"],
        enabled=True,
        notification=None,
        periodicity=SchedulePeriodicity.manually,
    )
    assert schedule.name == "test_schedule"
    assert schedule.category == ScheduleCategory.other
    assert schedule.language_code == "en"
    assert schedule.language_name_en == "English"
    assert schedule.language_name_native == "English"
    assert schedule.config == schedule_config.model_dump(
        mode="json", context={"show_secrets": True}
    )
    assert schedule.tags == ["test"]
    assert schedule.enabled
    assert schedule.notification is None
    assert schedule.periodicity == SchedulePeriodicity.manually
    assert len(schedule.durations) == 1
    assert schedule.durations[0].value == DEFAULT_SCHEDULE_DURATION.value
    assert schedule.durations[0].on == DEFAULT_SCHEDULE_DURATION.on
    assert schedule.durations[0].worker is None
    assert schedule.durations[0].default


def test_get_all_schedules(
    dbsession: OrmSession, create_schedule: Callable[..., Schedule]
):
    """Test that get_all_schedules returns all schedules"""
    schedule = create_schedule()
    results = get_all_schedules(dbsession)
    assert results.nb_records == 1
    assert results.schedules[0].name == schedule.name


def test_update_schedule(
    dbsession: OrmSession,
    create_schedule: Callable[..., Schedule],
    create_schedule_config: Callable[..., ScheduleConfigSchema],
):
    """Test that update_schedule updates a schedule"""
    old_schedule = create_schedule_full_schema(create_schedule())
    new_schedule_config = create_schedule_config(
        cpu=old_schedule.config.resources.cpu * 2,
        memory=old_schedule.config.resources.memory * 2,
        disk=old_schedule.config.resources.disk * 2,
    )
    updated_schedule = create_schedule_full_schema(
        update_schedule(
            dbsession,
            schedule_name=old_schedule.name,
            new_schedule_config=new_schedule_config,
            name=old_schedule.name + "_updated",
        )
    )
    assert updated_schedule.config.resources.cpu != old_schedule.config.resources.cpu
    assert (
        updated_schedule.config.resources.memory != old_schedule.config.resources.memory
    )
    assert updated_schedule.config.resources.disk != old_schedule.config.resources.disk
    assert updated_schedule.name == old_schedule.name + "_updated"


def test_delete_schedule(
    dbsession: OrmSession, create_schedule: Callable[..., Schedule]
):
    """Test that delete_schedule deletes a schedule"""
    schedule = create_schedule()
    delete_schedule(dbsession, schedule_name=schedule.name)
    assert get_schedule_or_none(dbsession, schedule_name=schedule.name) is None


def test_delete_schedule_not_found(dbsession: OrmSession):
    """Test that delete_schedule raises an exception if the schedule does not exist"""
    with pytest.raises(RecordDoesNotExistError):
        delete_schedule(dbsession, schedule_name="nonexistent")


@pytest.mark.parametrize(
    "name,lang,categories,tags,expected_count",
    [
        pytest.param(None, None, None, None, 30, id="all"),
        pytest.param("wiki", ["en"], None, None, 10, id="wiki_en"),
        pytest.param("wiki", ["en", "fr"], None, None, 20, id="wiki_en_fr"),
        pytest.param(
            "schedule",
            None,
            [ScheduleCategory.wikipedia],
            None,
            0,
            id="schedule_wikipedia",
        ),
        pytest.param(None, ["en"], None, ["important"], 10, id="en_important"),
        pytest.param("nonexistent", None, None, None, 0, id="nonexistent"),
        pytest.param(
            "schedule",
            ["en"],
            [ScheduleCategory.other],
            ["test"],
            10,
            id="schedule_en_other_test",
        ),
    ],
)
def test_get_schedules(
    dbsession: OrmSession,
    create_schedule: Callable[..., Schedule],
    create_requested_task: Callable[..., RequestedTask],
    create_task: Callable[..., Task],
    name: str | None,
    lang: list[str] | None,
    categories: list[ScheduleCategory] | None,
    tags: list[str] | None,
    expected_count: int,
):
    """Test that get_schedules works correctly with combined filters"""
    for i in range(10):
        schedule = create_schedule(
            name=f"wiki_en_{i}",
            category=ScheduleCategory.wikipedia,
            language=LanguageSchema(
                code="en", name_en="English", name_native="English"
            ),
            tags=["important"],
        )
        requested_task = create_requested_task(schedule_name=schedule.name)
        task = create_task(requested_task=requested_task)
        schedule.most_recent_task = task
        dbsession.add(schedule)
        dbsession.flush()

    for i in range(10):
        schedule = create_schedule(
            name=f"wiki_fr_{i}",
            category=ScheduleCategory.wikipedia,
            language=LanguageSchema(
                code="fr", name_en="French", name_native="Français"
            ),
            tags=["important"],
        )
        requested_task = create_requested_task(schedule_name=schedule.name)
        task = create_task(requested_task=requested_task)
        schedule.most_recent_task = task
        dbsession.add(schedule)
        dbsession.flush()

    for i in range(10):
        schedule = create_schedule(
            name=f"other_schedule_{i}",
            category=ScheduleCategory.other,
            language=LanguageSchema(
                code="en", name_en="English", name_native="English"
            ),
            tags=["test"],
        )
        requested_task = create_requested_task(schedule_name=schedule.name)
        task = create_task(requested_task=requested_task)
        schedule.most_recent_task = task
        dbsession.add(schedule)
        dbsession.flush()

    limit = 5
    results = get_schedules(
        dbsession,
        skip=0,
        limit=limit,
        name=name,
        lang=lang,
        categories=categories,
        tags=tags,
    )
    assert results.nb_records == expected_count
    assert len(results.schedules) <= limit
    for result_schedule in results.schedules:
        assert result_schedule.config is not None
        assert result_schedule.nb_requested_tasks == 1
        assert result_schedule.most_recent_task is not None


def test_update_schedule_duration_no_tasks(
    dbsession: OrmSession, create_schedule: Callable[..., Schedule]
):
    """Test that update_schedule_duration does nothing when no matching tasks exist"""
    schedule = create_schedule(name="test_schedule")

    update_schedule_duration(dbsession, schedule_name=schedule.name)

    assert len(schedule.durations) == 1
    assert schedule.durations[0].default is True


def test_update_schedule_duration_with_completed_tasks(
    dbsession: OrmSession,
    create_schedule: Callable[..., Schedule],
    create_task: Callable[..., Task],
    worker: Worker,
):
    """Test that update_schedule_duration creates worker-specific durations"""
    schedule = create_schedule(name="test_schedule")

    # Create a task that completed successfully
    started_time = datetime.datetime(2023, 1, 1, 10, 0, 0)
    completed_time = datetime.datetime(2023, 1, 1, 12, 0, 0)  # 2 hours later

    task = create_task(
        schedule_name=schedule.name,
        status=TaskStatus.scraper_completed,
        worker=worker,
    )

    # Set up the task with proper timestamps and exit code
    task.timestamp = [
        (TaskStatus.started.value, started_time),
        (TaskStatus.scraper_completed.value, completed_time),
    ]
    task.container = {"exit_code": 0}
    dbsession.add(task)
    dbsession.flush()

    update_schedule_duration(dbsession, schedule_name=schedule.name)

    # Expire the schedule to force a reload of the schedule
    dbsession.expire(schedule)
    updated_schedule = get_schedule(dbsession, schedule_name=schedule.name)

    assert len(updated_schedule.durations) == 2  # Default + worker-specific

    # Find the worker-specific duration
    worker_duration = next(
        (d for d in updated_schedule.durations if d.worker_id == worker.id), None
    )

    assert worker_duration is not None
    assert worker_duration.default is False
    assert worker_duration.on == completed_time


def test_update_schedule_duration_with_failed_tasks(
    dbsession: OrmSession,
    create_schedule: Callable[..., Schedule],
    create_task: Callable[..., Task],
    worker: Worker,
):
    """Test that update_schedule_duration ignores tasks with non-zero exit codes"""
    schedule = create_schedule(name="test_schedule")

    # Create a task that failed (exit_code != 0)
    started_time = datetime.datetime(2023, 1, 1, 10, 0, 0)
    completed_time = datetime.datetime(2023, 1, 1, 12, 0, 0)

    task = create_task(
        schedule_name=schedule.name,
        status=TaskStatus.scraper_completed,
        worker=worker,
    )

    # Set up the task with proper timestamps but failed exit code
    task.timestamp = [
        (TaskStatus.started.value, started_time),
        (TaskStatus.scraper_completed.value, completed_time),
    ]
    task.container = {"exit_code": 1}  # Failed task
    dbsession.add(task)
    dbsession.flush()

    update_schedule_duration(dbsession, schedule_name=schedule.name)

    # Expire the schedule to force a reload of the schedule
    dbsession.expire(schedule)
    updated_schedule = get_schedule(dbsession, schedule_name=schedule.name)

    # Verify no new durations were created (only the default remains)
    assert len(updated_schedule.durations) == 1
    assert updated_schedule.durations[0].default is True


def test_update_schedule_duration_multiple_workers(
    dbsession: OrmSession,
    create_schedule: Callable[..., Schedule],
    create_task: Callable[..., Task],
    create_worker: Callable[..., Worker],
):
    """Test that update_schedule_duration handles multiple workers correctly"""
    schedule = create_schedule(name="test_schedule")
    worker1 = create_worker(name="worker1")
    worker2 = create_worker(name="worker2")

    # Create tasks for both workers
    task1 = create_task(
        schedule_name=schedule.name,
        status=TaskStatus.scraper_completed,
        worker=worker1,
    )
    task1.timestamp = [
        (TaskStatus.started.value, datetime.datetime(2023, 1, 1, 10, 0, 0)),
        (
            TaskStatus.scraper_completed.value,
            datetime.datetime(2023, 1, 1, 11, 0, 0),
        ),  # 1 hour
    ]
    task1.container = {"exit_code": 0}

    task2 = create_task(
        schedule_name=schedule.name,
        status=TaskStatus.scraper_completed,
        worker=worker2,
    )
    task2.timestamp = [
        (TaskStatus.started.value, datetime.datetime(2023, 1, 1, 10, 0, 0)),
        (
            TaskStatus.scraper_completed.value,
            datetime.datetime(2023, 1, 1, 12, 0, 0),
        ),  # 2 hours
    ]
    task2.container = {"exit_code": 0}

    dbsession.add_all([task1, task2])
    dbsession.flush()

    update_schedule_duration(dbsession, schedule_name=schedule.name)

    dbsession.expire(schedule)
    updated_schedule = get_schedule(dbsession, schedule_name=schedule.name)

    assert len(updated_schedule.durations) == 3  # Default + 2 worker-specific

    worker1_duration = next(
        (d for d in updated_schedule.durations if d.worker_id == worker1.id), None
    )
    assert worker1_duration is not None

    worker2_duration = next(
        (d for d in updated_schedule.durations if d.worker_id == worker2.id), None
    )
    assert worker2_duration is not None
