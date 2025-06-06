from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common.schemas.models import calculate_pagination_metadata
from zimfarm_backend.common.schemas.parameters import SkipLimit500Schema
from zimfarm_backend.db import gen_dbsession
from zimfarm_backend.db.language import get_languages as db_get_languages
from zimfarm_backend.routes.languages.models import LanguageList

router = APIRouter(prefix="/languages", tags=["languages"])


@router.get("")
def get_languages(
    params: Annotated[SkipLimit500Schema, Query()],
    db_session: Annotated[OrmSession, Depends(gen_dbsession)],
) -> LanguageList:
    """Get a list of languages."""

    results = db_get_languages(db_session, skip=params.skip, limit=params.limit)
    return LanguageList(
        meta=calculate_pagination_metadata(
            nb_records=results.nb_languages,
            skip=params.skip,
            limit=params.limit,
            page_size=len(results.languages),
        ),
        items=results.languages,
    )
