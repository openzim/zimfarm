#!/usr/bin/env python3
# vim: ai ts=4 sts=4 et sw=4 nu

import datetime
import logging

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONPATH
from sqlalchemy.orm import Session as OrmSession

import zimfarm_backend.db.models as dbm
from zimfarm_backend.common import getnow
from zimfarm_backend.common.constants import getenv
from zimfarm_backend.common.enums import TaskStatus
from zimfarm_backend.common.utils import task_cancel_requested_event_handler
from zimfarm_backend.db import Session

# constants
ONE_MN = 60
ONE_HOUR = 60 * ONE_MN
NAME = "periodic-tasks"

# config
HISTORY_TASK_PER_SCHEDULE = 10
STALLED_GONE_TIMEOUT = ONE_HOUR
# when launching worker, it sets status to `started` then start scraper and
# change status to `scraper_started` so it's a minutes max duration
STALLED_STARTED_TIMEOUT = 30 * ONE_MN
# reserving a task is the lock that happens just before starting a worker
# thus changing its status to `started` quickly afterwards
STALLED_RESERVED_TIMEOUT = 30 * ONE_MN
# only uploads happens after scraper_completed
STALLED_COMPLETED_TIMEOUT = 24 * ONE_HOUR
# cancel_request are picked-up during polls and may take a few minutes
# to be effective and reported
STALLED_CANCELREQ_TIMEOUT = 30 * ONE_MN
# tasks older than this are removed
OLD_TASK_DELETION_THRESHOLD = datetime.timedelta(
    days=int(getenv("TASKS_OLDER_THAN", default=10))
)
# flag to determine whether to remove old tasks
OLD_TASK_DELETION_ENABLED = (
    getenv("SHOULD_REMOVE_OLD_TASKS", default="false").lower() == "true"
)


logger = logging.getLogger(NAME)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("[%(name)s - %(asctime)s: %(levelname)s] %(message)s")
)
logger.addHandler(handler)


def history_cleanup(session: OrmSession):
    """removes tasks for which the schedule has been run multiple times after

    Uses HISTORY_TASK_PER_SCHEDULE"""

    logger.info(f":: removing tasks history (>{HISTORY_TASK_PER_SCHEDULE})")

    schedule_ids_stmt = (
        sa.select(dbm.Task.schedule_id)
        .group_by(dbm.Task.schedule_id)
        .having(sa.func.count(dbm.Task.id) > HISTORY_TASK_PER_SCHEDULE)
    )

    schedules_with_too_much_tasks = session.execute(
        sa.select(dbm.Schedule).filter(dbm.Schedule.id.in_(schedule_ids_stmt))
    ).scalars()

    nb_deleted_tasks = 0
    for schedule in schedules_with_too_much_tasks:
        nb_tasks_kept = 0
        for task in sorted(schedule.tasks, key=lambda x: x.updated_at, reverse=True):
            if nb_tasks_kept < HISTORY_TASK_PER_SCHEDULE:
                nb_tasks_kept += 1
                continue
            session.delete(task)
            nb_deleted_tasks += 1
    logger.info(f"::: deleted {nb_deleted_tasks} tasks")


def status_to_cancel(
    now: datetime.datetime, status: TaskStatus, timeout: int, session: OrmSession
):
    logger.info(f":: canceling tasks `{status}` for more than {timeout}s")
    ago = now - datetime.timedelta(seconds=timeout)
    tasks = session.execute(
        sa.select(dbm.Task).where(
            dbm.Task.status == status,
            sa.func.to_timestamp(
                sa.func.cast(
                    sa.func.jsonb_path_query_first(
                        dbm.Task.timestamp,
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

    nb_canceled_tasks = 0
    for task in tasks:
        task.status = TaskStatus.canceled
        task.canceled_by = NAME
        task.timestamp.append((TaskStatus.canceled, now))
        task.events.append(
            {
                "code": TaskStatus.canceled,
                "timestamp": now,
            }
        )
        task.updated_at = now
        nb_canceled_tasks += 1

    logger.info(f"::: canceled {nb_canceled_tasks} tasks")


def cancel_incomplete_tasks(session: OrmSession, now: datetime.datetime):
    """Cancel incomplete tasks that have not been updated recently"""
    logger.info(
        f":: checking for incomplete tasks (no update for {STALLED_GONE_TIMEOUT}s)"
    )
    ago = now - datetime.timedelta(seconds=STALLED_GONE_TIMEOUT)

    tasks = session.execute(
        sa.select(dbm.Task)
        .join(dbm.Worker, dbm.Worker.id == dbm.Task.worker_id)
        .where(
            dbm.Task.status.not_in(
                [
                    *TaskStatus.complete(),
                    TaskStatus.scraper_completed,
                    TaskStatus.cancel_requested,
                ]
            ),
            dbm.Task.updated_at <= ago,
            dbm.Worker.last_seen > ago,
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


def staled_statuses(session: OrmSession):
    """set the status for tasks in an unfinished state"""

    now = getnow()

    # `started` statuses
    status_to_cancel(now, TaskStatus.started, STALLED_STARTED_TIMEOUT, session)

    # `reserved` statuses
    status_to_cancel(now, TaskStatus.reserved, STALLED_RESERVED_TIMEOUT, session)

    # `cancel_requested` statuses
    status_to_cancel(
        now, TaskStatus.cancel_requested, STALLED_CANCELREQ_TIMEOUT, session
    )

    # `scraper_completed` statuses: either success or failure
    status = TaskStatus.scraper_completed
    logger.info(
        f":: closing tasks `{status}` for more than {STALLED_COMPLETED_TIMEOUT}s"
    )
    ago = now - datetime.timedelta(seconds=STALLED_COMPLETED_TIMEOUT)
    tasks = session.execute(
        sa.select(dbm.Task).where(
            dbm.Task.status == status,
            sa.func.to_timestamp(
                sa.cast(
                    sa.func.jsonb_path_query_first(
                        dbm.Task.timestamp,
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
    logger.info(f"::: succeeded {nb_suceeded_tasks} tasks")
    logger.info(f"::: failed {nb_failed_tasks} tasks")


def tasks_cleanup(session: OrmSession):
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
        sa.delete(dbm.Task).where(
            sa.and_(
                dbm.Task.updated_at < threshold,
            )
        )
    )

    logger.info(f"::: deleted {result.rowcount} tasks.")


def main(session: OrmSession):
    logger.info("running periodic tasks-cleaner")

    history_cleanup(session)

    cancel_incomplete_tasks(session, getnow())

    staled_statuses(session)

    tasks_cleanup(session)


if __name__ == "__main__":
    with Session.begin() as session:
        main(session)
