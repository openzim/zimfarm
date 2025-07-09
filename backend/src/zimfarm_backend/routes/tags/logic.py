from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common.schemas.fields import LimitFieldMax200, SkipField
from zimfarm_backend.common.schemas.models import calculate_pagination_metadata
from zimfarm_backend.db.tags import get_tags as db_get_tags
from zimfarm_backend.routes.dependencies import gen_dbsession
from zimfarm_backend.routes.models import ListResponse

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("")
async def get_tags(
    session: OrmSession = Depends(gen_dbsession),
    skip: Annotated[SkipField, Query()] = 0,
    limit: Annotated[LimitFieldMax200, Query()] = 200,
):
    """Get a list of schedule tags"""
    result = db_get_tags(session, skip, limit)
    return ListResponse(
        items=result.tags,
        meta=calculate_pagination_metadata(
            nb_records=result.nb_records,
            skip=skip,
            limit=limit,
            page_size=len(result.tags),
        ),
    )
