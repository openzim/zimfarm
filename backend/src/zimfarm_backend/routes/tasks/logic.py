from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from zimfarm_backend import logger
from zimfarm_backend.common.constants import ENABLED_SCHEDULER
from zimfarm_backend.common.enums import TaskStatus
from zimfarm_backend.common.schemas.fields import LimitFieldMax200, SkipField
from zimfarm_backend.common.schemas.models import calculate_pagination_metadata
from zimfarm_backend.common.schemas.orms import TaskLightSchema
from zimfarm_backend.common.utils import task_event_handler
from zimfarm_backend.db.exceptions import (
    RecordAlreadyExistsError,
    RecordDoesNotExistError,
)
from zimfarm_backend.db.models import User
from zimfarm_backend.db.requested_task import (
    delete_requested_task as db_delete_requested_task,
)
from zimfarm_backend.db.requested_task import (
    get_requested_task_by_id as db_get_requested_task,
)
from zimfarm_backend.db.tasks import create_task as db_create_task
from zimfarm_backend.db.tasks import get_task_by_id as db_get_task
from zimfarm_backend.db.tasks import get_tasks as db_get_tasks
from zimfarm_backend.db.user import check_user_permission
from zimfarm_backend.db.worker import get_worker as db_get_worker
from zimfarm_backend.routes.dependencies import (
    gen_dbsession,
    get_current_user,
    get_current_user_or_none,
)
from zimfarm_backend.routes.http_errors import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ServerError,
)
from zimfarm_backend.routes.models import ListResponse
from zimfarm_backend.routes.tasks.models import TaskCreateSchema, TaskUpdateSchema

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("")
async def get_tasks(
    db_session: Annotated[Session, Depends(gen_dbsession)],
    skip: Annotated[SkipField, Query()] = 0,
    limit: Annotated[LimitFieldMax200, Query()] = 20,
    status: Annotated[list[TaskStatus] | None, Query()] = None,
    schedule_name: Annotated[str | None, Query()] = None,
) -> ListResponse[TaskLightSchema]:
    """Get a list of tasks"""
    results = db_get_tasks(
        db_session, skip=skip, limit=limit, status=status, schedule_name=schedule_name
    )
    return ListResponse(
        meta=calculate_pagination_metadata(
            nb_records=results.nb_records,
            skip=skip,
            limit=limit,
            page_size=len(results.tasks),
        ),
        items=results.tasks,
    )


@router.get("/{task_id}")
async def get_task(
    task_id: Annotated[UUID, Path()],
    db_session: Annotated[Session, Depends(gen_dbsession)],
    current_user: Annotated[User | None, Depends(get_current_user_or_none)],
    *,
    hide_secrets: Annotated[bool, Query()] = True,
) -> JSONResponse:
    """Get a task by ID"""
    try:
        task = db_get_task(db_session, task_id)
    except RecordDoesNotExistError as exc:
        raise NotFoundError(f"Task {task_id} not found") from exc
    if not (
        current_user
        and check_user_permission(current_user, namespace="schedules", name="update")
    ):
        task.notification = None

    # if the user does not have the appropriate permission, then their flag does
    # not matter
    if not (
        current_user
        and check_user_permission(current_user, namespace="tasks", name="create")
    ):
        show_secrets = False
    else:
        show_secrets = not hide_secrets

    return JSONResponse(
        content=task.model_dump(
            mode="json", context={"show_secrets": show_secrets}, by_alias=True
        )
    )


@router.post("/{requested_task_id}")
async def create_task(
    requested_task_id: Annotated[UUID, Path()],
    task_create_schema: TaskCreateSchema,
    db_session: Annotated[Session, Depends(gen_dbsession)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Create a task from a requested task"""
    if not ENABLED_SCHEDULER:
        return JSONResponse(
            content={"message": "Scheduler is disabled"},
            status_code=HTTPStatus.NO_CONTENT,
        )

    if not check_user_permission(current_user, namespace="tasks", name="create"):
        raise ForbiddenError("You are not allowed to create tasks")

    try:
        requested_task = db_get_requested_task(db_session, requested_task_id)
    except RecordDoesNotExistError as exc:
        raise NotFoundError(f"Requested task {requested_task_id} not found") from exc

    try:
        worker = db_get_worker(db_session, worker_name=task_create_schema.worker_name)
    except RecordDoesNotExistError as exc:
        raise NotFoundError(
            f"Worker {task_create_schema.worker_name} not found"
        ) from exc

    try:
        task = db_create_task(
            db_session, requested_task=requested_task, worker_id=worker.id
        )
    except RecordAlreadyExistsError as exc:
        raise ConflictError(f"Task {requested_task_id} already exists") from exc

    try:
        task_event_handler(
            db_session,
            task.id,
            TaskStatus.reserved,
            {"worker": task_create_schema.worker_name},
        )
    except Exception as exc:
        raise ServerError("Unable to create task.") from exc

    db_delete_requested_task(db_session, requested_task_id)

    return JSONResponse(
        content=task.model_dump(
            mode="json", context={"show_secrets": True}, by_alias=True
        ),
        status_code=HTTPStatus.CREATED,
    )


@router.patch("/{task_id}")
async def update_task(
    task_id: Annotated[UUID, Path()],
    task_update_schema: TaskUpdateSchema,
    db_session: Annotated[Session, Depends(gen_dbsession)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Update a task"""
    if not check_user_permission(current_user, namespace="tasks", name="update"):
        raise ForbiddenError("You are not allowed to update this task")

    try:
        task = db_get_task(db_session, task_id)
    except RecordDoesNotExistError as exc:
        raise NotFoundError(f"Task {task_id} not found") from exc

    try:
        task_event_handler(
            db_session, task.id, task_update_schema.event, task_update_schema.payload
        )
    except Exception as exc:
        logger.exception("Unexpected error while updating task.")
        raise ServerError("Unable to update task.") from exc

    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.post("/{task_id}/cancel")
async def cancel_task(
    task_id: Annotated[UUID, Path()],
    db_session: Annotated[Session, Depends(gen_dbsession)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Cancel a task"""
    if not check_user_permission(current_user, namespace="tasks", name="cancel"):
        raise ForbiddenError("You are not allowed to cancel this task")

    try:
        task = db_get_task(db_session, task_id)
    except RecordDoesNotExistError as exc:
        raise NotFoundError(f"Task {task_id} not found") from exc

    if task.status not in TaskStatus.incomplete():
        raise NotFoundError(f"Task {task_id} not found")

    try:
        task_event_handler(
            db_session,
            task.id,
            TaskStatus.cancel_requested,
            {"canceled_by": current_user.username},
        )
    except Exception as exc:
        raise ServerError("Unable to cancel task.") from exc

    return Response(status_code=HTTPStatus.NO_CONTENT)
