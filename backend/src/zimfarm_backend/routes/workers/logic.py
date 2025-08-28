from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common.schemas.fields import LimitFieldMax200, SkipField
from zimfarm_backend.common.schemas.models import calculate_pagination_metadata
from zimfarm_backend.common.schemas.orms import WorkerLightSchema, WorkerMetricsSchema
from zimfarm_backend.db.exceptions import RecordDoesNotExistError
from zimfarm_backend.db.models import User
from zimfarm_backend.db.user import check_user_permission
from zimfarm_backend.db.worker import check_in_worker as db_check_in_worker
from zimfarm_backend.db.worker import get_active_workers as db_get_active_workers
from zimfarm_backend.db.worker import get_worker as db_get_worker
from zimfarm_backend.db.worker import get_worker_metrics as db_get_worker_metrics
from zimfarm_backend.db.worker import update_worker as db_update_worker
from zimfarm_backend.routes.dependencies import gen_dbsession, get_current_user
from zimfarm_backend.routes.http_errors import (
    BadRequestError,
    NotFoundError,
    UnauthorizedError,
)
from zimfarm_backend.routes.models import ListResponse
from zimfarm_backend.routes.workers.models import (
    WorkerCheckInSchema,
    WorkerUpdateSchema,
)

router = APIRouter(prefix="/workers", tags=["workers"])


@router.get("")
async def get_active_workers(
    session: Annotated[OrmSession, Depends(gen_dbsession)],
    skip: Annotated[SkipField, Query()] = 0,
    limit: Annotated[LimitFieldMax200, Query()] = 20,
) -> ListResponse[WorkerLightSchema]:
    """Get a list of active workers."""
    results = db_get_active_workers(session, skip=skip, limit=limit)
    return ListResponse(
        meta=calculate_pagination_metadata(
            nb_records=results.nb_records,
            skip=skip,
            limit=limit,
            page_size=len(results.workers),
        ),
        items=results.workers,
    )


@router.get("/{name}/metrics")
async def get_worker_metrics(
    name: Annotated[str, Path()],
    session: Annotated[OrmSession, Depends(gen_dbsession)],
) -> WorkerMetricsSchema:
    """Get a single worker with full details and metrics."""
    try:
        return db_get_worker_metrics(session, worker_name=name)
    except RecordDoesNotExistError as exc:
        raise NotFoundError(f"Worker {name} not found") from exc


@router.put("/{name}/context")
async def update_worker_context(
    name: Annotated[str, Path()],
    request: WorkerUpdateSchema,
    session: Annotated[OrmSession, Depends(gen_dbsession)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    """Update the context of a worker."""
    try:
        worker = db_get_worker(session, worker_name=name)
    except RecordDoesNotExistError as exc:
        raise NotFoundError(f"Worker {name} not found") from exc

    if not (check_user_permission(current_user, namespace="users", name="update")):
        raise UnauthorizedError("You are not allowed to access this resource")

    if worker.deleted:
        raise BadRequestError("Worker has been marked as deleted")

    db_update_worker(session, worker_name=name, contexts=request.contexts)
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.put("/{name}/check-in")
async def check_in_worker(
    name: Annotated[str, Path()],
    worker_checkin: WorkerCheckInSchema,
    session: Annotated[OrmSession, Depends(gen_dbsession)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    """Check in a worker."""
    try:
        worker = db_get_worker(session, worker_name=name)
    except RecordDoesNotExistError as exc:
        raise NotFoundError(f"Worker {name} not found") from exc

    if worker.deleted:
        raise BadRequestError("Worker has been marked as deleted")

    # if worker.user_id != current_user.id:
    #     raise BadRequestError("Worker is not associated with the current user")
    db_check_in_worker(
        session,
        worker_name=name,
        cpu=worker_checkin.cpu,
        memory=worker_checkin.memory,
        disk=worker_checkin.disk,
        selfish=worker_checkin.selfish or False,
        offliners=worker_checkin.offliners,
        platforms=worker_checkin.platforms,
        user_id=current_user.id,
    )
    return Response(status_code=HTTPStatus.NO_CONTENT)
