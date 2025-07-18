from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common.schemas.fields import LimitFieldMax500, SkipField
from zimfarm_backend.common.schemas.models import (
    LanguageSchema,
    calculate_pagination_metadata,
)
from zimfarm_backend.db import gen_dbsession
from zimfarm_backend.db.language import get_languages as db_get_languages
from zimfarm_backend.routes.models import ListResponse

router = APIRouter(prefix="/languages", tags=["languages"])


@router.get("")
def get_languages(
    db_session: Annotated[OrmSession, Depends(gen_dbsession)],
    skip: Annotated[SkipField, Query()] = 0,
    limit: Annotated[LimitFieldMax500, Query()] = 20,
) -> ListResponse[LanguageSchema]:
    """Get a list of languages."""

    results = db_get_languages(db_session, skip=skip, limit=limit)
    return ListResponse[LanguageSchema](
        meta=calculate_pagination_metadata(
            nb_records=results.nb_languages,
            skip=skip,
            limit=limit,
            page_size=len(results.languages),
        ),
        items=results.languages,
    )
