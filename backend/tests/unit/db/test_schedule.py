import datetime

import pytest
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.db.exceptions import RecordDoesNotExistError
from zimfarm_backend.db.models import Schedule, ScheduleDuration, Worker
from zimfarm_backend.db.schedule import (
    count_enabled_schedules,
    get_schedule,
    get_schedule_duration,
    get_schedule_or_none,
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
    assert duration["value"] > 0
    assert duration["worker"] is None
    assert isinstance(duration["on"], datetime.datetime)


def test_get_schedule_duration_with_worker(
    dbsession: OrmSession,
    schedule: Schedule,
    worker: Worker,
    schedule_duration: ScheduleDuration,
):
    """Returns worker-specific duration when schedule exists"""
    duration = get_schedule_duration(
        dbsession, schedule_name=schedule.name, worker=worker
    )
    assert duration["value"] == schedule_duration.value
    assert duration["worker"] == worker.name
    assert duration["on"] == schedule_duration.on
