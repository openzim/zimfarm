from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from zimfarm_backend.api.routes.dependencies import gen_dbsession
from zimfarm_backend.api.routes.models import ListResponse
from zimfarm_backend.common.schemas.fields import LimitFieldMax200
from zimfarm_backend.common.schemas.models import calculate_pagination_metadata
from zimfarm_backend.db.files import (
    CmsPendingFile,
    get_files_to_notify,
)

router = APIRouter(prefix="/files", tags=["files"])


@router.get("/pending-cms-notifications")
def get_cms_files_to_notify(
    db_session: Annotated[Session, Depends(gen_dbsession)],
    limit: Annotated[LimitFieldMax200, Query()] = 20,
) -> ListResponse[CmsPendingFile]:
    results = get_files_to_notify(db_session, limit)
    return ListResponse(
        meta=calculate_pagination_metadata(
            nb_records=results.nb_records,
            skip=0,
            limit=limit,
            page_size=len(results.files),
        ),
        items=results.files,
    )
