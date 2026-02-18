from fastapi import APIRouter

from zimfarm_backend.api.routes.models import ListResponse
from zimfarm_backend.common.enums import Platform
from zimfarm_backend.common.schemas.models import calculate_pagination_metadata

router = APIRouter(prefix="/platforms", tags=["platforms"])


@router.get("")
def get_platforms():
    """Get a list of supported platforms."""
    platforms = Platform.all()
    return ListResponse[Platform](
        meta=calculate_pagination_metadata(
            nb_records=len(platforms), skip=0, limit=100, page_size=len(platforms)
        ),
        items=platforms,
    )
