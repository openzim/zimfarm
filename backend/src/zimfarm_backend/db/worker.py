import ipaddress
from ipaddress import IPv4Address, IPv6Address
from typing import Any
from uuid import UUID

from sqlalchemy import asc, func, select
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


def _deserialize_worker_context(
    worker_contexts: dict[str, Any],
) -> dict[str, IPv4Address | IPv6Address | None]:
    return {
        context: ipaddress.ip_address(ip_address) if ip_address else None
        for context, ip_address in worker_contexts.items()
    }


def _serialize_worker_context(
    worker_contexts: dict[str, IPv4Address | IPv6Address | None],
) -> dict[str, Any]:
    return {
        context: str(ip_address) if ip_address else None
        for context, ip_address in worker_contexts.items()
    }


def create_worker_schema(
    worker: Worker, *, show_secrets: bool = True
) -> WorkerLightSchema:
    return WorkerLightSchema(
        show_secrets=show_secrets,
        last_ip=worker.last_ip,
        last_seen=worker.last_seen,
        selfish=worker.selfish,
        name=worker.name,
        offliners=worker.offliners,
        resources=ConfigResourcesSchema(
            cpu=worker.cpu,
            disk=worker.disk,
            memory=worker.memory,
        ),
        username=worker.user.username,
        contexts=_deserialize_worker_context(worker.contexts),
        cordoned=worker.cordoned,
        admin_disabled=worker.admin_disabled,
    )


def update_worker(
    session: OrmSession,
    *,
    worker_name: str,
    ip_address: str | None = None,
    contexts: dict[str, IPv4Address | IPv6Address | None] | None = None,
    update_last_seen: bool = True,
    admin_disabled: bool | None = None,
) -> Worker:
    """Update the last seen time and IP address for a worker."""
    worker = get_worker(session, worker_name=worker_name)
    if update_last_seen:
        worker.last_seen = getnow()
    if ip_address is not None:
        worker.last_ip = IPv4Address(ip_address)
    if contexts is not None:
        worker.contexts = _serialize_worker_context(contexts)
    if admin_disabled is not None:
        worker.admin_disabled = admin_disabled
    session.add(worker)
    session.flush()
    return worker


def get_workers(
    session: OrmSession,
    *,
    skip: int,
    limit: int,
    hide_offlines: bool = False,
    show_secrets: bool = True,
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
        .order_by(asc(Worker.name))
        .offset(skip)
        .limit(limit)
    )
    results = WorkersListResult(nb_records=0, workers=[])
    for nb_records, worker in session.execute(stmt).all():
        results.nb_records = nb_records
        results.workers.append(create_worker_schema(worker, show_secrets=show_secrets))
    return results


def get_worker_metrics(
    session: OrmSession, *, worker_name: str, show_secrets: bool = True
) -> WorkerMetricsSchema:
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
        last_ip=worker.last_ip,
        selfish=worker.selfish,
        last_seen=worker.last_seen,
        username=worker.user.username,
        resources=ConfigResourcesSchema(
            cpu=worker.cpu,
            disk=worker.disk,
            memory=worker.memory,
        ),
        offliners=worker.offliners,
        contexts=_deserialize_worker_context(worker.contexts),
        running_tasks=get_currently_running_tasks(session, worker),
        nb_tasks_total=nb_total or 0,
        nb_tasks_completed=nb_completed or 0,
        nb_tasks_succeeded=nb_succeeded or 0,
        nb_tasks_failed=nb_failed or 0,
        cordoned=worker.cordoned,
        admin_disabled=worker.admin_disabled,
        show_secrets=show_secrets,
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
    cordoned: bool,
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
        cordoned=cordoned,
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
            Worker.cordoned: stmt.excluded.cordoned,
            Worker.last_seen: stmt.excluded.last_seen,
        },
    )
    session.execute(stmt)
