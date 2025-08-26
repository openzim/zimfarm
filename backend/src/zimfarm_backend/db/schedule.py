from typing import Any
from uuid import UUID

from sqlalchemy import Integer, func, select
from sqlalchemy import cast as sql_cast
from sqlalchemy.dialects.postgresql import JSONPATH, insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common import constants, getnow
from zimfarm_backend.common.enums import (
    ScheduleCategory,
    SchedulePeriodicity,
    TaskStatus,
)
from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.models import (
    ScheduleConfigSchema,
    ScheduleNotificationSchema,
)
from zimfarm_backend.common.schemas.orms import (
    ConfigOfflinerOnlySchema,
    LanguageSchema,
    MostRecentTaskSchema,
    ScheduleDurationSchema,
    ScheduleFullSchema,
    ScheduleLightSchema,
)
from zimfarm_backend.db import count_from_stmt
from zimfarm_backend.db.exceptions import (
    RecordAlreadyExistsError,
    RecordDoesNotExistError,
)
from zimfarm_backend.db.language import get_language_from_code
from zimfarm_backend.db.models import (
    RequestedTask,
    Schedule,
    ScheduleDuration,
    Task,
    Worker,
)
from zimfarm_backend.utils.timestamp import (
    get_status_timestamp_expr,
    get_timestamp_for_status,
)

DEFAULT_SCHEDULE_DURATION = ScheduleDurationSchema(
    value=int(constants.DEFAULT_SCHEDULE_DURATION),
    on=getnow(),
    worker_name=None,
    default=True,
)


class ScheduleListResult(BaseModel):
    nb_records: int
    schedules: list[ScheduleLightSchema | ScheduleFullSchema]


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


def map_duration(duration: ScheduleDuration) -> ScheduleDurationSchema:
    return ScheduleDurationSchema(
        value=duration.value,
        on=duration.on,
        worker_name=duration.worker.name if duration.worker else None,
        default=duration.default,
    )


def _get_duration_for_schedule(
    schedule: Schedule, worker: Worker
) -> ScheduleDurationSchema:
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
) -> ScheduleDurationSchema:
    """get duration for a schedule and worker (or default one)"""
    if schedule_name is None:
        return DEFAULT_SCHEDULE_DURATION
    schedule = get_schedule_or_none(session, schedule_name=schedule_name)
    if schedule is None:
        return DEFAULT_SCHEDULE_DURATION
    return _get_duration_for_schedule(schedule, worker)


def update_schedule_duration(
    session: OrmSession,
    *,
    schedule_name: str,
):
    """Update the duration for a schedule and worker"""
    schedule = get_schedule(session, schedule_name=schedule_name)
    # retrieve tasks that completed the resources intensive part
    # we don't mind to retrieve all of them because they are regularly purged
    tasks = session.execute(
        select(Task)
        .where(
            # Task timestamp has changed from dict[str, Any] to
            # list[tuple[str, Any]. As such we use jsonb_path query functions
            # to search for timestamp objects.
            func.jsonb_path_exists(
                Task.timestamp,
                sql_cast(f'$[*] ? (@[0] == "{TaskStatus.started}")', JSONPATH),
            ),
            func.jsonb_path_exists(
                Task.timestamp,
                sql_cast(
                    f'$[*] ? (@[0] == "{TaskStatus.scraper_completed}")', JSONPATH
                ),
            ),
            Task.container["exit_code"].astext.cast(Integer) == 0,
            Task.schedule_id == schedule.id,
        )
        .order_by(
            get_status_timestamp_expr(Task.timestamp, TaskStatus.scraper_completed),
        )
    ).scalars()

    workers_durations: dict[UUID, dict[str, Any]] = {}
    for task in tasks:
        workers_durations[task.worker_id] = {
            "value": int(
                (
                    get_timestamp_for_status(
                        task.timestamp, TaskStatus.scraper_completed
                    )
                    - get_timestamp_for_status(task.timestamp, TaskStatus.started)
                ).total_seconds()
            ),
            "on": get_timestamp_for_status(
                task.timestamp, TaskStatus.scraper_completed
            ),
        }

    # compute values that will be inserted (or updated) in the DB
    inserts_durations = [
        {
            "default": False,
            "value": duration_payload["value"],
            "on": duration_payload["on"],
            "schedule_id": schedule.id,
            "worker_id": worker_id,
        }
        for worker_id, duration_payload in workers_durations.items()
    ]

    # if there is no matching task for this schedule, just exit
    if len(inserts_durations) == 0:
        return

    # let's do an upsert ; conflict on schedule_id + worker_id
    # on conflict, set the on, value, task_id
    upsert_stmt = insert(ScheduleDuration).values(inserts_durations)
    upsert_stmt = upsert_stmt.on_conflict_do_update(
        index_elements=[
            ScheduleDuration.schedule_id,
            ScheduleDuration.worker_id,
        ],
        set_={
            ScheduleDuration.on: upsert_stmt.excluded.on,
            ScheduleDuration.value: upsert_stmt.excluded.value,
        },
    )
    session.execute(upsert_stmt)


def get_schedules(
    session: OrmSession,
    *,
    skip: int,
    limit: int,
    name: str | None = None,
    lang: list[str] | None = None,
    categories: list[ScheduleCategory] | None = None,
    tags: list[str] | None = None,
) -> ScheduleListResult:
    """Get a list of schedules"""
    subquery = (
        select(
            func.count(RequestedTask.id).label("nb_requested_tasks"),
            RequestedTask.schedule_id,
        )
        .group_by(RequestedTask.schedule_id)
        .subquery("requested_task_count")
    )

    stmt = (
        select(
            func.count().over().label("total_records"),
            Schedule.name.label("schedule_name"),
            Schedule.category,
            Schedule.enabled,
            Schedule.language_code,
            Schedule.config,
            Task.id.label("task_id"),
            Task.status.label("task_status"),
            Task.updated_at.label("task_updated_at"),
            func.coalesce(subquery.c.nb_requested_tasks, 0).label("nb_requested_tasks"),
        )
        .join(Task, Schedule.most_recent_task, isouter=True)
        .join(subquery, subquery.c.schedule_id == Schedule.id, isouter=True)
        .order_by(Schedule.name)
        .where(
            # If a client provides an argument i.e it is not None,
            # we compare the corresponding model field against the argument,
            # otherwise, we compare the argument to its default which translates
            # to a SQL true i.e we don't filter based on this argument.
            (Schedule.category.in_(categories or []) | (categories is None)),
            (Schedule.language_code.in_(lang or []) | (lang is None)),
            (Schedule.tags.contains(tags or []) | (tags is None)),
            (Schedule.name.ilike(f"%{name}%") | (name is None)),
        )
        .offset(skip)
        .limit(limit)
    )

    results = ScheduleListResult(nb_records=0, schedules=[])

    for (
        nb_records,
        schedule_name,
        category,
        enabled,
        language_code,
        config,
        task_id,
        task_status,
        task_updated_at,
        nb_requested_tasks,
    ) in session.execute(stmt).all():
        # Because the SQL window function returns the total_records
        # for every row, assign that value to the nb_records
        try:
            language = get_language_from_code(language_code)
        except RecordDoesNotExistError:
            language = LanguageSchema.model_validate(
                {"code": language_code, "name": language_code},
                context={"skip_validation": True},
            )

        results.nb_records = nb_records
        results.schedules.append(
            ScheduleLightSchema(
                name=schedule_name,
                category=category,
                enabled=enabled,
                language=language,
                config=ConfigOfflinerOnlySchema(
                    offliner=config["offliner"]["offliner_id"],
                ),
                most_recent_task=(
                    MostRecentTaskSchema(
                        id=task_id,
                        status=task_status,
                        updated_at=task_updated_at,
                    )
                    if all([task_id, task_status, task_updated_at])
                    else None
                ),
                nb_requested_tasks=nb_requested_tasks,
            )
        )

    return results


def create_schedule(
    session: OrmSession,
    *,
    name: str,
    category: ScheduleCategory,
    language: LanguageSchema,
    config: ScheduleConfigSchema,
    tags: list[str],
    enabled: bool,
    notification: ScheduleNotificationSchema | None,
    periodicity: SchedulePeriodicity,
) -> Schedule:
    """Create a new schedule"""
    schedule = Schedule(
        name=name,
        category=category,
        language_code=language.code,
        config=config.model_dump(mode="json", context={"show_secrets": True}),
        tags=tags,
        enabled=enabled,
        notification=notification.model_dump(mode="json") if notification else None,
        periodicity=periodicity,
    )
    schedule_duration = ScheduleDuration(
        value=DEFAULT_SCHEDULE_DURATION.value,
        on=DEFAULT_SCHEDULE_DURATION.on,
        default=True,
    )
    schedule.durations.append(schedule_duration)
    session.add(schedule)
    try:
        session.flush()
    except IntegrityError as exc:
        raise RecordAlreadyExistsError(
            f"Schedule with name {name} already exists"
        ) from exc
    return schedule


def create_schedule_full_schema(schedule: Schedule) -> ScheduleFullSchema:
    """Create a full schedule schema"""
    # Given this function is almost always called while serializing an already
    # loaded schedule, we want to relax constraints while validating the schema
    try:
        language = get_language_from_code(schedule.language_code)
    except RecordDoesNotExistError:
        language = LanguageSchema.model_validate(
            {"code": schedule.language_code, "name": schedule.language_code},
            context={"skip_validation": True},
        )
    return ScheduleFullSchema(
        language=language,
        durations=[
            ScheduleDurationSchema(
                value=duration.value,
                on=duration.on,
                worker_name=duration.worker.name if duration.worker else None,
                default=duration.default,
            )
            for duration in schedule.durations
        ],
        name=schedule.name,
        category=schedule.category,
        config=ScheduleConfigSchema.model_validate(
            schedule.config, context={"skip_validation": True}
        ),
        enabled=schedule.enabled,
        tags=schedule.tags,
        periodicity=schedule.periodicity,
        notification=(
            ScheduleNotificationSchema.model_validate(schedule.notification)
            if schedule.notification
            else None
        ),
        most_recent_task=(
            MostRecentTaskSchema(
                id=schedule.most_recent_task.id,
                status=schedule.most_recent_task.status,
                updated_at=schedule.most_recent_task.updated_at,
            )
            if schedule.most_recent_task
            else None
        ),
        nb_requested_tasks=len(schedule.requested_tasks),
    )


def get_all_schedules(session: OrmSession) -> ScheduleListResult:
    """Get all schedules"""
    return ScheduleListResult(
        nb_records=len(session.scalars(select(Schedule).order_by(Schedule.name)).all()),
        schedules=[
            create_schedule_full_schema(schedule)
            for schedule in session.scalars(
                select(Schedule).order_by(Schedule.name)
            ).all()
        ],
    )


def update_schedule(
    session: OrmSession,
    *,
    schedule_name: str,
    new_schedule_config: ScheduleConfigSchema,
    language: LanguageSchema | None = None,
    name: str | None = None,
    category: ScheduleCategory | None = None,
    tags: list[str] | None = None,
    enabled: bool | None = None,
    periodicity: SchedulePeriodicity | None = None,
) -> Schedule:
    """Update a schedule"""
    schedule = get_schedule(session, schedule_name=schedule_name)
    if language:
        schedule.language_code = language.code
    schedule.name = name if name is not None else schedule.name
    schedule.category = category if category is not None else schedule.category
    schedule.tags = tags if tags is not None else schedule.tags
    schedule.enabled = enabled if enabled is not None else schedule.enabled
    schedule.periodicity = (
        periodicity if periodicity is not None else schedule.periodicity
    )
    schedule.config = new_schedule_config.model_dump(
        mode="json", context={"show_secrets": True}
    )
    session.add(schedule)
    try:
        session.flush()
    except IntegrityError as exc:
        raise RecordAlreadyExistsError(
            f"Schedule with name {name} already exists"
        ) from exc
    return schedule


def delete_schedule(session: OrmSession, *, schedule_name: str) -> None:
    """Delete a schedule"""
    schedule = get_schedule(session, schedule_name=schedule_name)
    # first unset most recent task to avoid circular dependency
    schedule.most_recent_task = None
    session.delete(schedule)
    session.flush()
