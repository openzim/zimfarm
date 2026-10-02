from collections.abc import Sequence
from uuid import UUID

from psycopg.errors import UniqueViolation
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy.orm import selectinload

from zimfarm_backend import logger
from zimfarm_backend.common import is_valid_uuid
from zimfarm_backend.common.schemas.models import TeamCreateSchema, TeamUpdateSchema
from zimfarm_backend.common.schemas.orms import (
    ListResult,
    TeamFullSchema,
    TeamHistorySchema,
    TeamLightSchema,
)
from zimfarm_backend.db import count_from_stmt
from zimfarm_backend.db.exceptions import (
    RecordAlreadyExistsError,
    RecordDoesNotExistError,
)
from zimfarm_backend.db.models import (
    Team,
    TeamHistory,
    TeamPermission,
)


def get_team_by_id_or_none(
    session: OrmSession,
    team_id: UUID,
    accessible_team_ids: Sequence[UUID] | None = None,
) -> Team | None:
    """Get a team by ID if possible else None"""
    return session.scalars(
        select(Team)
        .where(
            Team.id == team_id,
            (Team.id.in_(accessible_team_ids or []) | (accessible_team_ids is None)),
        )
        .options(selectinload(Team.recipes))
    ).one_or_none()


def get_team_by_id(
    session: OrmSession,
    team_id: UUID,
    accessible_team_ids: Sequence[UUID] | None = None,
) -> Team:
    """Get a team by ID if possible else raise an exception"""
    if (
        team := get_team_by_id_or_none(
            session,
            team_id=team_id,
            accessible_team_ids=accessible_team_ids,
        )
    ) is None:
        raise RecordDoesNotExistError(
            f"Team with ID {team_id} does not exist or is not accessible to you"
        )
    return team


def get_team_by_name_or_none(
    session: OrmSession,
    team_name: str,
    accessible_team_ids: Sequence[UUID] | None = None,
) -> Team | None:
    """Get a team by name if possible else None"""
    return session.scalars(
        select(Team)
        .where(
            Team.name == team_name,
            Team.id.in_(accessible_team_ids or []) | (accessible_team_ids is None),
        )
        .options(selectinload(Team.recipes))
    ).one_or_none()


def get_team_by_name(
    session: OrmSession,
    team_name: str,
    accessible_team_ids: Sequence[UUID] | None = None,
) -> Team:
    """Get a team by name if possible else raise an exception"""
    if (
        team := get_team_by_name_or_none(
            session,
            team_name=team_name,
            accessible_team_ids=accessible_team_ids,
        )
    ) is None:
        raise RecordDoesNotExistError(
            f"Team '{team_name}' does not exist or is not accessible to you"
        )
    return team


def get_team_or_none(
    session: OrmSession,
    team_identifier: str,
    accessible_team_ids: Sequence[UUID] | None = None,
) -> Team | None:
    """Get a team by it's name or ID if possible else None"""
    if is_valid_uuid(team_identifier):
        team = get_team_by_id_or_none(
            session, UUID(team_identifier), accessible_team_ids
        )
    else:
        team = get_team_by_name_or_none(session, team_identifier, accessible_team_ids)
    return team


def get_team(
    session: OrmSession,
    team_identifier: str,
    accessible_team_ids: Sequence[UUID] | None = None,
) -> Team:
    team = get_team_or_none(session, team_identifier, accessible_team_ids)
    if team is None:
        raise RecordDoesNotExistError(
            f"Team '{team_identifier}' does not exist or is not accessible to you"
        )
    return team


def get_teams(
    session: OrmSession,
    *,
    skip: int,
    limit: int,
    name: str | None = None,
    is_private: bool | None = None,
    accessible_team_ids: Sequence[UUID] | None = None,
    accessible_by: UUID | None = None,
) -> ListResult[TeamLightSchema]:
    """Get the list of teams."""
    stmt = (
        select(
            Team.name,
            Team.is_private,
        )
        .where(
            Team.id.in_(accessible_team_ids or []) | (accessible_team_ids is None),
            # If a client provides an argument i.e it is not None,
            # we compare the corresponding model field against the argument,
            # otherwise, we compare the argument to its default which translates
            # to a SQL true i.e we don't filter based on this argument (a no-op).
            (Team.name.ilike(f"%{name if name is not None else ''}%") | (name is None)),
            Team.is_private.is_(bool(is_private)) | (is_private is None),
        )
        .order_by(Team.name.desc())
    )
    if accessible_by is not None:
        stmt = stmt.join(TeamPermission, TeamPermission.team_id == Team.id).where(
            TeamPermission.account_id == accessible_by
        )

    return ListResult[TeamLightSchema](
        nb_records=count_from_stmt(session, stmt),
        records=[
            TeamLightSchema(
                name=team_name,
                is_private=is_private,
            )
            for (
                team_name,
                is_private,
            ) in session.execute(stmt.offset(skip).limit(limit)).all()
        ],
    )


def get_team_names(
    session: OrmSession,
    team_ids: Sequence[UUID],
) -> list[str]:
    """Get the names of the teams with the provided IDs."""
    return list(session.scalars(select(Team.name).where(Team.id.in_(team_ids))).all())


def create_team_light_schema(team: Team) -> TeamLightSchema:
    return TeamLightSchema(
        name=team.name,
        is_private=team.is_private,
    )


def create_team_full_schema(team: Team) -> TeamFullSchema:
    return TeamFullSchema(
        id=team.id,
        name=team.name,
        is_private=team.is_private,
    )


def create_team_history_entry(
    session: OrmSession,
    team: Team,
    author_id: UUID,
    comment: str | None = None,
) -> TeamHistory:
    history_entry = TeamHistory(
        name=team.name,
        comment=comment,
        is_private=team.is_private,
    )
    history_entry.team = team
    history_entry.author_id = author_id
    session.add(history_entry)
    return history_entry


def create_team(
    session: OrmSession,
    *,
    author_id: UUID,
    payload: TeamCreateSchema,
) -> Team:
    team = Team(
        name=payload.name,
        is_private=payload.is_private,
    )
    session.add(team)
    try:
        session.flush()
    except IntegrityError as exc:
        if isinstance(exc.orig, UniqueViolation):
            raise RecordAlreadyExistsError(
                f"Team with name {payload.name} already exists"
            ) from exc
        logger.exception("Unknown exception encountered while creating collection")
        raise

    create_team_history_entry(
        session, team, author_id, comment="Create initial history"
    )

    return team


def update_team(
    session: OrmSession,
    *,
    team_identifier: str,
    author_id: UUID,
    request: TeamUpdateSchema,
    accessible_team_ids: Sequence[UUID] | None = None,
) -> Team:
    """Update a team"""
    team = get_team(session, team_identifier, accessible_team_ids)

    values = request.model_dump(exclude_unset=True, exclude={"comment"}, mode="json")
    if not values:
        return team

    try:
        team = session.scalars(
            update(Team).values(**values).where(Team.id == team.id).returning(Team)
        ).one()
    except IntegrityError as exc:
        if isinstance(exc.orig, UniqueViolation):
            raise RecordAlreadyExistsError(
                f"Team with name {request.name} already exists"
            ) from exc
        logger.exception("Unknown exception encountered while creating collection")
        raise

    create_team_history_entry(session, team, author_id, request.comment)
    return team


def revert_team(
    session: OrmSession,
    *,
    team_identifier: str,
    history_id: UUID,
    author_id: UUID,
    accessible_team_ids: Sequence[UUID] | None = None,
    comment: str | None = None,
) -> Team:
    """Revert a team's name and visibility to those defined in history_id"""
    team = get_team(session, team_identifier, accessible_team_ids)
    history_entry = get_team_history_entry(
        session,
        team_id=team_identifier,
        history_id=history_id,
        accessible_team_ids=accessible_team_ids,
    )

    # Copy over the attributes from the history entry to the team as both db
    # models share the same relevant fields.
    team.name = history_entry.name
    team.is_private = history_entry.is_private
    session.add(team)

    create_team_history_entry(session, team, author_id, comment)

    try:
        session.flush()
    except IntegrityError as exc:
        if isinstance(exc.orig, UniqueViolation):
            raise RecordAlreadyExistsError(
                f"Team with name {team.name} already exists"
            ) from exc
        logger.exception("Unknown exception encountered while reverting team")
        raise
    session.refresh(team)

    return team


def create_team_history_schema(
    entry: TeamHistory,
) -> TeamHistorySchema:
    return TeamHistorySchema(
        id=entry.id,
        created_at=entry.created_at,
        comment=entry.comment,
        name=entry.name,
        author=entry.author.display_name,
        is_private=entry.is_private,
    )


def get_team_history(
    session: OrmSession,
    *,
    team_id: str,
    skip: int,
    limit: int,
    accessible_team_ids: Sequence[UUID] | None = None,
) -> ListResult[TeamHistorySchema]:
    """Get a team's history"""
    team = get_team(session, team_id, accessible_team_ids)
    stmt = (
        select(TeamHistory)
        .where(TeamHistory.team_id == team.id)
        .options(selectinload(TeamHistory.author))
        .order_by(TeamHistory.created_at.desc())
    )
    return ListResult[TeamHistorySchema](
        nb_records=count_from_stmt(session, stmt),
        records=[
            create_team_history_schema(entry)
            for entry in session.scalars(stmt.offset(skip).limit(limit)).all()
        ],
    )


def get_team_history_entry_or_none(
    session: OrmSession,
    *,
    team_id: str,
    history_id: UUID,
    accessible_team_ids: Sequence[UUID] | None = None,
) -> TeamHistory | None:
    """Get a team's history entry or None if it does not exist"""
    team = get_team(session, team_id, accessible_team_ids)
    return session.scalars(
        select(TeamHistory).where(
            TeamHistory.id == history_id,
            TeamHistory.team_id == team.id,
        )
    ).one_or_none()


def get_team_history_entry(
    session: OrmSession,
    *,
    team_id: str,
    history_id: UUID,
    accessible_team_ids: Sequence[UUID] | None = None,
) -> TeamHistory:
    """Get a book's history entry"""
    if history_entry := get_team_history_entry_or_none(
        session,
        team_id=team_id,
        history_id=history_id,
        accessible_team_ids=accessible_team_ids,
    ):
        return history_entry
    raise RecordDoesNotExistError(
        f"Team '{team_id}' does not have a history entry with id {history_id}"
    )
