from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.api.routes.dependencies import (
    gen_dbsession,
    get_current_account,
    get_current_account_or_none,
    require_permission,
)
from zimfarm_backend.api.routes.http_errors import (
    BadRequestError,
    ForbiddenError,
    UnauthorizedError,
)
from zimfarm_backend.api.routes.models import ListResponse
from zimfarm_backend.api.routes.workers.models import (
    KeySchema,
    WorkerCheckInResponse,
    WorkerCheckInSchema,
    WorkerCreateSchema,
    WorkerUpdateSchema,
)
from zimfarm_backend.common.constants import GITHUB_TOKEN
from zimfarm_backend.common.schemas.fields import (
    LimitFieldMax200,
    NotEmptyString,
    SkipField,
)
from zimfarm_backend.common.schemas.models import (
    DockerImageVersionSchema,
    calculate_pagination_metadata,
)
from zimfarm_backend.common.schemas.orms import (
    BaseWorkerWithSshKeysSchema,
    SshKeyRead,
    WorkerLightSchema,
    WorkerMetricsSchema,
)
from zimfarm_backend.db import account as db_account
from zimfarm_backend.db import models as db_models
from zimfarm_backend.db import ssh_key as db_ssh_key
from zimfarm_backend.db import worker as db_worker
from zimfarm_backend.utils.github_registry import (
    WorkerManagerVersion,
    get_latest_worker_manager_version,
)

router = APIRouter(prefix="/workers", tags=["workers"])


def require_permission_if_not_worker_itself(namespace: str, name: str):
    """
    Ensure an account has permission to perform action on a worker that isn't
    the worker itself.
    """

    def _require_permission_if_not_worker_owner(
        worker_name: Annotated[NotEmptyString, Path()],
        db_session: Annotated[OrmSession, Depends(gen_dbsession)],
        current_account: Annotated[db_models.Account, Depends(get_current_account)],
    ):
        worker = db_worker.get_worker(db_session, worker_name=worker_name)
        if worker.account_id == current_account.id:
            return

        if not db_account.check_account_permission(
            current_account, namespace=namespace, name=name
        ):
            raise ForbiddenError("You are not allowed to access this resource")

    return _require_permission_if_not_worker_owner


@router.get("")
def get_workers(
    session: Annotated[OrmSession, Depends(gen_dbsession)],
    current_account: Annotated[
        db_models.Account | None, Depends(get_current_account_or_none)
    ],
    skip: Annotated[SkipField, Query()] = 0,
    limit: Annotated[LimitFieldMax200, Query()] = 20,
    *,
    hide_offlines: Annotated[bool, Query()] = False,
) -> ListResponse[WorkerLightSchema]:
    """Get a list of workers."""
    results = db_worker.get_workers(
        session,
        skip=skip,
        limit=limit,
        hide_offlines=hide_offlines,
        show_secrets=current_account is not None
        and db_account.check_account_permission(
            current_account, namespace="workers", name="secrets"
        ),
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


@router.post(
    "",
    dependencies=[Depends(require_permission(namespace="workers", name="create"))],
)
def create_worker(
    session: Annotated[OrmSession, Depends(gen_dbsession)],
    request: WorkerCreateSchema,
):
    db_worker.create_worker(
        session,
        worker_name=request.name,
        ssh_key=request.ssh_key,
    )
    return Response(status_code=HTTPStatus.CREATED)


@router.put(
    "/{worker_name}",
    dependencies=[Depends(require_permission(namespace="workers", name="update"))],
)
def update_worker(
    worker_name: Annotated[str, Path()],
    request: WorkerUpdateSchema,
    session: Annotated[OrmSession, Depends(gen_dbsession)],
) -> Response:
    """Update a worker."""
    worker = db_worker.get_worker(session, worker_name=worker_name)

    if worker.deleted:
        raise BadRequestError("Worker has been marked as deleted")

    if not request.model_dump(exclude_unset=True):
        raise BadRequestError("No changes made to worker because nothing was set.")

    db_worker.update_worker(
        session,
        worker_name=worker_name,
        contexts=request.contexts if request.contexts is not None else {},
        admin_disabled=request.admin_disabled,
        update_last_seen=False,
    )
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.get("/{worker_name}")
def get_worker(
    worker_name: Annotated[str, Path()],
    session: Annotated[OrmSession, Depends(gen_dbsession)],
    current_account: Annotated[
        db_models.Account | None, Depends(get_current_account_or_none)
    ],
) -> WorkerMetricsSchema:
    """Get a single worker with full details and metrics."""
    return db_worker.get_worker_metrics(
        session,
        worker_name=worker_name,
        show_secrets=current_account is not None
        and db_account.check_account_permission(
            current_account, namespace="workers", name="secrets"
        ),
    )


@router.put("/{worker_name}/check-in")
def check_in_worker(
    worker_name: Annotated[NotEmptyString, Path()],
    worker_checkin: WorkerCheckInSchema,
    session: Annotated[OrmSession, Depends(gen_dbsession)],
    current_account: Annotated[db_models.Account, Depends(get_current_account)],
) -> WorkerCheckInResponse:
    """Check in a worker."""

    worker = db_worker.get_worker(session, worker_name=worker_name)

    if worker.deleted:
        raise BadRequestError("Worker has been marked as deleted")

    if worker.account_id != current_account.id:
        raise BadRequestError("Worker is not associated with the current user")

    # set defaults for docker image in case worker cannot retrieve details as
    # Docker API might change
    if worker:
        # use the worker's existing data for the checkin to avoid overriding with None
        docker_image_hash = worker.docker_image_hash
        docker_image_created_at = worker.docker_image_created_at
    else:
        docker_image_hash, docker_image_created_at = None, None

    db_worker.check_in_worker(
        session,
        worker_name=worker_name,
        cpu=worker_checkin.cpu,
        memory=worker_checkin.memory,
        disk=worker_checkin.disk,
        selfish=worker_checkin.selfish or False,
        offliners=worker_checkin.offliners,
        platforms=worker_checkin.platforms,
        cordoned=worker_checkin.cordoned or False,
        account_id=current_account.id,
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


@router.post(
    "/{worker_name}/keys",
    dependencies=[
        Depends(
            require_permission_if_not_worker_itself(
                namespace="workers", name="ssh_keys"
            )
        )
    ],
)
def create_worker_key(
    worker_name: Annotated[NotEmptyString, Path()],
    ssh_key: KeySchema,
    db_session: Annotated[OrmSession, Depends(gen_dbsession)],
) -> SshKeyRead:
    """Create a new SSH key for a worker"""
    worker = db_worker.get_worker(db_session, worker_name=worker_name)
    return db_ssh_key.create_ssh_key_read_schema(
        db_ssh_key.create_ssh_key(db_session, worker_id=worker.id, ssh_key=ssh_key)
    )


@router.get(
    "/{worker_name}/keys",
    dependencies=[Depends(require_permission(namespace="workers", name="ssh_keys"))],
)
def get_worker_keys(
    worker_name: Annotated[NotEmptyString, Path()],
    db_session: Annotated[OrmSession, Depends(gen_dbsession)],
) -> ListResponse[SshKeyRead]:
    """Get a list of SSH keys for a worker"""
    worker = db_worker.get_worker(db_session, worker_name=worker_name)
    results = db_ssh_key.get_ssh_keys(db_session, worker_id=worker.id)
    page_size = len(results.ssh_keys)
    return ListResponse(
        meta=calculate_pagination_metadata(
            nb_records=results.nb_records,
            skip=0,
            limit=page_size,
            page_size=page_size,
        ),
        items=results.ssh_keys,
    )


@router.get(
    "/image/latest",
)
def get_latest_worker_image() -> DockerImageVersionSchema:
    version = get_latest_worker_manager_version()
    if version is None:
        raise BadRequestError("Unable to fetch latest worker image details.")
    return DockerImageVersionSchema(hash=version.hash, created_at=version.created_at)


@router.get("/{worker_name}/keys/{fingerprint:path}")
def get_ssh_key(
    worker_name: Annotated[str, Path()],
    fingerprint: Annotated[str, Path()],
    db_session: Annotated[OrmSession, Depends(gen_dbsession)],
    with_permission: Annotated[list[str] | None, Query()] = None,
) -> BaseWorkerWithSshKeysSchema:
    """Get a specific SSH key for a worker"""
    key_record = db_ssh_key.get_ssh_key_by_fingerprint(
        db_session, fingerprint=fingerprint
    )

    if worker_name != "-":
        db_worker.get_worker(db_session, worker_name=worker_name)

    requested_permissions = with_permission or []
    for permission in requested_permissions:
        namespace, perm_name = permission.split(".", 1)
        if key_record.worker.account.scope and not key_record.worker.account.scope.get(
            namespace, {}
        ).get(perm_name):
            raise UnauthorizedError(permission)

    return BaseWorkerWithSshKeysSchema(
        worker_name=key_record.worker.name,
        key=key_record.key,
        name=key_record.name,
        type=key_record.type,
    )


@router.delete(
    "/{worker_name}/keys/{fingerprint:path}",
    dependencies=[
        Depends(
            require_permission_if_not_worker_itself(
                namespace="workers", name="ssh_keys"
            )
        )
    ],
)
def delete_account_key(
    worker_name: Annotated[NotEmptyString, Path()],
    fingerprint: Annotated[str, Path()],
    db_session: Annotated[OrmSession, Depends(gen_dbsession)],
) -> Response:
    """Delete a specific SSH key for an account"""
    worker = db_worker.get_worker(db_session, worker_name=worker_name)
    db_ssh_key.get_ssh_key_by_fingerprint(db_session, fingerprint=fingerprint)
    db_ssh_key.delete_ssh_key(db_session, fingerprint=fingerprint, worker_id=worker.id)
    return Response(status_code=HTTPStatus.NO_CONTENT)
