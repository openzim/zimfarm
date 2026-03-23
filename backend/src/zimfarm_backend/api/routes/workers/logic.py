from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.api.routes.dependencies import (
    gen_dbsession,
    get_current_user,
    get_current_user_or_none,
    require_permission,
)
from zimfarm_backend.api.routes.http_errors import BadRequestError
from zimfarm_backend.api.routes.models import ListResponse
from zimfarm_backend.api.routes.workers.models import (
    WorkerCheckInResponse,
    WorkerCheckInSchema,
    WorkerUpdateSchema,
)
from zimfarm_backend.common.constants import GITHUB_TOKEN
from zimfarm_backend.common.schemas.fields import LimitFieldMax200, SkipField
from zimfarm_backend.common.schemas.models import (
    DockerImageVersionSchema,
    calculate_pagination_metadata,
)
from zimfarm_backend.common.schemas.orms import WorkerLightSchema, WorkerMetricsSchema
from zimfarm_backend.db.models import User
from zimfarm_backend.db.user import check_user_permission
from zimfarm_backend.db.worker import check_in_worker as db_check_in_worker
from zimfarm_backend.db.worker import (
    get_worker as db_get_worker,
)
from zimfarm_backend.db.worker import get_worker_metrics as db_get_worker_metrics
from zimfarm_backend.db.worker import (
    get_worker_or_none as db_get_worker_or_none,
)
from zimfarm_backend.db.worker import get_workers as db_get_workers
from zimfarm_backend.db.worker import update_worker as db_update_worker
from zimfarm_backend.utils.github_registry import (
    WorkerManagerVersion,
    get_latest_worker_manager_version,
)

router = APIRouter(prefix="/workers", tags=["workers"])


@router.get("")
def get_workers(
    session: Annotated[OrmSession, Depends(gen_dbsession)],
    current_user: Annotated[User | None, Depends(get_current_user_or_none)],
    skip: Annotated[SkipField, Query()] = 0,
    limit: Annotated[LimitFieldMax200, Query()] = 20,
    *,
    hide_offlines: Annotated[bool, Query()] = False,
) -> ListResponse[WorkerLightSchema]:
    """Get a list of workers."""
    results = db_get_workers(
        session,
        skip=skip,
        limit=limit,
        hide_offlines=hide_offlines,
        show_secrets=current_user is not None
        and check_user_permission(current_user, namespace="workers", name="secrets"),
    )
    return ListResponse(
        meta=calculate_pagination_metadata(
            nb_records=results.nb_records,
            skip=skip,
            limit=limit,
            page_size=len(results.workers),
        ),
        items=results.workers,
    )


@router.put(
    "/{name}",
    dependencies=[Depends(require_permission(namespace="workers", name="update"))],
)
def update_worker(
    name: Annotated[str, Path()],
    request: WorkerUpdateSchema,
    session: Annotated[OrmSession, Depends(gen_dbsession)],
) -> Response:
    """Update a worker."""
    worker = db_get_worker(session, worker_name=name)

    if worker.deleted:
        raise BadRequestError("Worker has been marked as deleted")

    if not request.model_dump(exclude_unset=True):
        raise BadRequestError("No changes made to worker because nothing was set.")

    db_update_worker(
        session,
        worker_name=name,
        contexts=request.contexts if request.contexts is not None else {},
        admin_disabled=request.admin_disabled,
        update_last_seen=False,
    )
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.get("/{name}")
def get_worker(
    name: Annotated[str, Path()],
    session: Annotated[OrmSession, Depends(gen_dbsession)],
    current_user: Annotated[User | None, Depends(get_current_user_or_none)],
) -> WorkerMetricsSchema:
    """Get a single worker with full details and metrics."""
    return db_get_worker_metrics(
        session,
        worker_name=name,
        show_secrets=current_user is not None
        and check_user_permission(current_user, namespace="workers", name="secrets"),
    )


@router.put(
    "/{name}/check-in",
    dependencies=[Depends(require_permission(namespace="workers", name="create"))],
)
def check_in_worker(
    name: Annotated[str, Path()],
    worker_checkin: WorkerCheckInSchema,
    session: Annotated[OrmSession, Depends(gen_dbsession)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> WorkerCheckInResponse:
    """Check in a worker."""

    worker = db_get_worker_or_none(session, worker_name=name)

    if worker is not None:
        if worker.deleted:
            raise BadRequestError("Worker has been marked as deleted")

        if worker.user_id != current_user.id:
            raise BadRequestError("Worker is not associated with the current user")

    # set defaults for docker image in case worker cannot retrieve details as
    # Docker API might change
    if worker:
        # use the worker's existing data for the checkin to avoid overriding with None
        docker_image_hash = worker.docker_image_hash
        docker_image_created_at = worker.docker_image_created_at
    else:
        docker_image_hash, docker_image_created_at = None, None

    db_check_in_worker(
        session,
        worker_name=name,
        cpu=worker_checkin.cpu,
        memory=worker_checkin.memory,
        disk=worker_checkin.disk,
        selfish=worker_checkin.selfish or False,
        offliners=worker_checkin.offliners,
        platforms=worker_checkin.platforms,
        cordoned=worker_checkin.cordoned or False,
        user_id=current_user.id,
        docker_image_hash=(
            worker_checkin.docker_image.hash
            if worker_checkin.docker_image
            else docker_image_hash
        ),
        docker_image_created_at=(
            worker_checkin.docker_image.created_at
            if worker_checkin.docker_image
            else docker_image_created_at
        ),
    )

    # Fetch latest worker manager version from GitHub Container Registry
    worker_manager_version: WorkerManagerVersion | None = None
    if GITHUB_TOKEN:
        worker_manager_version = get_latest_worker_manager_version()

    return WorkerCheckInResponse(
        worker_manager=(
            DockerImageVersionSchema(
                hash=worker_manager_version.hash,
                created_at=worker_manager_version.created_at,
            )
            if worker_manager_version
            else None
        )
    )


@router.get(
    "/image/latest",
)
def get_latest_worker_image() -> DockerImageVersionSchema:
    version = get_latest_worker_manager_version()
    if version is None:
        raise BadRequestError("Unable to fetch latest worker image details.")
    return DockerImageVersionSchema(hash=version.hash, created_at=version.created_at)
