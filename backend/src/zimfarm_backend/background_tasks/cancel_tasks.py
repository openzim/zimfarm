import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONPATH
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.background_tasks import logger
from zimfarm_backend.background_tasks.constants import (
    OLD_TASK_DELETION_ENABLED,
    OLD_TASK_DELETION_THRESHOLD,
    PERIODIC_TASK_NAME,
    STALLED_CANCELREQ_TIMEOUT,
    STALLED_COMPLETED_TIMEOUT,
    STALLED_GONE_TIMEOUT,
    STALLED_RESERVED_TIMEOUT,
    STALLED_STARTED_TIMEOUT,
)
from zimfarm_backend.common import getnow
from zimfarm_backend.common.enums import TaskStatus
from zimfarm_backend.common.utils import task_cancel_requested_event_handler
from zimfarm_backend.db.models import Task, Worker


def get_stale_tasks_with_status(
    session: OrmSession, status: TaskStatus, ago: datetime.datetime
) -> sa.ScalarResult[Task]:
    """Get tasks with a given status that have not been updated recently"""
    return session.execute(
        sa.select(Task).where(
            Task.status == status,
            sa.func.to_timestamp(
                sa.cast(
                    sa.func.jsonb_path_query_first(
                        Task.timestamp,
                        sa.cast(
                            f'strict $[*] ? (@[0] == "{status}")[1]."$date"',
                            JSONPATH,
                        ),
                    ),
                    sa.BigInteger,
                )
                / 1000
            )
            <= ago,
        )
    ).scalars()


def cancel_incomplete_tasks(session: OrmSession):
    """Cancel incomplete tasks that have not been updated recently"""
    logger.info(
        f":: checking for incomplete tasks (no update for {STALLED_GONE_TIMEOUT}s)"
    )
    now = getnow()
    ago = now - datetime.timedelta(seconds=STALLED_GONE_TIMEOUT)

    tasks = session.execute(
        sa.select(Task)
        .join(Worker, Worker.id == Task.worker_id)
        .where(
            Task.status.not_in(
                [
                    *TaskStatus.complete(),
                    TaskStatus.scraper_completed,
                    TaskStatus.cancel_requested,
                ]
            ),
            Task.updated_at <= ago,
            Worker.last_seen > ago,
        )
    ).scalars()

    nb_gone_tasks = 0
    for task in tasks:
        # Prepare payload for cancel request
        payload = {
            "canceled_by": "periodic-task-gone",
            "timestamp": now,
        }

        task_cancel_requested_event_handler(session, task.id, payload)
        nb_gone_tasks += 1

    logger.info(f"::: requested cancellation of {nb_gone_tasks} gone tasks")


def cancel_stale_tasks_with_status(
    session: OrmSession, status: TaskStatus, now: datetime.datetime, timeout: float
):
    """
    Cancel tasks that have been in status for more than a given timeout.
    """
    logger.info(f":: canceling tasks with status `{status}` for more than {timeout}s")
    ago = now - datetime.timedelta(seconds=timeout)
    tasks = get_stale_tasks_with_status(session, status, ago)

    nb_canceled_tasks = 0
    for task in tasks:
        task.status = TaskStatus.canceled
        task.canceled_by = PERIODIC_TASK_NAME
        task.timestamp.append((TaskStatus.canceled, now))
        task.events.append(
            {
                "code": TaskStatus.canceled,
                "timestamp": now,
            }
        )
        task.updated_at = now
        nb_canceled_tasks += 1
        session.add(task)
    session.flush()

    logger.info(f"::: canceled {nb_canceled_tasks} tasks")


def close_scraper_completed_tasks(session: OrmSession, now: datetime.datetime):
    """Close scraper_completed tasks that are older than STALLED_COMPLETED_TIMEOUT"""

    status = TaskStatus.scraper_completed
    logger.info(
        f":: closing tasks with `{status}` for more than {STALLED_COMPLETED_TIMEOUT}s"
    )
    now = getnow()
    ago = now - datetime.timedelta(seconds=STALLED_COMPLETED_TIMEOUT)
    tasks = get_stale_tasks_with_status(session, status, ago)
    nb_suceeded_tasks = 0
    nb_failed_tasks = 0
    for task in tasks:
        if "exit_code" in task.container and int(task.container["exit_code"]) == 0:
            task.status = TaskStatus.succeeded
            task.timestamp.append((TaskStatus.succeeded, now))
            nb_suceeded_tasks += 1
        else:
            task.status = TaskStatus.failed
            task.timestamp.append((TaskStatus.failed, now))
            nb_failed_tasks += 1
        session.add(task)
    session.flush()
    logger.info(f"::: succeeded {nb_suceeded_tasks} tasks")
    logger.info(f"::: failed {nb_failed_tasks} tasks")


def cancel_stale_tasks(session: OrmSession):
    """Cancel stale tasks"""

    # Use a nested transaction to run each cancellation so that
    # if one fails, the others can run as they are

    now = getnow()

    # `started` statuses
    with session.begin_nested():
        try:
            cancel_stale_tasks_with_status(
                session, TaskStatus.started, now, STALLED_STARTED_TIMEOUT
            )
        except Exception:
            logger.exception(
                f"Failed to cancel stale tasks with status `{TaskStatus.started}`"
            )

    # `reserved` statuses
    with session.begin_nested():
        try:
            cancel_stale_tasks_with_status(
                session, TaskStatus.reserved, now, STALLED_RESERVED_TIMEOUT
            )
        except Exception:
            logger.exception(
                f"Failed to cancel stale tasks with status `{TaskStatus.reserved}`"
            )

    # `cancel_requested` statuses
    with session.begin_nested():
        try:
            cancel_stale_tasks_with_status(
                session, TaskStatus.cancel_requested, now, STALLED_CANCELREQ_TIMEOUT
            )
        except Exception:
            logger.exception(
                "Failed to cancel stale tasks with status "
                f"`{TaskStatus.cancel_requested}`"
            )

    # `scraper_completed` statuses: either success or failure
    with session.begin_nested():
        try:
            close_scraper_completed_tasks(session, now)
        except Exception:
            logger.exception("Failed to close scraper completed tasks")


def remove_old_tasks(session: OrmSession):
    """removes old tasks excluding most recent tasks for schedules"""

    threshold = getnow() - OLD_TASK_DELETION_THRESHOLD

    if not OLD_TASK_DELETION_ENABLED:
        logger.info(
            ":: skipping deletion of tasks older than "
            f"{threshold.isoformat(timespec='seconds')}"
        )
        return

    logger.info(
        f":: deleting tasks older than {threshold.isoformat(timespec='seconds')}"
    )

    result = session.execute(
        sa.delete(Task).where(
            sa.and_(
                Task.updated_at < threshold,
            )
        )
    )

    logger.info(f"::: deleted {result.rowcount} tasks.")
