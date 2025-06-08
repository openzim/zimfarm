import datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy.orm import selectinload

from zimfarm_backend.db.exceptions import RecordDoesNotExistError
from zimfarm_backend.db.models import Sshkey


def get_ssh_key_by_fingerprint_or_none(
    session: OrmSession, *, fingerprint: str
) -> Sshkey | None:
    """Get a ssh key by fingerprint or return None if it does not exist"""
    return session.scalars(
        select(Sshkey)
        .options(selectinload(Sshkey.user))
        .where(Sshkey.fingerprint == fingerprint)
    ).one_or_none()


def create_ssh_key(
    session: OrmSession,
    *,
    fingerprint: str,
    user_id: UUID,
    key: str,
    pkcs8_key: str,
    name: str,
) -> Sshkey:
    """Create a new ssh key"""
    ssh_key = Sshkey(
        fingerprint=fingerprint,
        key=key,
        pkcs8_key=pkcs8_key,
        name=name,
        type="RSA",
        added=datetime.datetime.now(datetime.UTC).replace(tzinfo=None),
    )

    ssh_key.user_id = user_id
    session.add(ssh_key)
    session.flush()

    return ssh_key


def get_ssh_key_by_fingerprint(session: OrmSession, *, fingerprint: str) -> Sshkey:
    """Get a ssh key by fingerprint"""
    if ssh_key := get_ssh_key_by_fingerprint_or_none(session, fingerprint=fingerprint):
        return ssh_key
    raise RecordDoesNotExistError("SSH key not found")


def delete_ssh_key(session: OrmSession, *, fingerprint: str, user_id: UUID) -> None:
    """Delete a ssh key"""
    session.execute(
        delete(Sshkey).where(
            Sshkey.fingerprint == fingerprint, Sshkey.user_id == user_id
        )
    )
