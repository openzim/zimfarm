from collections.abc import Sequence
from http import HTTPStatus
from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from zimfarm_backend.api.routes.dependencies import (
    gen_dbsession,
    get_current_account,
    get_current_account_or_none,
    get_editable_team_ids,
    require_permission,
)
from zimfarm_backend.api.routes.http_errors import (
    NotFoundError,
)
from zimfarm_backend.api.routes.models import ListResponse
from zimfarm_backend.api.routes.tasks.models import (
    TaskCreateSchema,
    TasksGetSchema,
    TaskUpdateSchema,
)
from zimfarm_backend.common.constants import ENABLED_SCHEDULER, INFORM_CMS
from zimfarm_backend.common.enums import TaskStatus
from zimfarm_backend.common.schemas.models import (
    RecipeConfigSchema,
    calculate_pagination_metadata,
)
from zimfarm_backend.common.schemas.orms import TaskLightSchema
from zimfarm_backend.common.upload import (
    UPLOAD_SECRET_KEYS,
    build_task_upload_uris,
    populate_zim_urls,
)
from zimfarm_backend.common.utils import task_event_handler
from zimfarm_backend.db import account as db_account
from zimfarm_backend.db import offliner as db_offliner
from zimfarm_backend.db import offliner_definition as db_offliner_definition
from zimfarm_backend.db import requested_task as db_requested_task
from zimfarm_backend.db import tasks as db_tasks
from zimfarm_backend.db import worker as db_worker
from zimfarm_backend.db.models import Account
from zimfarm_backend.utils.offliners import expanded_config

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("")
def get_tasks(
    db_session: Annotated[Session, Depends(gen_dbsession)],
    params: Annotated[TasksGetSchema, Query()],
    accessible_team_ids: Annotated[
        Sequence[UUID] | None, Depends(get_editable_team_ids)
    ],
) -> ListResponse[TaskLightSchema]:
    """Get a list of tasks"""
    results = db_tasks.get_tasks(
        db_session,
        skip=params.skip,
        limit=params.limit,
        accessible_team_ids=accessible_team_ids,
        status=params.status,
        recipe_identifier=params.recipe_name or params.recipe_id,
        sort_criteria=params.sort_criteria,
        offliner=params.offliner,
        fetch_most_recent_tasks=params.fetch_most_recent_tasks,
    )
    return ListResponse(
        meta=calculate_pagination_metadata(
            nb_records=results.nb_records,
            skip=params.skip,
            limit=params.limit,
            page_size=len(results.records),
        ),
        items=results.records,
    )


@router.get("/{task_id}")
def get_task(
    task_id: Annotated[UUID, Path()],
    db_session: Annotated[Session, Depends(gen_dbsession)],
    current_account: Annotated[Account | None, Depends(get_current_account_or_none)],
    accessible_team_ids: Annotated[
        Sequence[UUID] | None, Depends(get_editable_team_ids)
    ],
    *,
    hide_secrets: Annotated[bool, Query()] = False,
) -> JSONResponse:
    """Get a task by ID"""
    task = db_tasks.get_task_by_id(db_session, task_id, accessible_team_ids)
    if not (
        current_account
        and db_account.check_account_permission(
            current_account, namespace="tasks", name="secrets"
        )
    ):
        task.notification = None
        show_secrets = False
    else:
        show_secrets = not hide_secrets
    offliner_definition = db_offliner_definition.get_offliner_definition_by_id(
        db_session, task.offliner_definition_id
    )
    offliner = db_offliner.get_offliner(db_session, offliner_definition.offliner)

    # Rebuild the config as the one that was retrieved from the DB has secrets saved
    task.config = expanded_config(
        cast(RecipeConfigSchema, task.config),
        offliner=offliner,
        offliner_definition=offliner_definition,
        show_secrets=show_secrets,
    )
    task.container.command = task.config.command
    task = build_task_upload_uris(
        task, keys=UPLOAD_SECRET_KEYS, show_secrets=show_secrets
    )
    if INFORM_CMS:
        populate_zim_urls(task)
    return JSONResponse(
        content=task.model_dump(mode="json", context={"show_secrets": show_secrets})
    )


@router.post(
    "/{requested_task_id}",
    dependencies=[Depends(require_permission(namespace="tasks", name="create"))],
)
def create_task(
    requested_task_id: Annotated[UUID, Path()],
    task_create_schema: TaskCreateSchema,
    db_session: Annotated[Session, Depends(gen_dbsession)],
    accessible_team_ids: Annotated[
        Sequence[UUID] | None, Depends(get_editable_team_ids)
    ],
):
    """Create a task from a requested task"""
    if not ENABLED_SCHEDULER:
        return JSONResponse(
            content={"message": "Scheduler is disabled"},
            status_code=HTTPStatus.NO_CONTENT,
        )

    requested_task = db_requested_task.get_requested_task_by_id(
        db_session, requested_task_id, accessible_team_ids
    )

    worker = db_worker.get_worker(
        db_session, worker_name=task_create_schema.worker_name
    )

    task = db_tasks.create_task(
        db_session,
        requested_task=requested_task,
        worker_id=worker.id,
        accessible_team_ids=accessible_team_ids,
    )

    task_event_handler(
        db_session,
        task.id,
        TaskStatus.reserved,
        {"worker": task_create_schema.worker_name},
    )

    db_requested_task.delete_requested_task(
        db_session, requested_task_id, accessible_team_ids
    )

    return JSONResponse(
        content=task.model_dump(mode="json", context={"show_secrets": True}),
        status_code=HTTPStatus.CREATED,
    )


@router.patch(
    "/{task_id}",
    dependencies=[Depends(require_permission(namespace="tasks", name="update"))],
)
def update_task(
    task_id: Annotated[UUID, Path()],
    task_update_schema: TaskUpdateSchema,
    db_session: Annotated[Session, Depends(gen_dbsession)],
    accessible_team_ids: Annotated[
        Sequence[UUID] | None, Depends(get_editable_team_ids)
    ],
):
    """Update a task"""
    task = db_tasks.get_task_by_id(db_session, task_id, accessible_team_ids)

    task_event_handler(
        db_session, task.id, task_update_schema.event, task_update_schema.payload
    )

    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.post(
    "/{task_id}/cancel",
    dependencies=[Depends(require_permission(namespace="tasks", name="cancel"))],
)
def cancel_task(
    task_id: Annotated[UUID, Path()],
    db_session: Annotated[Session, Depends(gen_dbsession)],
    current_account: Annotated[Account, Depends(get_current_account)],
    accessible_team_ids: Annotated[
        Sequence[UUID] | None, Depends(get_editable_team_ids)
    ],
):
    """Cancel a task"""

    task = db_tasks.get_task_by_id(db_session, task_id, accessible_team_ids)

    if task.status not in TaskStatus.incomplete():
        raise NotFoundError(f"Task {task_id} not found")

    task_event_handler(
        db_session,
        task.id,
        TaskStatus.cancel_requested,
        {"canceled_by": str(current_account.id)},
    )

    return Response(status_code=HTTPStatus.NO_CONTENT)
