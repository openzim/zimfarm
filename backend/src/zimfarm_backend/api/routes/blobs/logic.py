from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.api.routes.dependencies import gen_dbsession
from zimfarm_backend.api.routes.models import ListResponse
from zimfarm_backend.common.schemas.fields import (
    LimitFieldMax200,
    NotEmptyString,
    SkipField,
)
from zimfarm_backend.common.schemas.models import calculate_pagination_metadata
from zimfarm_backend.db.blob import get_blobs as db_get_blobs

router = APIRouter(prefix="/blobs", tags=["blobs"])


@router.get("/{schedule_name}")
async def get_blobs(
    schedule_name: Annotated[NotEmptyString, Path()],
    session: OrmSession = Depends(gen_dbsession),
    skip: Annotated[SkipField, Query()] = 0,
    limit: Annotated[LimitFieldMax200, Query()] = 20,
):
    """Get a list of all available blobs for schedule"""
    result = db_get_blobs(session, skip=skip, limit=limit, schedule_name=schedule_name)
    return ListResponse(
        items=result.blobs,
        meta=calculate_pagination_metadata(
            nb_records=result.nb_records,
            skip=skip,
            limit=limit,
            page_size=len(result.blobs),
        ),
    )
