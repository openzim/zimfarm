from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, Response
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.api.routes.blobs.models import (
    BlobsGetSchema,
    CreateBlobRequest,
    UpdateBlobRequest,
)
from zimfarm_backend.api.routes.dependencies import (
    gen_dbsession,
    require_permission,
)
from zimfarm_backend.api.routes.http_errors import BadRequestError
from zimfarm_backend.api.routes.models import ListResponse
from zimfarm_backend.common.schemas.fields import (
    NotEmptyString,
)
from zimfarm_backend.common.schemas.models import calculate_pagination_metadata
from zimfarm_backend.common.schemas.offliners.transformers import (
    prepare_blob,
    upload_blob,
)
from zimfarm_backend.common.schemas.orms import BlobSchema, CreateBlobSchema
from zimfarm_backend.db.blob import create_or_update_blob as db_create_or_update_blob
from zimfarm_backend.db.blob import delete_blob as db_delete_blob
from zimfarm_backend.db.blob import get_blob as db_get_blob
from zimfarm_backend.db.blob import get_blob_by_id as db_get_blob_by_id
from zimfarm_backend.db.blob import get_blob_or_none as db_get_blob_or_none
from zimfarm_backend.db.blob import get_blobs as db_get_blobs
from zimfarm_backend.db.exceptions import RecordDoesNotExistError
from zimfarm_backend.db.schedule import get_schedule

router = APIRouter(prefix="/blobs", tags=["blobs"])


@router.post(
    "/{schedule_name}",
    dependencies=[Depends(require_permission(namespace="schedules", name="create"))],
)
async def create_blob(
    schedule_name: Annotated[NotEmptyString, Path()],
    request: CreateBlobRequest,
    session: Annotated[OrmSession, Depends(gen_dbsession)],
) -> BlobSchema:
    "Create a blob for schedule"

    prepared_blob = prepare_blob(
        blob_data=request.data, flag_name=request.flag_name, kind=request.kind
    )
    schedule = get_schedule(session, schedule_name=schedule_name)

    if existing_blob := db_get_blob_or_none(
        session,
        schedule_id=schedule.id,
        flag_name=request.flag_name,
        checksum=prepared_blob.checksum,
    ):
        return existing_blob

    upload_blob(prepared_blob)

    db_create_or_update_blob(
        session,
        schedule_id=schedule.id,
        request=CreateBlobSchema(
            flag_name=request.flag_name,
            kind=request.kind,
            checksum=prepared_blob.checksum,
            comments=request.comments,
            url=prepared_blob.public_url,
        ),
    )
    return db_get_blob(
        session,
        schedule_id=schedule.id,
        flag_name=request.flag_name,
        checksum=prepared_blob.checksum,
    )


@router.get(
    "/{schedule_name}",
    dependencies=[Depends(require_permission(namespace="schedules", name="read"))],
)
async def get_blobs(
    schedule_name: Annotated[NotEmptyString, Path()],
    session: Annotated[OrmSession, Depends(gen_dbsession)],
    params: Annotated[BlobsGetSchema, Query()],
):
    """Get a list of all available blobs for schedule"""
    result = db_get_blobs(
        session,
        skip=params.skip,
        limit=params.limit,
        schedule_name=schedule_name,
    )
    return ListResponse(
        items=result.blobs,
        meta=calculate_pagination_metadata(
            nb_records=result.nb_records,
            skip=params.skip,
            limit=params.limit,
            page_size=len(result.blobs),
        ),
    )


@router.patch(
    "/{blob_id}",
    dependencies=[Depends(require_permission(namespace="schedules", name="create"))],
)
async def update_blob(
    blob_id: Annotated[UUID, Path()],
    session: Annotated[OrmSession, Depends(gen_dbsession)],
    request: UpdateBlobRequest,
):
    """Update a blob."""
    if not request.model_dump(exclude_unset=True):
        raise BadRequestError(
            "No changes were made to the blob because no fields being set"
        )
    blob = db_get_blob_by_id(session, blob_id=blob_id)
    if blob.schedule_id is None:
        raise RecordDoesNotExistError("Blob does not belong to any schedule.")

    db_create_or_update_blob(
        session,
        schedule_id=blob.schedule_id,
        request=CreateBlobSchema(
            flag_name=blob.flag_name,
            kind=blob.kind,
            checksum=blob.checksum,
            comments=request.comments,
            url=blob.url,
        ),
    )
    return db_get_blob(
        session,
        schedule_id=blob.schedule_id,
        flag_name=blob.flag_name,
        checksum=blob.checksum,
    )


@router.delete(
    "/{blob_id}",
    dependencies=[Depends(require_permission(namespace="schedules", name="create"))],
)
async def delete_blob(
    blob_id: Annotated[UUID, Path()],
    session: Annotated[OrmSession, Depends(gen_dbsession)],
):
    "Delete a blob"

    if db_delete_blob(session=session, blob_id=blob_id):
        return Response(status_code=HTTPStatus.NO_CONTENT)
    raise RecordDoesNotExistError("Blob does not exist.")


@router.get(
    "/{schedule_name}/{flag_name}/{checksum}",
    dependencies=[Depends(require_permission(namespace="schedules", name="read"))],
)
async def get_blob(
    schedule_name: Annotated[NotEmptyString, Path()],
    flag_name: Annotated[NotEmptyString, Path()],
    checksum: Annotated[NotEmptyString, Path()],
    session: Annotated[OrmSession, Depends(gen_dbsession)],
) -> BlobSchema:
    schedule = get_schedule(session, schedule_name=schedule_name)
    return db_get_blob(
        session, schedule_id=schedule.id, flag_name=flag_name, checksum=checksum
    )
