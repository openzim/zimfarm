from ipaddress import IPv4Address
from uuid import UUID

from sqlalchemy import asc, desc, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common import getnow
from zimfarm_backend.common.constants import WORKER_OFFLINE_DELAY_DURATION
from zimfarm_backend.common.enums import TaskStatus
from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.orms import (
    ConfigResourcesSchema,
    WorkerLightSchema,
    WorkerMetricsSchema,
)
from zimfarm_backend.db.exceptions import RecordDoesNotExistError
from zimfarm_backend.db.models import Task, User, Worker
from zimfarm_backend.db.tasks import get_currently_running_tasks


class WorkersListResult(BaseModel):
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


def create_worker_schema(worker: Worker) -> WorkerLightSchema:
    return WorkerLightSchema(
        last_seen=worker.last_seen,
        name=worker.name,
        offliners=worker.offliners,
        resources=ConfigResourcesSchema(
            cpu=worker.cpu,
            disk=worker.disk,
            memory=worker.memory,
        ),
        username=worker.user.username,
        contexts=worker.contexts,
    )


def update_worker(
    session: OrmSession,
    *,
    worker_name: str,
    ip_address: str | None = None,
    contexts: list[str] | None = None,
    update_last_seen: bool = True,
) -> Worker:
    """Update the last seen time and IP address for a worker."""
    worker = get_worker(session, worker_name=worker_name)
    if update_last_seen:
        worker.last_seen = getnow()
    if ip_address is not None:
        worker.last_ip = IPv4Address(ip_address)
    if contexts is not None:
        worker.contexts = contexts
    session.add(worker)
    session.flush()
    return worker


def get_workers(
    session: OrmSession, *, skip: int, limit: int, hide_offlines: bool = False
) -> WorkersListResult:
    """Get a list of workers."""
    stmt = (
        select(
            func.count().over().label("nb_records"),
            Worker,
        )
        .join(User)
        .where(
            User.deleted.is_(False),
            Worker.deleted.is_(False),
            # if hide_offlines is False, then, the second condition will always
            # translate to a SQL true and include all workers
            (
                func.extract("epoch", func.now() - Worker.last_seen)
                < WORKER_OFFLINE_DELAY_DURATION
            )
            | (hide_offlines is False),
        )
        .order_by(desc(Worker.last_seen), asc(Worker.name))
        .offset(skip)
        .limit(limit)
    )
    results = WorkersListResult(nb_records=0, workers=[])
    for nb_records, worker in session.execute(stmt).all():
        results.nb_records = nb_records
        results.workers.append(create_worker_schema(worker))
    return results


def get_worker_metrics(session: OrmSession, *, worker_name: str) -> WorkerMetricsSchema:
    """Get a worker with full details and metrics."""
    worker = get_worker(session, worker_name=worker_name)

    # SQL-level metrics for this worker's tasks
    metrics_stmt = select(
        func.count(Task.id).label("nb_total"),
        func.count(Task.id)
        .filter(Task.status.in_(TaskStatus.complete()))
        .label("nb_completed"),
        func.count(Task.id)
        .filter(Task.status == TaskStatus.succeeded)
        .label("nb_succeeded"),
        func.count(Task.id).filter(Task.status == TaskStatus.failed).label("nb_failed"),
    ).where(Task.worker_id == worker.id)
    nb_total, nb_completed, nb_succeeded, nb_failed = session.execute(
        metrics_stmt
    ).one()

    return WorkerMetricsSchema(
        name=worker.name,
        last_seen=worker.last_seen,
        username=worker.user.username,
        resources=ConfigResourcesSchema(
            cpu=worker.cpu,
            disk=worker.disk,
            memory=worker.memory,
        ),
        offliners=worker.offliners,
        contexts=worker.contexts,
        running_tasks=get_currently_running_tasks(session, worker),
        nb_tasks_total=nb_total or 0,
        nb_tasks_completed=nb_completed or 0,
        nb_tasks_succeeded=nb_succeeded or 0,
        nb_tasks_failed=nb_failed or 0,
    )


def check_in_worker(
    session: OrmSession,
    *,
    worker_name: str,
    cpu: int,
    memory: int,
    disk: int,
    selfish: bool,
    offliners: list[str],
    platforms: dict[str, int] | None = None,
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
        platforms=platforms if platforms is not None else {},
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
