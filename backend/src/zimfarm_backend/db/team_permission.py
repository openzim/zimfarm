from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common.roles import RoleEnum, is_global_role, is_team_role
from zimfarm_backend.db.models import Account, Team, TeamPermission


def _get_public_team_ids(session: OrmSession):
    return session.scalars(select(Team.id).where(Team.is_private.is_(False))).all()


def _get_member_team_ids(session: OrmSession, account: Account):
    return session.scalars(
        select(Team.id)
        .join(
            TeamPermission,
            TeamPermission.team_id == Team.id,
        )
        .where(TeamPermission.account_id == account.id)
    ).all()


def _get_team_ids(
    session: OrmSession, account: Account | None, *, viewable: bool
) -> Sequence[UUID] | None:
    """Resolve the team IDs an account is scoped to.

    Returns None when the account is not scoped to any team (global roles),
    """
    if account is None or RoleEnum(account.role) == RoleEnum.PUBLIC_VIEWER:
        return _get_public_team_ids(session)

    role = RoleEnum(account.role)
    if is_global_role(role):
        return None

    if is_team_role(role):
        member_ids = _get_member_team_ids(session, account)
        if not viewable:
            return member_ids
        return list({*_get_public_team_ids(session), *member_ids})

    return _get_public_team_ids(session)


def get_editable_team_ids(
    session: OrmSession, account: Account | None
) -> Sequence[UUID] | None:
    """Get the team IDs account is allowed to operate on."""
    return _get_team_ids(session, account, viewable=False)


def get_viewable_team_ids(
    session: OrmSession, account: Account | None
) -> Sequence[UUID] | None:
    """Get the team IDs account is allowed to view resources of."""
    return _get_team_ids(session, account, viewable=True)


def create_team_permission(session: OrmSession, team_id: UUID, account_id: UUID):
    """Create a team permission for the current account on the team"""
    permission = TeamPermission(team_id=team_id, account_id=account_id)
    session.add(permission)
    session.flush()


def delete_team_permissions(session: OrmSession, account_id: UUID):
    """Delete all team permissions for account"""
    session.execute(
        delete(TeamPermission).where(TeamPermission.account_id == account_id)
    )
