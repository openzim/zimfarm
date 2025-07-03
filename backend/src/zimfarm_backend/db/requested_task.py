import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import BigInteger, delete, func, or_, select, update
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend import logger
from zimfarm_backend.common import getnow
from zimfarm_backend.common.constants import (
    ARTIFACTS_EXPIRATION,
    ARTIFACTS_UPLOAD_URI,
    LOGS_EXPIRATION,
    LOGS_UPLOAD_URI,
    ZIM_EXPIRATION,
    ZIM_UPLOAD_URI,
    ZIMCHECK_OPTION,
)
from zimfarm_backend.common.enums import Offliner, Platform, TaskStatus
from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.models import (
    ExpandedScheduleConfigSchema,
    ScheduleConfigSchema,
    ScheduleNotificationSchema,
)
from zimfarm_backend.common.schemas.orms import (
    ConfigResourcesSchema,
    ConfigWithOnlyOfflinerAndResourcesSchema,
    RequestedTaskFullSchema,
    RequestedTaskLightSchema,
    ScheduleDurationSchema,
)
from zimfarm_backend.db import count_from_stmt
from zimfarm_backend.db.exceptions import RecordDoesNotExistError
from zimfarm_backend.db.models import RequestedTask, Schedule, Task, User, Worker
from zimfarm_backend.db.schedule import get_schedule_duration, get_schedule_or_none
from zimfarm_backend.db.worker import get_worker_or_none
from zimfarm_backend.utils.offliners import expanded_config

# Maximum positive integer value for PostgreSQL BigInteger
MAX_BIG_INT_VAL = 2**63 - 1


class RequestedTaskListResult(BaseModel):
    nb_records: int
    requested_tasks: list[RequestedTaskLightSchema]


def request_task(
    session: OrmSession,
    *,
    schedule_name: str,
    requested_by: str,
    worker_name: str | None = None,
    priority: int = 0,
) -> RequestedTaskFullSchema | None:
    """Request a task for the given schedule name if possible else None

    Schedule can't be requested if already requested on same worker.
    Schedule can't be requested if it's disabled.
    """

    query = (
        select(
            RequestedTask,
            Schedule,
        )
        .join(Schedule, RequestedTask.schedule)
        .where(
            Schedule.name == schedule_name,
        )
    )
    if worker_name is not None:
        query = query.join(Worker, RequestedTask.worker).where(
            Worker.name == worker_name
        )

    # If the worker has a requested task for this schedule, return None
    if count_from_stmt(session, query) > 0:
        return None

    schedule = get_schedule_or_none(session, schedule_name=schedule_name)

    if schedule is None or not schedule.enabled:
        return None

    worker = None
    if worker_name is not None:
        worker = get_worker_or_none(session, worker_name=worker_name)
        if worker is None:
            return None

    # Otherwise, create a new requested task
    now = getnow()
    requested_task = RequestedTask(
        status=TaskStatus.requested,
        timestamp={TaskStatus.requested.value: now},
        events=[{"code": TaskStatus.requested, "timestamp": now}],
        requested_by=requested_by,
        priority=priority,
        config=expanded_config(
            ScheduleConfigSchema.model_validate(schedule.config)
        ).model_dump(mode="json", by_alias=True, context={"show_secrets": True}),
        upload={
            "zim": {
                "upload_uri": ZIM_UPLOAD_URI,
                "expiration": ZIM_EXPIRATION,
                "zimcheck": ZIMCHECK_OPTION,
            },
            "logs": {
                "upload_uri": LOGS_UPLOAD_URI,
                "expiration": LOGS_EXPIRATION,
            },
            "artifacts": {
                "upload_uri": ARTIFACTS_UPLOAD_URI,
                "expiration": ARTIFACTS_EXPIRATION,
            },
        },
        notification=schedule.notification if schedule.notification else {},
        updated_at=now,
        original_schedule_name=schedule.name,
    )
    requested_task.schedule = schedule
    if worker:
        requested_task.worker = worker

    session.add(requested_task)
    session.flush()

    return _create_requested_task_full_schema(session, requested_task)


def get_requested_tasks(
    session: OrmSession,
    *,
    worker_name: str | None = None,
    skip: int,
    limit: int,
    matching_offliners: list[str] | None = None,
    schedule_name: list[str] | None = None,
    priority: int | None = None,
    cpu: int | None = None,
    memory: int | None = None,
    disk: int | None = None,
) -> RequestedTaskListResult:
    """Get a paginated list of requested tasks filtered by various criteria.

    Tasks are sorted by priority (descending), reserved timestamp, and
    requested timestamp.

    Args:
        session: SQLAlchemy database session
        worker_name: Optional worker name to filter tasks by. If None, tasks for all
            workers are returned.
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return (for pagination)
        matching_offliners: Optional list of offliner IDs to filter tasks by. If None,
            tasks for all offliners are returned.
        schedule_name: Optional list of schedule names to filter tasks by. If None,
            tasks for all schedules are returned.
        priority: Optional minimum priority to filter tasks by. If None, no priority
            filter is applied.
        cpu: Optional maximum CPU requirement to filter tasks by. If None, no CPU filter
            is applied.
        memory: Optional maximum memory requirement to filter tasks by. If None, no
            memory filter is applied.
        disk: Optional maximum disk requirement to filter tasks by. If None, no disk
            filter is applied.

    Returns:
        RequestedTaskListResult containing:
            - nb_records: Total number of records matching the filters (no pagination)
            - requested_tasks: List of RequestedTaskLightSchema objects matching the
                filters and pagination
    """
    # Set reasonable defaults if a client omits a param
    offliners = (
        matching_offliners
        if matching_offliners
        else [offliner.value for offliner in Offliner]
    )
    priority = priority or 0
    cpu = cpu if cpu is not None else MAX_BIG_INT_VAL
    memory = memory if memory is not None else MAX_BIG_INT_VAL
    disk = disk if disk is not None else MAX_BIG_INT_VAL

    query = (
        select(
            func.count().over().label("nb_records"),
            RequestedTask.id,
            RequestedTask.status,
            RequestedTask.config,
            RequestedTask.timestamp,
            RequestedTask.requested_by,
            RequestedTask.priority,
            RequestedTask.original_schedule_name,
            RequestedTask.updated_at,
            Schedule.name.label("schedule_name"),
            Worker.name.label("worker_name"),
        )
        .join(Worker, RequestedTask.worker, isouter=True)
        .join(Schedule, RequestedTask.schedule, isouter=True)
        .where(
            # If a client provides an argument i.e it is not None, we compare the
            # corresponding model field against the argument, otherwise, we compare the
            # argument to its default in param which translates to a SQL true i.e
            # we don't filter based on this argument.
            (Schedule.name.in_(schedule_name or [])) | (schedule_name is None),
            (RequestedTask.priority >= priority),
            (RequestedTask.config["resources"]["cpu"].astext.cast(BigInteger) <= cpu),
            (
                RequestedTask.config["resources"]["memory"].astext.cast(BigInteger)
                <= memory
            ),
            (RequestedTask.config["resources"]["disk"].astext.cast(BigInteger) <= disk),
            (RequestedTask.config["offliner"]["offliner_id"].astext.in_(offliners)),
            (Worker.name == worker_name)
            | (
                RequestedTask.worker is None
            )  # pyright: ignore[reportUnnecessaryComparison]
            | (worker_name is None),
        )
        .order_by(
            RequestedTask.priority.desc(),
            RequestedTask.timestamp["reserved"]["$date"].astext.cast(BigInteger),
            RequestedTask.timestamp["requested"]["$date"].astext.cast(BigInteger),
        )
    )

    query = query.offset(skip).limit(limit)

    results = RequestedTaskListResult(nb_records=0, requested_tasks=[])

    for (
        nb_records,
        requested_task_id,
        status,
        config,
        timestamp,
        requested_by,
        _priority,
        original_schedule_name,
        updated_at,
        _schedule_name,
        _worker_name,
    ) in session.execute(query).all():
        # Because the SQL window function returns the total_records
        # for every row, assign that value to the nb_records
        results.nb_records = nb_records
        results.requested_tasks.append(
            RequestedTaskLightSchema(
                id=requested_task_id,
                status=status,
                config=ConfigWithOnlyOfflinerAndResourcesSchema(
                    offliner=config["offliner"]["offliner_id"],
                    resources=ConfigResourcesSchema(
                        cpu=config["resources"]["cpu"],
                        memory=config["resources"]["memory"],
                        disk=config["resources"]["disk"],
                    ),
                ),
                timestamp=timestamp,
                requested_by=requested_by,
                priority=_priority,
                original_schedule_name=original_schedule_name,
                updated_at=updated_at,
                worker_name=_worker_name,
                schedule_name=_schedule_name,
            )
        )

    return results


def compute_task_eta(session: OrmSession, task: Task) -> dict[str, Any]:
    """compute task duration (dict), remaining (seconds) and eta (datetime)"""
    now = getnow()
    duration = get_schedule_duration(
        session,
        schedule_name=task.schedule.name if task.schedule else None,
        worker=task.worker,
    )
    elapsed = now - task.timestamp.get("started", task.timestamp["reserved"])
    remaining = max([duration.value - elapsed.total_seconds(), 60])  # seconds
    remaining *= 1.005  # .5% margin
    eta = now + datetime.timedelta(seconds=remaining)
    return {
        "duration": duration,
        "remaining": remaining,
        "eta": eta,
    }


class RunningTask(BaseModel):
    config: ExpandedScheduleConfigSchema
    schedule_name: str
    timestamp: dict[str, Any]
    worker_name: str
    duration: ScheduleDurationSchema
    remaining: float
    eta: datetime.datetime


def get_currently_running_tasks(
    session: OrmSession,
    worker: Worker,
) -> list[RunningTask]:
    """list of tasks being run by worker at this moment, including ETA"""

    stmt = (
        select(Task)
        .join(Worker)
        .where(Task.status.notin_(TaskStatus.complete()), Worker.name == worker.name)
    )
    return [
        RunningTask(
            config=ExpandedScheduleConfigSchema.model_validate(task.config),
            schedule_name=task.schedule.name if task.schedule else "none",
            timestamp=task.timestamp,
            worker_name=task.worker.name,
            **compute_task_eta(session, task),
        )
        for task in session.scalars(stmt).all()
    ]


class RequestedTaskWithDuration(BaseModel):
    id: UUID
    status: str
    config: ExpandedScheduleConfigSchema
    timestamp: dict[str, Any]
    requested_by: str
    priority: int
    schedule_name: str
    original_schedule_name: str
    worker_name: str
    duration: ScheduleDurationSchema
    updated_at: datetime.datetime


def get_tasks_doable_by_worker(
    session: OrmSession, worker: Worker
) -> list[RequestedTaskWithDuration]:
    """list of tasks that a worker can do with its total resources.

    The tasks are sorted by:
    - priority
    - duration (longest first)
    - requested_at (oldest first)
    """
    query = select(RequestedTask).where(
        RequestedTask.config["resources"]["cpu"].astext.cast(BigInteger) <= worker.cpu,
        RequestedTask.config["resources"]["memory"].astext.cast(BigInteger)
        <= worker.memory,
        RequestedTask.config["resources"]["disk"].astext.cast(BigInteger)
        <= worker.disk,
        RequestedTask.config["offliner"]["offliner_id"].astext.in_(worker.offliners),
    )
    if worker.selfish:
        query = query.where(RequestedTask.worker_id == worker.id)
    else:
        query = query.where(
            or_(
                RequestedTask.worker_id == worker.id,
                RequestedTask.worker_id.is_(None),
            )
        )
    return sorted(
        [
            RequestedTaskWithDuration(
                id=task.id,
                status=task.status,
                schedule_name=task.schedule.name if task.schedule else "none",
                original_schedule_name=task.original_schedule_name,
                config=ExpandedScheduleConfigSchema.model_validate(task.config),
                timestamp=task.timestamp,
                requested_by=task.requested_by,
                priority=task.priority,
                worker_name=task.worker.name if task.worker else worker.name,
                duration=get_schedule_duration(
                    session,
                    schedule_name=task.schedule.name if task.schedule else None,
                    worker=worker,
                ),
                updated_at=task.updated_at,
            )
            for task in session.scalars(query).all()
        ],
        key=lambda x: (-x.priority, -x.duration.value, x.updated_at),
    )


def does_platform_allow_worker_to_run(
    *,
    worker: Worker,
    all_running_tasks: list[RunningTask],
    running_tasks: list[RunningTask],
    task: RequestedTaskWithDuration,
) -> bool:
    """check if a worker can run a task based on its platform limitations"""
    platform = task.config.offliner.offliner_id
    if not platform:
        return True

    # check whether we have an overall per-platform limit
    platform_overall_limit = Platform.get_max_overall_tasks_for(platform)
    if platform_overall_limit is not None:
        nb_platform_running = sum(
            [
                1
                for running_task in all_running_tasks
                if running_task.config.offliner.offliner_id == platform
            ]
        )
        if nb_platform_running >= platform_overall_limit:
            return False

    # check whether we have a per-worker limit for this platform
    worker_limit = worker.platforms.get(
        platform, Platform.get_max_per_worker_tasks_for(platform)
    )
    if worker_limit is None:
        return True

    nb_worker_running = sum(
        [
            1
            for running_task in running_tasks
            if running_task.config.offliner.offliner_id == platform
        ]
    )
    return nb_worker_running < worker_limit


def get_possible_task_with_resources(
    *,
    tasks_worker_could_do: list[RequestedTaskWithDuration],
    available_resources: dict[str, int],
    available_time: float,
) -> RequestedTaskWithDuration | None:
    """first of possible tasks runnable with availresources within avail_time"""
    for temp_candidate in tasks_worker_could_do:
        if _can_run(temp_candidate, available_resources):
            if temp_candidate.duration.value <= available_time:
                logger.debug(
                    f"{temp_candidate.id}@{temp_candidate.schedule_name} it is!"
                )
                return temp_candidate
            logger.debug(
                f"{temp_candidate.id}"
                f"@{temp_candidate.schedule_name} would take too long"
            )
    return None


def _can_run(task: RequestedTaskWithDuration, resources: dict[str, int]) -> bool:
    """whether resources are suffiscient to run this task"""
    for key in ["cpu", "memory", "disk"]:
        if getattr(task.config.resources, key) > resources[key]:
            return False
    return True


def find_requested_task_for_worker(
    session: OrmSession,
    *,
    username: str,
    worker_name: str,
    avail_cpu: int,
    avail_memory: int,
    avail_disk: int,
) -> RequestedTaskWithDuration | None:
    """Find optimal task to run for a given worker with given resources.

    The optimal task is the one that will finish the soonest.
    - If there are multiple tasks that finish at the same time, the one with the highest
    priority is chosen.
    - If there are multiple tasks with the same priority, the one with the lowest id
    is chosen.
    """

    worker = session.scalars(
        select(Worker)
        .join(User)
        .where(Worker.name == worker_name, User.username == username)
    ).one_or_none()

    if worker is None:
        raise RecordDoesNotExistError(f"Worker {worker_name} not found")

    # retrieve list of all running tasks with associated resources
    all_running_tasks = get_currently_running_tasks(session, worker)

    # retrieve list of tasks we are currently running with associated resources
    running_tasks = [
        task for task in all_running_tasks if task.worker_name == worker_name
    ]

    # filter-out requested tasks that are not doable now due to platform limitations

    tasks_worker_could_do = (
        task
        for task in get_tasks_doable_by_worker(session=session, worker=worker)
        if does_platform_allow_worker_to_run(
            worker=worker,
            all_running_tasks=all_running_tasks,
            running_tasks=running_tasks,
            task=task,
        )
    )

    available_resources = {
        "cpu": avail_cpu,
        "memory": avail_memory,
        "disk": avail_disk,
    }

    candidate = next(tasks_worker_could_do, None)
    if candidate is None:
        return None

    if _can_run(candidate, available_resources):
        logger.debug("first candidate can be run!")
        return candidate

    missing_cpu = max([candidate.config.resources.cpu - avail_cpu, 0])
    missing_memory = max([candidate.config.resources.memory - avail_memory, 0])
    missing_disk = max([candidate.config.resources.disk - avail_disk, 0])
    logger.debug(f"missing cpu:{missing_cpu}, mem:{missing_memory}, dsk:{missing_disk}")

    # pile-up all of those which we need to complete to have enough resources
    preventing_tasks: list[RunningTask] = []
    for task in sorted(running_tasks, key=lambda x: x.eta):
        preventing_tasks.append(task)
        if (
            sum([t.config.resources.cpu for t in preventing_tasks]) >= missing_cpu
            and sum([t.config.resources.memory for t in preventing_tasks])
            >= missing_memory
            and sum([t.config.resources.disk for t in preventing_tasks]) >= missing_disk
        ):
            # stop when we'd have reclaimed our missing resources
            break

    if not preventing_tasks:
        # we should not get there: no preventing task yet we don't have our total
        logger.error("we have no preventing tasks. oops")
        return None

    logger.debug(f"we have {len(preventing_tasks)} tasks blocking out way")
    opening_eta = preventing_tasks[-1].eta
    logger.debug(f"opening_eta:{opening_eta}")

    # get the number of available seconds from now to that ETA
    available_time = (
        opening_eta - datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
    ).total_seconds()
    logger.debug(f"we have approx. {available_time / 60}mn to reclaim resources")

    # loop on task[1+] to find the first task which can fit
    temp_candidate = get_possible_task_with_resources(
        tasks_worker_could_do=list(tasks_worker_could_do),
        available_resources=available_resources,
        available_time=available_time,
    )
    if temp_candidate:
        return temp_candidate

    # if none in the loop are possible, return None (worker will wait)
    logger.debug("unable to fit anything, you'll have to wait for task to complete")
    return None


def _create_requested_task_full_schema(
    session: OrmSession, requested_task: RequestedTask
) -> RequestedTaskFullSchema:
    return RequestedTaskFullSchema(
        id=requested_task.id,
        status=requested_task.status,
        config=ExpandedScheduleConfigSchema.model_validate(requested_task.config),
        timestamp=requested_task.timestamp,
        requested_by=requested_task.requested_by,
        priority=requested_task.priority,
        schedule_name=(
            requested_task.schedule.name if requested_task.schedule else "none"
        ),
        original_schedule_name=requested_task.original_schedule_name,
        worker_name=requested_task.worker.name if requested_task.worker else None,
        events=requested_task.events,
        upload=requested_task.upload,
        notification=(
            ScheduleNotificationSchema.model_validate(requested_task.notification)
            if requested_task.notification
            else None
        ),
        rank=compute_requested_task_rank(session, requested_task.id),
        updated_at=requested_task.updated_at,
        schedule_id=requested_task.schedule_id,
    )


def get_requested_task_by_id_or_none(
    session: OrmSession, requested_task_id: UUID
) -> RequestedTaskFullSchema | None:
    requested_task = session.scalars(
        select(RequestedTask).where(RequestedTask.id == requested_task_id)
    ).one_or_none()
    if requested_task is None:
        return None
    return _create_requested_task_full_schema(session, requested_task)


def get_requested_task_by_id(
    session: OrmSession, requested_task_id: UUID
) -> RequestedTaskFullSchema:
    requested_task = get_requested_task_by_id_or_none(session, requested_task_id)
    if requested_task is None:
        raise RecordDoesNotExistError(f"Requested task {requested_task_id} not found")
    return requested_task


def compute_requested_task_rank(session: OrmSession, requested_task_id: UUID) -> int:
    """Compute the rank of a requested task based on its priority and updated_at."""
    stmt = select(RequestedTask.id).order_by(
        RequestedTask.priority.desc(), RequestedTask.updated_at.asc()
    )
    return session.scalars(stmt).all().index(requested_task_id)


def update_requested_task_priority(
    session: OrmSession, requested_task_id: UUID, priority: int
) -> RequestedTaskFullSchema:
    """Update the priority of a requested task."""
    requested_task = session.scalars(
        update(RequestedTask)
        .where(RequestedTask.id == requested_task_id)
        .values(priority=priority)
        .returning(RequestedTask)
    ).one()
    return _create_requested_task_full_schema(session, requested_task)


def delete_requested_task(session: OrmSession, requested_task_id: UUID) -> None:
    """Delete a requested task by ID."""
    session.execute(delete(RequestedTask).where(RequestedTask.id == requested_task_id))
