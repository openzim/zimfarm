from collections.abc import Sequence
from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, Response
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.api.routes.dependencies import (
    gen_dbsession,
    get_current_account,
    get_editable_team_ids,
    require_permission,
)
from zimfarm_backend.api.routes.models import ListResponse
from zimfarm_backend.api.routes.teams.models import RevertTeamSchema, TeamsGetSchema
from zimfarm_backend.common.schemas.fields import (
    LimitFieldMax200,
    NotEmptyString,
    SkipField,
)
from zimfarm_backend.common.schemas.models import (
    TeamCreateSchema,
    TeamUpdateSchema,
    calculate_pagination_metadata,
)
from zimfarm_backend.common.schemas.orms import (
    TeamFullSchema,
    TeamHistorySchema,
    TeamLightSchema,
)
from zimfarm_backend.db import team as db_team
from zimfarm_backend.db.models import Account

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("")
def get_teams(
    params: Annotated[TeamsGetSchema, Query()],
    session: Annotated[OrmSession, Depends(gen_dbsession)],
    accessible_team_ids: Annotated[
        Sequence[UUID] | None, Depends(get_editable_team_ids)
    ],
) -> ListResponse[TeamLightSchema]:
    """Get a list of teams the current account can access"""
    results = db_team.get_teams(
        session,
        skip=params.skip,
        limit=params.limit,
        name=params.name,
        is_private=params.is_private,
        accessible_team_ids=accessible_team_ids,
    )
    return ListResponse(
        meta=calculate_pagination_metadata(
            nb_records=results.nb_records,
            skip=params.skip,
            limit=params.limit,
            page_size=len(results.records),
        ),
        items=results.records,
    )


@router.post(
    "", dependencies=[Depends(require_permission(namespace="teams", name="create"))]
)
def create_team(
    request: TeamCreateSchema,
    session: Annotated[OrmSession, Depends(gen_dbsession)],
    current_account: Annotated[Account, Depends(get_current_account)],
) -> TeamFullSchema:
    """Create a new team"""
    team = db_team.create_team(
        session,
        author_id=current_account.id,
        payload=request,
    )
    return db_team.create_team_full_schema(team)


@router.get("/{team_identifier}")
def get_team(
    team_identifier: Annotated[NotEmptyString, Path()],
    session: Annotated[OrmSession, Depends(gen_dbsession)],
    accessible_team_ids: Annotated[
        Sequence[UUID] | None, Depends(get_editable_team_ids)
    ],
) -> TeamFullSchema:
    """Get a team by name or ID"""
    team = db_team.get_team(
        session,
        team_identifier=team_identifier,
        accessible_team_ids=accessible_team_ids,
    )
    return db_team.create_team_full_schema(team)


@router.patch(
    "/{team_identifier}",
    dependencies=[Depends(require_permission(namespace="teams", name="update"))],
)
def update_team(
    team_identifier: Annotated[NotEmptyString, Path()],
    request: TeamUpdateSchema,
    session: Annotated[OrmSession, Depends(gen_dbsession)],
    current_account: Annotated[Account, Depends(get_current_account)],
    accessible_team_ids: Annotated[
        Sequence[UUID] | None, Depends(get_editable_team_ids)
    ],
) -> Response:
    """Update a team"""
    db_team.update_team(
        session,
        team_identifier=team_identifier,
        author_id=current_account.id,
        request=request,
        accessible_team_ids=accessible_team_ids,
    )
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.get("/{team_identifier}/history")
def get_team_history(
    team_identifier: Annotated[NotEmptyString, Path()],
    session: Annotated[OrmSession, Depends(gen_dbsession)],
    accessible_team_ids: Annotated[
        Sequence[UUID] | None, Depends(get_editable_team_ids)
    ],
    skip: Annotated[SkipField, Query()] = 0,
    limit: Annotated[LimitFieldMax200, Query()] = 200,
) -> ListResponse[TeamHistorySchema]:
    """Get a team's history"""
    results = db_team.get_team_history(
        session,
        team_id=team_identifier,
        accessible_team_ids=accessible_team_ids,
        skip=skip,
        limit=limit,
    )
    return ListResponse(
        items=results.records,
        meta=calculate_pagination_metadata(
            nb_records=results.nb_records,
            skip=skip,
            limit=limit,
            page_size=len(results.records),
        ),
    )


@router.get("/{team_identifier}/history/{history_id}")
def get_team_history_entry(
    team_identifier: Annotated[NotEmptyString, Path()],
    history_id: Annotated[UUID, Path()],
    session: Annotated[OrmSession, Depends(gen_dbsession)],
    accessible_team_ids: Annotated[
        Sequence[UUID] | None, Depends(get_editable_team_ids)
    ],
) -> TeamHistorySchema:
    """Get a single entry of a team's history"""
    history_entry = db_team.get_team_history_entry(
        session,
        team_id=team_identifier,
        history_id=history_id,
        accessible_team_ids=accessible_team_ids,
    )
    return db_team.create_team_history_schema(history_entry)


@router.patch(
    "/{team_identifier}/revert/{history_id}",
    dependencies=[Depends(require_permission(namespace="teams", name="update"))],
)
def revert_team(
    team_identifier: Annotated[NotEmptyString, Path()],
    history_id: Annotated[UUID, Path()],
    request: RevertTeamSchema,
    session: Annotated[OrmSession, Depends(gen_dbsession)],
    current_account: Annotated[Account, Depends(get_current_account)],
    accessible_team_ids: Annotated[
        Sequence[UUID] | None, Depends(get_editable_team_ids)
    ],
) -> TeamFullSchema:
    """Revert a team to a previous history entry"""
    team = db_team.revert_team(
        session,
        team_identifier=team_identifier,
        history_id=history_id,
        author_id=current_account.id,
        accessible_team_ids=accessible_team_ids,
        comment=request.comment,
    )
    return db_team.create_team_full_schema(team)
