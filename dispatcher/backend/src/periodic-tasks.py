#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import logging
import datetime

import pymongo

from common import getnow
from common.mongo import Tasks
from common.enum import TaskStatus

# constants
ONE_MN = 60
ONE_HOUR = 60 * ONE_MN
NAME = "periodic-tasks"

# config
HISTORY_TASK_PER_SCHEDULE = 5
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


def history_cleanup():
    """ removes tasks for which the schedule has been run multiple times after

        Uses HISTORY_TASK_PER_SCHEDULE """

    logger.info(f":: removing tasks history (>{HISTORY_TASK_PER_SCHEDULE})")
    cursor = Tasks().aggregate(
        [
            {"$group": {"_id": "$schedule_name", "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": HISTORY_TASK_PER_SCHEDULE}}},
        ]
    )

    schedules_with_too_much_tasks = [s["_id"] for s in cursor]

    task_ids_to_delete = []
    for schedule_name in schedules_with_too_much_tasks:
        cursor = Tasks().aggregate(
            [
                {"$match": {"schedule_name": schedule_name}},
                {
                    "$project": {
                        "schedule_name": 1,
                        "updated_at": {"$arrayElemAt": ["$events.timestamp", -1]},
                    }
                },
                {"$sort": {"updated_at": pymongo.DESCENDING}},
                {"$skip": HISTORY_TASK_PER_SCHEDULE},
            ]
        )
        task_ids_to_delete += [t["_id"] for t in cursor]

    result = Tasks().delete_many({"_id": {"$in": task_ids_to_delete}})
    logger.info(f"::: deleted {result.deleted_count}/{len(task_ids_to_delete)} tasks")


def status_to_cancel(now, status, timeout):
    logger.info(f":: canceling tasks `{status}` for more than {timeout}s")
    ago = now - datetime.timedelta(seconds=timeout)
    query = {"status": status, f"timestamp.{status}": {"$lte": ago}}
    result = Tasks().update_many(
        query,
        {
            "$set": {
                "status": TaskStatus.canceled,
                "canceled_by": NAME,
                f"timestamp.{TaskStatus.canceled}": now,
            }
        },
    )
    logger.info(f"::: canceled {result.modified_count}/{result.matched_count} tasks")


def staled_statuses():
    """ set the status for tasks in an unfinished state """

    now = getnow()

    # `started` statuses
    status_to_cancel(now, TaskStatus.started, STALLED_STARTED_TIMEOUT)

    # `reserved` statuses
    status_to_cancel(now, TaskStatus.reserved, STALLED_RESERVED_TIMEOUT)

    # `cancel_requested` statuses
    status_to_cancel(now, TaskStatus.cancel_requested, STALLED_CANCELREQ_TIMEOUT)

    # `scraper_completed` statuses: either success or failure
    status = TaskStatus.scraper_completed
    logger.info(
        f":: closing tasks `{status}` for more than {STALLED_COMPLETED_TIMEOUT}s"
    )
    ago = now - datetime.timedelta(seconds=STALLED_COMPLETED_TIMEOUT)
    query = {"status": status, f"timestamp.{status}": {"$lte": ago}}
    query_success = {"container.exit_code": 0}
    query_success.update(query)
    result = Tasks().update_many(
        query_success,
        {
            "$set": {
                "status": TaskStatus.succeeded,
                f"timestamp.{TaskStatus.succeeded}": now,
            }
        },
    )
    logger.info(f"::: succeeded {result.modified_count}/{result.matched_count} tasks")
    query_failed = {"container.exit_code": {"$ne": 0}}
    query_failed.update(query)
    result = Tasks().update_many(
        query_failed,
        {"$set": {"status": TaskStatus.failed, f"timestamp.{TaskStatus.failed}": now}},
    )
    logger.info(f"::: failed {result.modified_count}/{result.matched_count} tasks")


def main():
    logger.info("running periodic tasks-cleaner")

    history_cleanup()

    staled_statuses()


if __name__ == "__main__":
    main()
