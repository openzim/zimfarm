import datetime
from ipaddress import IPv4Address

from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.db.exceptions import RecordDoesNotExistError
from zimfarm_backend.db.models import Worker


def get_worker_or_none(session: OrmSession, *, worker_name: str) -> Worker | None:
    """Get a worker for the given worker name if possible else None"""
    return session.scalars(
        select(Worker).where(Worker.name == worker_name)
    ).one_or_none()


def get_worker(session: OrmSession, *, worker_name: str) -> Worker:
    """Get a worker for the given worker name.

    Raise an exception if the worker does not exist.
    """
    if (worker := get_worker_or_none(session, worker_name=worker_name)) is None:
        raise RecordDoesNotExistError(f"Worker with name {worker_name} does not exist")
    return worker


def update_worker(
    session: OrmSession,
    *,
    worker_name: str,
    ip_address: str | None = None,
) -> Worker:
    """Update the last seen time and IP address for a worker."""
    worker = get_worker(session, worker_name=worker_name)
    worker.last_seen = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
    if ip_address is not None:
        worker.last_ip = IPv4Address(ip_address)
    session.add(worker)
    session.flush()
    return worker
