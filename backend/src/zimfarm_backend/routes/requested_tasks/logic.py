from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend import logger
from zimfarm_backend.common import WorkersIpChangesCounts, getnow
from zimfarm_backend.common.constants import (
    ENABLED_SCHEDULER,
    MAX_WORKER_IP_CHANGES_PER_DAY,
    USES_WORKERS_IPS_WHITELIST,
)
from zimfarm_backend.common.external import update_workers_whitelist
from zimfarm_backend.common.schemas.fields import (
    ZIMCPU,
    WorkerField,
    ZIMDisk,
    ZIMMemory,
)
from zimfarm_backend.common.schemas.models import calculate_pagination_metadata
from zimfarm_backend.common.schemas.orms import (
    ConfigResourcesSchema,
    ConfigWithOnlyOfflinerAndResourcesSchema,
    RequestedTaskFullSchema,
    RequestedTaskLightSchema,
)
from zimfarm_backend.common.utils import task_event_handler
from zimfarm_backend.db import gen_dbsession, gen_manual_dbsession
from zimfarm_backend.db.models import User
from zimfarm_backend.db.requested_task import (
    compute_requested_task_rank,
    find_requested_task_for_worker,
    get_requested_task_by_id,
    request_task,
    update_requested_task_priority,
)
from zimfarm_backend.db.requested_task import (
    delete_requested_task as db_delete_requested_task,
)
from zimfarm_backend.db.requested_task import (
    get_requested_tasks as db_get_requested_tasks,
)
from zimfarm_backend.db.schedule import count_enabled_schedules
from zimfarm_backend.db.user import check_user_permission
from zimfarm_backend.db.worker import get_worker, update_worker
from zimfarm_backend.routes.dependencies import (
    get_current_user,
    get_current_user_or_none,
    get_current_user_or_none_with_session,
)
from zimfarm_backend.routes.http_errors import (
    BadRequestError,
    ForbiddenError,
    NotFoundError,
    ServiceUnavailableError,
)
from zimfarm_backend.routes.models import ListResponse
from zimfarm_backend.routes.requested_tasks.models import (
    NewRequestedTaskSchema,
    NewRequestedTaskSchemaResponse,
    RequestedTaskSchema,
    UpdateRequestedTaskSchema,
)

router = APIRouter(prefix="/requested-tasks", tags=["requested-tasks"])


def record_ip_change(session: OrmSession, worker_name: str):
    """record that this worker changed its IP and trigger whitelist changes"""
    today = getnow().date()
    # counts and limits are per-day so reset it if date changed
    if today != WorkersIpChangesCounts.today:
        WorkersIpChangesCounts.reset()
    if WorkersIpChangesCounts.add(worker_name) <= MAX_WORKER_IP_CHANGES_PER_DAY:
        update_workers_whitelist(session)
    else:
        logger.error(
            f"Worker {worker_name} IP changes for {today} "
            f"is above limit ({MAX_WORKER_IP_CHANGES_PER_DAY}). Not updating whitelist!"
        )


@router.post("")
def create_request_task(
    new_requested_task: NewRequestedTaskSchema,
    session: OrmSession = Depends(gen_dbsession),
    current_user: User = Depends(get_current_user),
):
    """Create requested task from a list of schedule_names"""
    if not check_user_permission(current_user, namespace="tasks", name="request"):
        raise ForbiddenError("You are not allowed to request tasks")

    if count_enabled_schedules(session, new_requested_task.schedule_names) == 0:
        raise NotFoundError(
            "No enabled schedules found for the given names",
        )

    requested_tasks: list[RequestedTaskFullSchema] = []
    errors: dict[str, str] = {}
    for schedule_name in new_requested_task.schedule_names:
        result = request_task(
            session,
            schedule_name=schedule_name,
            requested_by=current_user.username,
            worker_name=new_requested_task.worker,
            priority=new_requested_task.priority or 0,
        )
        if result.error:
            errors[schedule_name] = result.error

        if result.requested_task:
            requested_tasks.append(result.requested_task)

    if errors:
        raise BadRequestError(message="Unable to request tasks", errors=errors)

    # trigger event handlers
    for requested_task in requested_tasks:
        task_event_handler(session, requested_task.id, "requested", {})

    return NewRequestedTaskSchemaResponse(
        requested=[requested_task.id for requested_task in requested_tasks]
    )


@router.get("")
def get_requested_tasks(
    requested_task_schema: Annotated[RequestedTaskSchema, Query()],
    session: Annotated[OrmSession, Depends(gen_dbsession)],
    current_user: Annotated[User | None, Depends(get_current_user_or_none)],
) -> ListResponse[RequestedTaskLightSchema]:
    """Get list of requested tasks for user."""
    if current_user and requested_task_schema.worker:
        update_worker(session, worker_name=requested_task_schema.worker)

    skip = requested_task_schema.skip or 0
    limit = requested_task_schema.limit or 20

    results = db_get_requested_tasks(
        session,
        worker_name=requested_task_schema.worker,
        skip=skip,
        limit=limit,
        matching_offliners=(
            requested_task_schema.matching_offliners
            if requested_task_schema.matching_offliners is not None
            else None
        ),
        schedule_name=requested_task_schema.schedule_name,
        priority=requested_task_schema.priority,
        cpu=requested_task_schema.matching_cpu,
        memory=requested_task_schema.matching_memory,
        disk=requested_task_schema.matching_disk,
    )
    return ListResponse(
        meta=calculate_pagination_metadata(
            nb_records=results.nb_records,
            skip=skip,
            limit=limit,
            page_size=len(results.requested_tasks),
        ),
        items=results.requested_tasks,
    )


@router.get("/worker")
def get_requested_tasks_for_worker(
    request: Request,
    worker_name: Annotated[WorkerField, Query()],
    avail_cpu: Annotated[ZIMCPU, Query()],
    avail_memory: Annotated[ZIMMemory, Query()],
    avail_disk: Annotated[ZIMDisk, Query()],
    session: Annotated[OrmSession, Depends(gen_manual_dbsession)],
    current_user: Annotated[
        User, Depends(get_current_user_or_none_with_session(session_type="manual"))
    ],
) -> ListResponse[RequestedTaskLightSchema]:
    """Get list of requested tasks for a worker."""

    worker = get_worker(session, worker_name=worker_name)

    fallback_ip = request.client.host if request.client else None
    x_forwarded_for = request.headers.get("X-Forwarded-For", fallback_ip)
    if worker.user.username == current_user.username:
        ip_changed = str(worker.last_ip) != x_forwarded_for

        if ip_changed:
            logger.info(
                f"Worker {worker_name} IP changed from {worker.last_ip} to "
                f"{x_forwarded_for}"
            )
            worker = update_worker(
                session, worker_name=worker_name, ip_address=x_forwarded_for
            )
        else:
            worker = update_worker(session, worker_name=worker_name)

        # commit explicitly last_ip and last_seen changes, since we are not
        # using an explicit transaction, and do it before calling Wasabi so
        # that changes are propagated quickly and transaction is not blocking
        session.commit()

        if ip_changed and USES_WORKERS_IPS_WHITELIST:
            try:
                record_ip_change(session, worker_name)
            except Exception as exc:
                logger.exception("Pushing IP changes to Wasabi failed")
                raise ServiceUnavailableError(
                    "Pushing IP changes to Wasabi failed"
                ) from exc

    if not ENABLED_SCHEDULER:
        return ListResponse(
            meta=calculate_pagination_metadata(
                nb_records=0,
                skip=0,
                limit=0,
                page_size=0,
            ),
            items=[],
        )

    task = find_requested_task_for_worker(
        session=session,
        worker_name=worker_name,
        username=current_user.username,
        avail_cpu=avail_cpu,
        avail_memory=avail_memory,
        avail_disk=avail_disk,
    )

    return ListResponse(
        meta=calculate_pagination_metadata(
            nb_records=1 if task else 0,
            skip=0,
            limit=1,
            page_size=1 if task else 0,
        ),
        items=(
            [
                RequestedTaskLightSchema(
                    id=task.id,
                    status=task.status,
                    schedule_name=task.schedule_name,
                    config=ConfigWithOnlyOfflinerAndResourcesSchema(
                        offliner=cast(
                            str,
                            task.config.offliner.offliner_id,  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
                        ),
                        resources=ConfigResourcesSchema(
                            cpu=task.config.resources.cpu,
                            memory=task.config.resources.memory,
                            disk=task.config.resources.disk,
                        ),
                    ),
                    timestamp=task.timestamp,
                    requested_by=task.requested_by,
                    priority=task.priority,
                    original_schedule_name=task.original_schedule_name,
                    worker_name=task.worker_name,
                    updated_at=task.updated_at,
                    context=task.context,
                ),
            ]
            if task
            else []
        ),
    )


@router.get("/{requested_task_id}")
def get_requested_task(
    requested_task_id: Annotated[UUID, Path()],
    session: Annotated[OrmSession, Depends(gen_dbsession)],
    current_user: Annotated[User | None, Depends(get_current_user_or_none)],
    *,
    hide_secrets: Annotated[bool | None, Query()] = True,
) -> JSONResponse:
    """Get a requested task by ID."""
    requested_task = get_requested_task_by_id(session, requested_task_id)

    # also fetch all requested tasks IDs to compute estimated task rank ; this is
    # only an indicator for zimit.kiwix.org where duration is unknown because
    # schedule is created on-demand and all tasks have access to same worker(s) ;
    # sorting by priority and updated_at won't give a good indicator in other cases
    requested_task.rank = compute_requested_task_rank(session, requested_task_id)

    # exclude notification to not expose private information (privacy)
    # on anonymous requests and requests for users without schedules_update
    if not (
        current_user
        and check_user_permission(current_user, namespace="schedules", name="update")
    ):
        requested_task.notification = None

    # if the user doesn't have permission, then their flag to hide secret
    # does not matter
    if not (
        current_user
        and check_user_permission(current_user, namespace="schedules", name="update")
    ):
        show_secrets = False
    else:
        show_secrets = not hide_secrets

    return JSONResponse(
        content=requested_task.model_dump(
            context={"show_secrets": show_secrets}, mode="json"
        )
    )


@router.patch("/{requested_task_id}")
def update_requested_task(
    requested_task_id: Annotated[UUID, Path()],
    update_requested_task_schema: UpdateRequestedTaskSchema,
    session: Annotated[OrmSession, Depends(gen_dbsession)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> RequestedTaskFullSchema:
    """Update the priority of a requested task."""
    if not check_user_permission(current_user, namespace="tasks", name="update"):
        raise ForbiddenError("You are not allowed to update requested tasks")

    get_requested_task_by_id(session, requested_task_id)

    return update_requested_task_priority(
        session, requested_task_id, update_requested_task_schema.priority
    )


@router.delete("/{requested_task_id}")
def delete_requested_task(
    requested_task_id: Annotated[UUID, Path()],
    session: Annotated[OrmSession, Depends(gen_dbsession)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> JSONResponse:
    """Delete a requested task by ID."""
    if not check_user_permission(current_user, namespace="tasks", name="unrequest"):
        raise ForbiddenError("You are not allowed to unrequest tasks")

    db_delete_requested_task(session, requested_task_id)

    return JSONResponse(content={"deleted": 1})
