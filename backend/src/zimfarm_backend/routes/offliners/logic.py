from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common.schemas.models import (
    calculate_pagination_metadata,
)
from zimfarm_backend.common.schemas.offliners.builder import build_offliner_model
from zimfarm_backend.common.schemas.offliners.serializer import schema_to_flags
from zimfarm_backend.db.offliner import get_all_offliners
from zimfarm_backend.db.offliner import get_offliner as db_get_offliner
from zimfarm_backend.db.offliner_definition import get_offliner_definition
from zimfarm_backend.db.offliner_definition import (
    get_offliner_definition_by_id as db_get_offliner_definition_by_id,
)
from zimfarm_backend.routes.dependencies import gen_dbsession
from zimfarm_backend.routes.models import ListResponse

router = APIRouter(prefix="/offliners", tags=["offliners"])


@router.get("")
async def get_offliners(
    session: Annotated[OrmSession, Depends(gen_dbsession)],
) -> ListResponse[str]:
    """Get a list of offliners"""
    offliners = get_all_offliners(session)
    return ListResponse(
        meta=calculate_pagination_metadata(
            nb_records=len(offliners),
            skip=0,
            limit=len(offliners),
            page_size=len(offliners),
        ),
        items=[offliner.id for offliner in offliners],
    )


@router.get("/definition/{definition_id}")
async def get_offliner_definition_by_id(
    definition_id: Annotated[UUID, Path()],
    session: Annotated[OrmSession, Depends(gen_dbsession)],
) -> JSONResponse:
    """Get a specific offliner using it's definition"""

    # find the schema class that matches the offliner
    offliner_definition = db_get_offliner_definition_by_id(session, definition_id)
    offliner = db_get_offliner(session, offliner_definition.offliner)
    schema_cls = build_offliner_model(offliner, offliner_definition.schema_)

    flags = schema_to_flags(schema_cls)

    return JSONResponse(
        content={
            "flags": [flag.model_dump(mode="json", by_alias=True) for flag in flags],
            "help": (  # dynamic + sourced from backend because it might be custom
                f"https://github.com/openzim/{offliner}/wiki/Frequently-Asked-Questions"
            ),
        }
    )


@router.get("/{offliner_id}/{version}")
async def get_offliner(
    offliner_id: Annotated[str, Path()],
    version: Annotated[str, Path()],
    session: Annotated[OrmSession, Depends(gen_dbsession)],
) -> JSONResponse:
    """Get a specific offliner"""

    # find the schema class that matches the offliner
    offliner = db_get_offliner(session, offliner_id)
    offliner_definition = get_offliner_definition(
        session, offliner_id=offliner_id, version=version
    )
    schema_cls = build_offliner_model(offliner, offliner_definition.schema_)

    flags = schema_to_flags(schema_cls)

    return JSONResponse(
        content={
            "flags": [flag.model_dump(mode="json", by_alias=True) for flag in flags],
            "help": (  # dynamic + sourced from backend because it might be custom
                f"https://github.com/openzim/{offliner}/wiki/Frequently-Asked-Questions"
            ),
        }
    )
