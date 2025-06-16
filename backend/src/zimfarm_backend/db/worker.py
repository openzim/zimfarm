import datetime
from ipaddress import IPv4Address
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common import getnow
from zimfarm_backend.common.enums import Offliner
from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.models import PlatformsLimitSchema
from zimfarm_backend.common.schemas.orms import ConfigResourcesSchema, WorkerLightSchema
from zimfarm_backend.db.exceptions import RecordDoesNotExistError
from zimfarm_backend.db.models import User, Worker


class ActiveWorkersListResult(BaseModel):
    nb_records: int
    workers: list[WorkerLightSchema]


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


def get_active_workers(
    session: OrmSession, *, skip: int, limit: int
) -> ActiveWorkersListResult:
    """Get a list of active workers."""
    stmt = (
        select(
            func.count().over().label("nb_records"),
            Worker,
        )
        .join(User)
        .where(
            User.deleted.is_(False),
            Worker.deleted.is_(False),
        )
        .order_by(Worker.name)
        .offset(skip)
        .limit(limit)
    )
    results = ActiveWorkersListResult(nb_records=0, workers=[])
    for nb_records, worker in session.execute(stmt).all():
        results.nb_records = nb_records
        results.workers.append(
            WorkerLightSchema(
                last_seen=worker.last_seen,
                name=worker.name,
                offliners=worker.offliners,
                last_ip=worker.last_ip,
                resources=ConfigResourcesSchema(
                    cpu=worker.cpu,
                    disk=worker.disk,
                    memory=worker.memory,
                ),
                username=worker.user.username,
            )
        )
    return results


def check_in_worker(
    session: OrmSession,
    *,
    worker_name: str,
    cpu: int,
    memory: int,
    disk: int,
    selfish: bool,
    offliners: list[Offliner],
    platforms: PlatformsLimitSchema | None = None,
    user_id: UUID,
) -> None:
    """Check in a worker."""
    stmt = insert(Worker).values(
        name=worker_name,
        selfish=selfish,
        cpu=cpu,
        memory=memory,
        disk=disk,
        offliners=offliners,
        platforms=platforms.model_dump(mode="json") if platforms else {},
        last_ip=None,
        last_seen=getnow(),
        user_id=user_id,
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=[Worker.name],
        set_={
            Worker.selfish: stmt.excluded.selfish,
            Worker.cpu: stmt.excluded.cpu,
            Worker.memory: stmt.excluded.memory,
            Worker.disk: stmt.excluded.disk,
            Worker.offliners: stmt.excluded.offliners,
            Worker.platforms: stmt.excluded.platforms,
            Worker.last_seen: stmt.excluded.last_seen,
        },
    )
    session.execute(stmt)
