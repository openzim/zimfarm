import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Bundle
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common import getnow
from zimfarm_backend.common.enums import TaskStatus
from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.orms import (
    ConfigResourcesSchema,
    ConfigWithOnlyResourcesSchema,
    ExpandedScheduleConfigSchema,
    RequestedTaskFullSchema,
    TaskFullSchema,
    TaskLightSchema,
)
from zimfarm_backend.db.exceptions import (
    RecordAlreadyExistsError,
    RecordDoesNotExistError,
)
from zimfarm_backend.db.models import Schedule, Task, Worker


class TaskListResult(BaseModel):
    nb_records: int
    tasks: list[TaskLightSchema]


def get_task_by_id_or_none(session: OrmSession, task_id: UUID) -> TaskFullSchema | None:
    """
    Get a task by id or None if it does not exist
    """
    stmt = (
        select(
            Task.id,
            Task.status,
            Task.timestamp,
            Task.config,
            Task.events,
            Task.debug,
            Task.requested_by,
            Task.canceled_by,
            Task.container,
            Task.priority,
            Task.notification,
            Task.files,
            Task.upload,
            Task.updated_at,
            Task.original_schedule_name,
            Schedule.name.label("schedule_name"),
            Worker.name.label("worker_name"),
        )
        .join(Schedule, Task.schedule, isouter=True)
        .join(Worker, Task.worker, isouter=True)
        .where(Task.id == task_id)
    )
    if row := session.execute(stmt).one_or_none():
        return TaskFullSchema(
            id=row.id,
            status=row.status,
            timestamp=row.timestamp,
            config=ExpandedScheduleConfigSchema.model_validate(
                {
                    "warehouse_path": row.config["warehouse_path"],
                    "resources": row.config["resources"],
                    "offliner": row.config["offliner"],
                    "monitor": row.config["monitor"],
                    "image": row.config["image"],
                    "mount_point": row.config["mount_point"],
                    "command": row.config["command"],
                    "str_command": row.config["str_command"],
                },
                context={"skip_validation": True},
            ),
            events=row.events,
            debug=row.debug,
            requested_by=row.requested_by,
            canceled_by=row.canceled_by,
            container=row.container,
            priority=row.priority,
            notification=row.notification or None,
            files=row.files,
            upload=row.upload,
            updated_at=row.updated_at,
            original_schedule_name=row.original_schedule_name,
            schedule_name=row.schedule_name,
            worker_name=row.worker_name,
        )
    return None


def get_task_by_id(session: OrmSession, task_id: UUID) -> TaskFullSchema:
    if task := get_task_by_id_or_none(session, task_id):
        return task
    raise RecordDoesNotExistError(f"Task with id {task_id} does not exist")


def get_tasks(
    session: OrmSession,
    *,
    skip: int,
    limit: int,
    status: list[TaskStatus] | None = None,
    schedule_name: str | None = None,
):
    status = status or list(TaskStatus)
    stmt = (  # pyright: ignore[reportUnknownVariableType]
        select(
            func.count().over().label("nb_records"),
            Task.id,
            Task.status,
            Task.timestamp,
            Task.original_schedule_name,
            Bundle(  # pyright: ignore[reportUnknownArgumentType]
                "config",
                Task.config["resources"].label("resources"),
            ),
            Task.updated_at,
            Schedule.name.label("schedule_name"),
            Worker.name.label("worker_name"),
        )
        .join(Worker, Task.worker, isouter=True)
        .join(Schedule, Task.schedule, isouter=True)
        .where(
            (Schedule.name == schedule_name) | (schedule_name is None),
            (Task.status.in_(status)),
        )
        .order_by(Task.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )

    results = TaskListResult(nb_records=0, tasks=[])
    for (
        nb_records,
        _id,
        _status,
        timestamp,
        original_schedule_name,
        config,
        updated_at,
        _schedule_name,
        worker_name,
    ) in session.execute(
        stmt  # pyright: ignore[reportUnknownArgumentType]
    ).all():
        results.nb_records = nb_records
        results.tasks.append(
            TaskLightSchema(
                id=_id,
                status=_status,
                timestamp=timestamp,
                original_schedule_name=original_schedule_name,
                config=ConfigWithOnlyResourcesSchema(
                    resources=ConfigResourcesSchema(
                        cpu=config.resources["cpu"],
                        disk=config.resources["disk"],
                        memory=config.resources["memory"],
                    ),
                ),
                updated_at=updated_at,
                schedule_name=_schedule_name,
                worker_name=worker_name,
            )
        )
    return results


def create_task(
    session: OrmSession, *, requested_task: RequestedTaskFullSchema, worker_id: UUID
) -> TaskFullSchema:
    """
    Create a task from a requested task
    """
    task = Task(
        updated_at=requested_task.updated_at,
        events=requested_task.events,
        debug={},
        status=requested_task.status,
        timestamp=requested_task.timestamp,
        requested_by=requested_task.requested_by,
        canceled_by=None,
        container={},
        priority=requested_task.priority,
        config=requested_task.config.model_dump(
            mode="json", context={"show_secrets": True}
        ),
        notification=(
            requested_task.notification.model_dump(mode="json")
            if requested_task.notification
            else {}
        ),
        files={},
        upload=requested_task.upload,
        original_schedule_name=requested_task.original_schedule_name,
    )
    task.id = requested_task.id
    task.schedule_id = requested_task.schedule_id
    task.worker_id = worker_id
    session.add(task)
    try:
        session.flush()
    except IntegrityError as exc:
        raise RecordAlreadyExistsError(
            f"Task with id {requested_task.id} already exists"
        ) from exc
    return get_task_by_id(session, requested_task.id)


def get_oldest_task_timestamp(
    session: OrmSession, status: TaskStatus
) -> datetime.datetime:
    """
    Get the oldest task timestamp for a given status or now if no tasks with this status
    """
    rows: list[list[tuple[str, datetime.datetime]]] = list(
        session.scalars(
            select(
                Task.timestamp,
            ).where(Task.status == status)
        ).all()
    )
    return min([getnow(), *[timestamp for row in rows for _, timestamp in row]])
