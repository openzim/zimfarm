from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session as OrmSession
from werkzeug.security import check_password_hash, generate_password_hash

from zimfarm_backend.api.routes.dependencies import gen_dbsession, get_current_user
from zimfarm_backend.api.routes.http_errors import UnauthorizedError
from zimfarm_backend.api.routes.models import ListResponse
from zimfarm_backend.api.routes.offliners.models import (
    OfflinerCreateSchema,
    OfflinerDefinitionCreateSchema,
)
from zimfarm_backend.common.schemas.fields import (
    LimitFieldMax200,
    SkipField,
)
from zimfarm_backend.common.schemas.models import (
    calculate_pagination_metadata,
)
from zimfarm_backend.common.schemas.offliners.builder import build_offliner_model
from zimfarm_backend.common.schemas.offliners.serializer import schema_to_flags
from zimfarm_backend.common.schemas.orms import OfflinerDefinitionSchema
from zimfarm_backend.db.models import User
from zimfarm_backend.db.offliner import create_offliner as db_create_offliner
from zimfarm_backend.db.offliner import get_all_offliners
from zimfarm_backend.db.offliner import get_offliner as db_get_offliner
from zimfarm_backend.db.offliner_definition import (
    create_offliner_definition as db_create_offliner_definition,
)
from zimfarm_backend.db.offliner_definition import (
    get_offliner_definition as db_get_offliner_definition,
)
from zimfarm_backend.db.offliner_definition import (
    get_offliner_versions as db_get_offliner_versions,
)
from zimfarm_backend.db.user import check_user_permission

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


@router.post("")
async def create_offliner(
    request: OfflinerCreateSchema,
    session: Annotated[OrmSession, Depends(gen_dbsession)],
    current_user: User = Depends(get_current_user),
) -> Response:
    """Create an offliner"""
    if not check_user_permission(current_user, namespace="offliners", name="create"):
        raise UnauthorizedError("You do not have permissions to create an offliner.")

    db_create_offliner(
        session,
        offliner_id=request.offliner_id,
        base_model=request.base_model,
        docker_image_name=request.docker_image_name,
        command_name=request.command_name,
        ci_secret_hash=generate_password_hash(request.ci_secret_hash),
    )

    return Response(status_code=HTTPStatus.CREATED)


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


@router.post("/{offliner_id}/versions")
async def create_offliner_version(
    offliner_id: Annotated[str, Path()],
    session: Annotated[OrmSession, Depends(gen_dbsession)],
    request: Annotated[OfflinerDefinitionCreateSchema, Body()],
) -> Response:
    """Create a new version for a specific offliner"""
    offliner = db_get_offliner(session, offliner_id)
    if offliner.ci_secret_hash is None:
        raise UnauthorizedError("CI secret is missing for offliner")

    if not check_password_hash(offliner.ci_secret_hash, request.ci_secret):
        raise UnauthorizedError(
            "You are not authorized to create a new version for this offliner"
        )

    db_create_offliner_definition(session, request.spec, offliner_id, request.version)
    return Response(status_code=HTTPStatus.CREATED)


@router.get("/{offliner_id}/{version}")
async def get_offliner(
    offliner_id: Annotated[str, Path()],
    version: Annotated[str, Path()],
    session: Annotated[OrmSession, Depends(gen_dbsession)],
) -> JSONResponse:
    """Get a specific offliner"""

    # find the schema class that matches the offliner
    offliner = db_get_offliner(session, offliner_id)
    offliner_definition = db_get_offliner_definition(
        session, offliner_id=offliner_id, version=version
    )
    schema_cls = build_offliner_model(offliner, offliner_definition.schema_)

    flags = schema_to_flags(schema_cls)

    return JSONResponse(
        content={
            "flags": [flag.model_dump(mode="json", by_alias=True) for flag in flags],
            "help": (  # dynamic + sourced from backend because it might be custom
                f"https://github.com/openzim/{offliner_id}/wiki/Frequently-Asked-Questions"
            ),
        }
    )


@router.get("/{offliner_id}/{version}/spec")
async def get_offliner_spec(
    offliner_id: Annotated[str, Path()],
    version: Annotated[str, Path()],
    session: Annotated[OrmSession, Depends(gen_dbsession)],
) -> OfflinerDefinitionSchema:
    return db_get_offliner_definition(session, offliner_id=offliner_id, version=version)
