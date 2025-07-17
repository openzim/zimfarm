#!/usr/bin/env python3
# vim: ai ts=4 sts=4 et sw=4 nu

import datetime
import logging

import sqlalchemy as sa
from sqlalchemy.orm import Session as OrmSession

import zimfarm_backend.db.models as dbm
from zimfarm_backend.common import getnow
from zimfarm_backend.common.enums import TaskStatus
from zimfarm_backend.db import Session

# constants
ONE_MN = 60
ONE_HOUR = 60 * ONE_MN
NAME = "periodic-tasks"

# config
HISTORY_TASK_PER_SCHEDULE = 10
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
        sa.select(dbm.Task)
        .filter(dbm.Task.status == status)
        .filter(
            sa.func.to_timestamp(
                dbm.Task.timestamp[status]["$date"].astext.cast(sa.BigInteger) / 1000
            )
            <= ago
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
        sa.select(dbm.Task)
        .filter(dbm.Task.status == status)
        .filter(
            sa.func.to_timestamp(
                dbm.Task.timestamp[status]["$date"].astext.cast(sa.BigInteger) / 1000
            )
            <= ago
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


def main(session: OrmSession):
    logger.info("running periodic tasks-cleaner")

    history_cleanup(session)

    staled_statuses(session)


if __name__ == "__main__":
    with Session.begin() as session:
        main(session)
