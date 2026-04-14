from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy.orm import selectinload

from zimfarm_backend.common import getnow
from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.orms import SshKeyRead
from zimfarm_backend.db.exceptions import RecordDoesNotExistError
from zimfarm_backend.db.models import Sshkey, Worker


def get_ssh_key_by_fingerprint_or_none(
    session: OrmSession, *, fingerprint: str
) -> Sshkey | None:
    """Get a ssh key by fingerprint or return None if it does not exist"""
    return session.scalars(
        select(Sshkey)
        .options(selectinload(Sshkey.worker).selectinload(Worker.account))
        .where(Sshkey.fingerprint == fingerprint)
    ).first()


class SshKeyList(BaseModel):
    nb_records: int
    ssh_keys: list[SshKeyRead]


def create_ssh_key_read_schema(ssh_key: Sshkey) -> SshKeyRead:
    return SshKeyRead(
        name=ssh_key.name,
        fingerprint=ssh_key.fingerprint,
        added=ssh_key.added,
        type=ssh_key.type,
        key=ssh_key.key,
    )


def get_ssh_keys(session: OrmSession, *, worker_id: UUID) -> SshKeyList:
    """Get list of ssh keys for worker."""
    query = (
        select(
            func.count().over().label("nb_records"),
            Sshkey,
        )
        .where(Sshkey.worker_id == worker_id)
        .order_by(Sshkey.added.desc(), Sshkey.id.asc())
    )

    results = SshKeyList(nb_records=0, ssh_keys=[])
    for nb_records, ssh_key in session.execute(query).all():
        results.nb_records = nb_records
        results.ssh_keys.append(create_ssh_key_read_schema(ssh_key))
    return results


def create_ssh_key(
    session: OrmSession,
    *,
    fingerprint: str,
    worker_id: UUID,
    key: str,
    name: str,
    type_: str,
) -> Sshkey:
    """Create a new ssh key"""
    ssh_key = Sshkey(
        fingerprint=fingerprint,
        key=key,
        name=name,
        type=type_,
        added=getnow(),
    )

    ssh_key.worker_id = worker_id
    session.add(ssh_key)
    session.flush()

    return ssh_key


def get_ssh_key_by_fingerprint(session: OrmSession, *, fingerprint: str) -> Sshkey:
    """Get a ssh key by fingerprint"""
    if ssh_key := get_ssh_key_by_fingerprint_or_none(session, fingerprint=fingerprint):
        return ssh_key
    raise RecordDoesNotExistError("SSH key not found")


def delete_ssh_key(session: OrmSession, *, fingerprint: str, worker_id: UUID) -> None:
    """Delete a ssh key"""
    session.execute(
        delete(Sshkey).where(
            Sshkey.fingerprint == fingerprint, Sshkey.worker_id == worker_id
        )
    )
