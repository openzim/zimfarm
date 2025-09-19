from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common.schemas.fields import LimitFieldMax200, SkipField
from zimfarm_backend.common.schemas.models import (
    calculate_pagination_metadata,
)
from zimfarm_backend.common.schemas.offliners.builder import build_offliner_model
from zimfarm_backend.common.schemas.offliners.serializer import schema_to_flags
from zimfarm_backend.db.offliner import get_all_offliners
from zimfarm_backend.db.offliner import get_offliner as db_get_offliner
from zimfarm_backend.db.offliner_definition import get_offliner_definition
from zimfarm_backend.db.offliner_definition import (
    get_offliner_versions as db_get_offliner_versions,
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


@router.get("/{offliner_id}")
async def get_initial_offliner_version(
    offliner_id: Annotated[str, Path()],
    session: Annotated[OrmSession, Depends(gen_dbsession)],
) -> JSONResponse:
    """Get a specific offliner"""

    # find the schema class that matches the offliner
    offliner = db_get_offliner(session, offliner_id)
    offliner_definition = get_offliner_definition(
        session, offliner_id=offliner_id, version="initial"
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


@router.get("/{offliner_id}/versions")
async def get_offliner_versions(
    offliner_id: Annotated[str, Path()],
    session: Annotated[OrmSession, Depends(gen_dbsession)],
    skip: Annotated[SkipField, Query()] = 0,
    limit: Annotated[LimitFieldMax200, Query()] = 20,
) -> ListResponse[str]:
    """Get a list of versions for a specific offliner"""
    offliner_versions = db_get_offliner_versions(
        session, offliner_id, skip=skip, limit=limit
    )
    return ListResponse(
        meta=calculate_pagination_metadata(
            nb_records=offliner_versions.nb_records,
            skip=skip,
            limit=limit,
            page_size=len(offliner_versions.versions),
        ),
        items=offliner_versions.versions,
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
