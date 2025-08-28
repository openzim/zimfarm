from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common.schemas.fields import LimitFieldMax500, SkipField
from zimfarm_backend.common.schemas.models import calculate_pagination_metadata
from zimfarm_backend.db.contexts import get_contexts as db_get_contexts
from zimfarm_backend.routes.dependencies import gen_dbsession
from zimfarm_backend.routes.models import ListResponse

router = APIRouter(prefix="/contexts", tags=["contexts"])


@router.get("")
async def get_contexts(
    session: OrmSession = Depends(gen_dbsession),
    skip: Annotated[SkipField, Query()] = 0,
    limit: Annotated[LimitFieldMax500, Query()] = 500,
):
    """Get a list of all available contexts from schedules and workers"""
    result = db_get_contexts(session, skip, limit)
    return ListResponse(
        items=result.contexts,
        meta=calculate_pagination_metadata(
            nb_records=result.nb_records,
            skip=skip,
            limit=limit,
            page_size=len(result.contexts),
        ),
    )
