import base64
import io
import pathlib
from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.api.image import convert_image_to_png, create_zim_illustration
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
    get_extension_from_kind,
    prepare_blob,
)
from zimfarm_backend.common.schemas.orms import BlobSchema, CreateBlobSchema
from zimfarm_backend.db.blob import create_or_update_blob as db_create_or_update_blob
from zimfarm_backend.db.blob import delete_blob as db_delete_blob
from zimfarm_backend.db.blob import get_blob as db_get_blob
from zimfarm_backend.db.blob import get_blob_by_id
from zimfarm_backend.db.blob import get_blob_by_id as db_get_blob_by_id
from zimfarm_backend.db.blob import get_blob_or_none as db_get_blob_or_none
from zimfarm_backend.db.blob import get_blobs as db_get_blobs
from zimfarm_backend.db.exceptions import RecordDoesNotExistError
from zimfarm_backend.db.recipe import get_recipe

router = APIRouter(prefix="/blobs", tags=["blobs"])


@router.post(
    "/{recipe_name}",
    dependencies=[Depends(require_permission(namespace="recipes", name="create"))],
)
def create_blob(
    recipe_name: Annotated[NotEmptyString, Path()],
    request: CreateBlobRequest,
    session: Annotated[OrmSession, Depends(gen_dbsession)],
) -> BlobSchema:
    "Create a blob for recipe"

    recipe = get_recipe(session, recipe_name=recipe_name)

    if request.data.startswith("data:"):
        _, encoded_data = request.data.split(",", 1)
    else:
        encoded_data = request.data
    value = base64.b64decode(encoded_data)

    if request.kind == "image":
        blob_data = convert_image_to_png(value)
    elif request.kind == "illustration":
        blob_data = create_zim_illustration(value)
    else:
        blob_data = value

    prepared_blob = prepare_blob(
        blob_data=blob_data, flag_name=request.flag_name, kind=request.kind
    )

    if existing_blob := db_get_blob_or_none(
        session,
        recipe_id=recipe.id,
        flag_name=request.flag_name,
        checksum=prepared_blob.checksum,
    ):
        return existing_blob

    db_create_or_update_blob(
        session,
        recipe_id=recipe.id,
        request=CreateBlobSchema(
            flag_name=request.flag_name,
            kind=request.kind,
            checksum=prepared_blob.checksum,
            comments=request.comments,
            content=prepared_blob.data,
        ),
    )
    return db_get_blob(
        session,
        recipe_id=recipe.id,
        flag_name=request.flag_name,
        checksum=prepared_blob.checksum,
    )


@router.get(
    "/{recipe_name}",
    dependencies=[Depends(require_permission(namespace="recipes", name="read"))],
)
def get_blobs(
    recipe_name: Annotated[NotEmptyString, Path()],
    session: Annotated[OrmSession, Depends(gen_dbsession)],
    params: Annotated[BlobsGetSchema, Query()],
):
    """Get a list of all available blobs for recipe"""
    result = db_get_blobs(
        session,
        skip=params.skip,
        limit=params.limit,
        recipe_name=recipe_name,
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
    dependencies=[Depends(require_permission(namespace="recipes", name="create"))],
)
def update_blob(
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
    if blob.recipe_id is None:
        raise RecordDoesNotExistError("Blob does not belong to any recipe.")

    if blob.content is None:
        raise RecordDoesNotExistError("Blob does not have any data.")

    db_create_or_update_blob(
        session,
        recipe_id=blob.recipe_id,
        request=CreateBlobSchema(
            flag_name=blob.flag_name,
            kind=blob.kind,
            checksum=blob.checksum,
            comments=request.comments,
            content=blob.content,
        ),
    )

    return db_get_blob(
        session,
        recipe_id=blob.recipe_id,
        flag_name=blob.flag_name,
        checksum=blob.checksum,
    )


@router.delete(
    "/{blob_id}",
    dependencies=[Depends(require_permission(namespace="recipes", name="create"))],
)
def delete_blob(
    blob_id: Annotated[UUID, Path()],
    session: Annotated[OrmSession, Depends(gen_dbsession)],
):
    "Delete a blob"

    if db_delete_blob(session=session, blob_id=blob_id):
        return Response(status_code=HTTPStatus.NO_CONTENT)
    raise RecordDoesNotExistError("Blob does not exist.")


@router.get(
    "/{recipe_name}/{flag_name}/{checksum}",
    dependencies=[Depends(require_permission(namespace="recipes", name="read"))],
)
def get_blob(
    recipe_name: Annotated[NotEmptyString, Path()],
    flag_name: Annotated[NotEmptyString, Path()],
    checksum: Annotated[NotEmptyString, Path()],
    session: Annotated[OrmSession, Depends(gen_dbsession)],
) -> BlobSchema:
    recipe = get_recipe(session, recipe_name=recipe_name)
    return db_get_blob(
        session, recipe_id=recipe.id, flag_name=flag_name, checksum=checksum
    )


@router.get("/download/{filename}")
def download_blob(
    filename: Annotated[pathlib.Path, Path()],
    session: Annotated[OrmSession, Depends(gen_dbsession)],
):
    try:
        blob_id, ext = UUID(filename.stem), filename.suffix
    except ValueError as exc:
        raise RecordDoesNotExistError("Blob does not exist.") from exc

    blob = get_blob_by_id(session, blob_id=blob_id)
    if get_extension_from_kind(blob.kind) != ext or blob.content is None:
        raise RecordDoesNotExistError("Blob does not exist")
    byte_stream = io.BytesIO(blob.content)
    return StreamingResponse(
        content=byte_stream,
    )
