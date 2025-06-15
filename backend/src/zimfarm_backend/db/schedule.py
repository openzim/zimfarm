import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common import constants
from zimfarm_backend.db import count_from_stmt
from zimfarm_backend.db.exceptions import RecordDoesNotExistError
from zimfarm_backend.db.models import Schedule, ScheduleDuration, Worker

DEFAULT_SCHEDULE_DURATION_DICT = {
    "value": int(constants.DEFAULT_SCHEDULE_DURATION),
    "on": datetime.datetime.now(datetime.UTC).replace(tzinfo=None),
    "worker": None,
    "task": None,
}


def count_enabled_schedules(session: OrmSession, schedule_names: list[str]) -> int:
    """Count all enabled schedules that match the given names"""
    return count_from_stmt(
        session,
        (
            select(Schedule).where(
                Schedule.enabled.is_(True), Schedule.name.in_(schedule_names)
            )
        ),
    )


def get_schedule_or_none(session: OrmSession, *, schedule_name: str) -> Schedule | None:
    """Get a schedule for the given schedule name if possible else None"""
    return session.scalars(
        select(Schedule).where(Schedule.name == schedule_name)
    ).one_or_none()


def get_schedule(session: OrmSession, *, schedule_name: str) -> Schedule:
    """Get a schedule for the given schedule name if possible else raise an exception"""
    if (schedule := get_schedule_or_none(session, schedule_name=schedule_name)) is None:
        raise RecordDoesNotExistError(
            f"Schedule with name {schedule_name} does not exist"
        )
    return schedule


def map_duration(duration: ScheduleDuration) -> dict[str, Any]:
    return {
        "value": duration.value,
        "on": duration.on,
        "worker": duration.worker.name if duration.worker else None,
    }


def _get_duration_for_schedule(schedule: Schedule, worker: Worker) -> dict[str, Any]:
    """get duration"""
    for duration in schedule.durations:
        if duration.worker and duration.worker.name == worker.name:
            return map_duration(duration)
    for duration in schedule.durations:
        if duration.default:
            return map_duration(duration)
    raise RecordDoesNotExistError(
        f"No default duration found for schedule {schedule.name}"
    )


def get_schedule_duration(
    session: OrmSession, *, schedule_name: str | None, worker: Worker
) -> dict[str, Any]:
    """get duration for a schedule and worker (or default one)"""
    if schedule_name is None:
        return DEFAULT_SCHEDULE_DURATION_DICT
    schedule = get_schedule_or_none(session, schedule_name=schedule_name)
    if schedule is None:
        return DEFAULT_SCHEDULE_DURATION_DICT
    return _get_duration_for_schedule(schedule, worker)
