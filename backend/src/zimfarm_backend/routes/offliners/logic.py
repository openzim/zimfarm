from typing import Annotated, get_args

from fastapi import APIRouter, Path
from fastapi.responses import JSONResponse

from zimfarm_backend.common.enums import Offliner
from zimfarm_backend.common.schemas.models import (
    OfflinerSchema,
    calculate_pagination_metadata,
)
from zimfarm_backend.common.schemas.offliners.serializer import schema_to_flags
from zimfarm_backend.routes.http_errors import NotFoundError
from zimfarm_backend.routes.models import ListResponse

router = APIRouter(prefix="/offliners", tags=["offliners"])


@router.get("")
async def get_offliners():
    """Get a list of offliners"""
    offliners = Offliner.all()
    return ListResponse(
        meta=calculate_pagination_metadata(
            nb_records=len(offliners),
            skip=0,
            limit=100,
            page_size=len(offliners),
        ),
        items=offliners,
    )


@router.get("/{offliner}")
async def get_offliner(offliner: Annotated[Offliner, Path()]) -> JSONResponse:
    """Get a specific offliner"""

    # find the schema class that matches the offliner
    schema_cls = next(
        (
            schema_cls
            for schema_cls in get_args(OfflinerSchema)
            if get_args(schema_cls.model_fields["offliner_id"].annotation)[0]
            == offliner
        ),
        None,
    )
    if schema_cls is None:
        raise NotFoundError(f"Offliner {offliner} not found")

    definition = schema_to_flags(schema_cls)

    return JSONResponse(
        content={
            "flags": definition["flags"],
            "help": (  # dynamic + sourced from backend because it might be custom
                f"https://github.com/openzim/{offliner}/wiki/Frequently-Asked-Questions"
            ),
        }
    )
