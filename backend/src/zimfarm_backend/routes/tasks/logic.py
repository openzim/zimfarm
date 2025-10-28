from http import HTTPStatus
from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from zimfarm_backend.common.constants import ENABLED_SCHEDULER
from zimfarm_backend.common.enums import TaskStatus
from zimfarm_backend.common.schemas.fields import (
    LimitFieldMax200,
    SkipField,
)
from zimfarm_backend.common.schemas.models import (
    ScheduleConfigSchema,
    calculate_pagination_metadata,
)
from zimfarm_backend.common.schemas.orms import TaskLightSchema
from zimfarm_backend.common.utils import task_event_handler
from zimfarm_backend.db.models import User
from zimfarm_backend.db.offliner import get_offliner as db_get_offliner
from zimfarm_backend.db.offliner_definition import (
    get_offliner_definition_by_id as db_get_offliner_definition_by_id,
)
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
    ForbiddenError,
    NotFoundError,
)
from zimfarm_backend.routes.models import ListResponse
from zimfarm_backend.routes.tasks.models import TaskCreateSchema, TaskUpdateSchema
from zimfarm_backend.utils.offliners import expanded_config

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
    hide_secrets: Annotated[bool, Query()] = False,
) -> JSONResponse:
    """Get a task by ID"""
    task = db_get_task(db_session, task_id)
    if not (
        current_user
        and check_user_permission(current_user, namespace="tasks", name="secrets")
    ):
        task.notification = None
        show_secrets = False
    else:
        show_secrets = not hide_secrets
    offliner_definition = db_get_offliner_definition_by_id(
        db_session, task.offliner_definition_id
    )
    offliner = db_get_offliner(db_session, offliner_definition.offliner)

    # Rebuild the config as the one that was retrieved from the DB has secrets saved
    task.config = expanded_config(
        cast(ScheduleConfigSchema, task.config),
        offliner=offliner,
        offliner_definition=offliner_definition,
        show_secrets=show_secrets,
    )
    return JSONResponse(
        content=task.model_dump(mode="json", context={"show_secrets": show_secrets})
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

    requested_task = db_get_requested_task(db_session, requested_task_id)

    worker = db_get_worker(db_session, worker_name=task_create_schema.worker_name)

    task = db_create_task(
        db_session, requested_task=requested_task, worker_id=worker.id
    )

    task_event_handler(
        db_session,
        task.id,
        TaskStatus.reserved,
        {"worker": task_create_schema.worker_name},
    )

    db_delete_requested_task(db_session, requested_task_id)

    return JSONResponse(
        content=task.model_dump(mode="json", context={"show_secrets": True}),
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

    task = db_get_task(db_session, task_id)

    task_event_handler(
        db_session, task.id, task_update_schema.event, task_update_schema.payload
    )

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

    task = db_get_task(db_session, task_id)

    if task.status not in TaskStatus.incomplete():
        raise NotFoundError(f"Task {task_id} not found")

    task_event_handler(
        db_session,
        task.id,
        TaskStatus.cancel_requested,
        {"canceled_by": current_user.username},
    )

    return Response(status_code=HTTPStatus.NO_CONTENT)
