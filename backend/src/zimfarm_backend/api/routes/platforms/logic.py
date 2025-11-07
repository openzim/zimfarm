from fastapi import APIRouter

from zimfarm_backend.api.routes.models import ListResponse
from zimfarm_backend.common.enums import Platform
from zimfarm_backend.common.schemas.models import Paginator

router = APIRouter(prefix="/platforms", tags=["platforms"])


@router.get("")
async def get_platforms():
    """Get a list of supported platforms."""
    platforms = Platform.all()
    return ListResponse[Platform](
        meta=Paginator(
            skip=0, limit=100, nb_records=len(platforms), page_size=len(platforms)
        ),
        items=platforms,
    )
