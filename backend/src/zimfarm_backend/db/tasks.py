import datetime
from typing import Any, cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Bundle, selectinload
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common import getnow
from zimfarm_backend.common.constants import parse_bool
from zimfarm_backend.common.enums import TaskStatus
from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.models import FileCreateUpdateSchema
from zimfarm_backend.common.schemas.offliners.models import OfflinerSpecSchema
from zimfarm_backend.common.schemas.orms import (
    ConfigResourcesSchema,
    ConfigWithOnlyResourcesSchema,
    ExpandedScheduleConfigSchema,
    OfflinerDefinitionSchema,
    RequestedTaskFullSchema,
    RunningTask,
    ScheduleNotificationSchema,
    TaskContainerSchema,
    TaskFileSchema,
    TaskFullSchema,
    TaskLightSchema,
    TaskUploadSchema,
)
from zimfarm_backend.db.exceptions import (
    RecordAlreadyExistsError,
    RecordDoesNotExistError,
)
from zimfarm_backend.db.models import (
    File,
    OfflinerDefinition,
    Schedule,
    Task,
    User,
    Worker,
)
from zimfarm_backend.db.offliner import get_offliner
from zimfarm_backend.db.offliner_definition import create_offliner_instance
from zimfarm_backend.db.schedule import get_schedule_duration
from zimfarm_backend.db.user import get_user_by_username
from zimfarm_backend.utils.timestamp import (
    get_status_timestamp_expr,
    get_timestamp_for_status,
)


class TaskListResult(BaseModel):
    nb_records: int
    tasks: list[TaskLightSchema]


def create_task_file_schema(file: File) -> TaskFileSchema:
    return TaskFileSchema(
        name=file.name,
        task_id=file.task_id,
        size=file.size,
        status=file.status,
        created_timestamp=file.created_timestamp,
        uploaded_timestamp=file.uploaded_timestamp,
        failed_timestamp=file.failed_timestamp,
        check_timestamp=file.check_timestamp,
        check_result=file.check_result,
        check_filename=file.check_filename,
        check_upload_timestamp=file.check_upload_timestamp,
        info=file.info,
        cms_on=file.cms_on,
        cms_notified=file.cms_notified,
    )


def get_task_by_id_or_none(session: OrmSession, task_id: UUID) -> TaskFullSchema | None:
    """
    Get a task by id or None if it does not exist
    """
    stmt = (
        select(
            Task,
            OfflinerDefinition.id.label("offliner_definition_id"),
            OfflinerDefinition.offliner.label("offliner"),
            OfflinerDefinition.schema.label("offliner_schema"),
            OfflinerDefinition.version.label("offliner_version"),
            OfflinerDefinition.created_at.label("offliner_definition_created_at"),
            Schedule.name.label("schedule_name"),
            Worker.name.label("worker_name"),
        )
        .options(
            selectinload(Task.files),
            selectinload(Task.requested_by),
            selectinload(Task.canceled_by),
        )
        .join(OfflinerDefinition, Task.offliner_definition)
        .join(Schedule, Task.schedule, isouter=True)
        .join(Worker, Task.worker, isouter=True)
        .where(Task.id == task_id)
    )
    if row := session.execute(stmt).one_or_none():
        task = cast(Task, row.Task)
        return TaskFullSchema(
            id=task.id,
            status=task.status,
            timestamp=task.timestamp,
            config=ExpandedScheduleConfigSchema.model_validate(
                {
                    "warehouse_path": task.config["warehouse_path"],
                    "resources": task.config["resources"],
                    "platform": task.config.get("platform"),
                    "offliner": create_offliner_instance(
                        offliner=get_offliner(session, row.offliner),
                        offliner_definition=OfflinerDefinitionSchema(
                            id=row.offliner_definition_id,
                            version=row.offliner_version,
                            created_at=row.offliner_definition_created_at,
                            offliner=row.offliner,
                            schema_=OfflinerSpecSchema.model_validate(
                                row.offliner_schema
                            ),
                        ),
                        data=task.config["offliner"],
                        skip_validation=True,
                    ),
                    "monitor": parse_bool(task.config.get("monitor")),
                    "image": task.config["image"],
                    "mount_point": task.config["mount_point"],
                    "command": task.config["command"],
                    "str_command": task.config["str_command"],
                    "artifacts_globs": task.config.get("artifacts_globs", []),
                },
                context={"skip_validation": True},
            ),
            events=task.events,
            debug=task.debug,
            requested_by=task.requested_by.username,
            canceled_by=task.canceled_by.username if task.canceled_by else None,
            container=TaskContainerSchema.model_validate(task.container),
            priority=task.priority,
            notification=(
                ScheduleNotificationSchema.model_validate(task.notification)
                if task.notification
                else None
            ),
            files={file.name: create_task_file_schema(file) for file in task.files},
            upload=TaskUploadSchema.model_validate(task.upload),
            updated_at=task.updated_at,
            original_schedule_name=task.original_schedule_name,
            schedule_name=row.schedule_name,
            worker_name=row.worker_name,
            context=task.context,
            offliner_definition_id=row.offliner_definition_id,
            version=row.offliner_version,
            offliner=row.offliner,
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
            Task.context,
            Task.priority,
            Bundle(  # pyright: ignore[reportUnknownArgumentType]
                "config",
                Task.config["resources"].label("resources"),
            ),
            Task.updated_at,
            User.username.label("requested_by"),
            Schedule.name.label("schedule_name"),
            Worker.name.label("worker_name"),
        )
        .join(User, Task.requested_by)
        .join(Worker, Task.worker, isouter=True)
        .join(Schedule, Task.schedule, isouter=True)
        .where(
            (Schedule.name == schedule_name) | (schedule_name is None),
            (Task.status.in_(status)),
        )
        .order_by(
            get_status_timestamp_expr(Task.timestamp, TaskStatus.started).desc(),
            get_status_timestamp_expr(Task.timestamp, TaskStatus.reserved).desc(),
            Task.updated_at.desc(),
        )
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
        context,
        priority,
        config,
        updated_at,
        requested_by,
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
                context=context,
                priority=priority,
                config=ConfigWithOnlyResourcesSchema(
                    resources=ConfigResourcesSchema(
                        cpu=config.resources["cpu"],
                        disk=config.resources["disk"],
                        memory=config.resources["memory"],
                    ),
                ),
                updated_at=updated_at,
                requested_by=requested_by,
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
        upload=requested_task.upload.model_dump(mode="json"),
        original_schedule_name=requested_task.original_schedule_name,
        context=requested_task.context,
    )
    task.id = requested_task.id
    task.requested_by_id = get_user_by_username(
        session, username=requested_task.requested_by
    ).id
    task.schedule_id = requested_task.schedule_id
    task.worker_id = worker_id
    task.offliner_definition_id = requested_task.offliner_definition_id
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
            id=task.id,
            config=ExpandedScheduleConfigSchema.model_validate(
                {
                    **task.config,
                    "offliner": create_offliner_instance(
                        offliner=get_offliner(
                            session, task.offliner_definition.offliner
                        ),
                        offliner_definition=task.offliner_definition,
                        data=task.config["offliner"],
                        skip_validation=True,
                    ),
                },
                context={"skip_validation": True},
            ),
            schedule_name=task.schedule.name if task.schedule else None,
            timestamp=task.timestamp,
            updated_at=task.updated_at,
            worker_name=task.worker.name,
            status=task.status,
            **compute_task_eta(session, task),
        )
        for task in session.scalars(stmt).all()
    ]


def compute_task_eta(session: OrmSession, task: Task) -> dict[str, Any]:
    """compute task duration (dict), remaining (seconds) and eta (datetime)"""
    now = getnow()
    duration = get_schedule_duration(
        session,
        schedule_name=task.schedule.name if task.schedule else None,
        worker=task.worker,
    )
    elapsed = now - get_timestamp_for_status(
        task.timestamp, "started", get_timestamp_for_status(task.timestamp, "reserved")
    )
    remaining = max([duration.value - elapsed.total_seconds(), 60])  # seconds
    remaining *= 1.005  # .5% margin
    eta = now + datetime.timedelta(seconds=remaining)
    return {
        "duration": duration,
        "remaining": remaining,
        "eta": eta,
    }


def get_task_file_or_none(
    session: OrmSession, task_id: UUID, filename: str
) -> TaskFileSchema | None:
    """Get a task file by task id and file id."""
    file = session.scalars(
        select(File).where(File.task_id == task_id, File.name == filename)
    ).one_or_none()
    return create_task_file_schema(file) if file else None


def get_task_file(session: OrmSession, task_id: UUID, filename: str) -> TaskFileSchema:
    """Get a task file by task id and file name."""
    if file := get_task_file_or_none(session, task_id, filename):
        return file
    raise RecordDoesNotExistError(f"Task {task_id} has no file {filename}")


def create_or_update_task_file(
    session: OrmSession,
    request: FileCreateUpdateSchema,
):
    """Create or update a task file using insert with on conflict update."""
    values = request.model_dump(exclude_unset=True)
    stmt = insert(File).values(**values)
    stmt = stmt.on_conflict_do_update(
        index_elements=[File.task_id, File.name],
        set_={**request.model_dump(exclude_unset=True, exclude={"task_id", "name"})},
    )
    session.execute(stmt)
