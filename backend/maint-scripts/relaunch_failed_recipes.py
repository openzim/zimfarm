#!/usr/bin/env python3

"""Relaunch schedules which have failed recently

Relaunch schedules which have failed since start_date and have not
failed more than 1 time in a row.

Typically used when a bug occured in production at start_date and all
recipes which are not known to be failing should be tried again.

./relaunch_failed_recipes.py
"""

import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend import logger
from zimfarm_backend.db import Session
from zimfarm_backend.db.models import Task
from zimfarm_backend.db.requested_task import request_task
from zimfarm_backend.utils.task import get_timestamp_for_status


def relaunch_failed_recipes(session: OrmSession, start_date: str):
    logger.info("Loading tasks that have failed since start_date")

    start_datetime = datetime.datetime.fromisoformat(start_date)
    stmt = (
        sa.select(Task)
        .where(Task.updated_at > start_datetime)
        .where(
            Task.timestamp["reserved"]["$date"].astext.cast(sa.BigInteger)
            > start_datetime.timestamp()
        )
        .where(Task.status == "failed")
        .order_by(Task.updated_at.desc())
    )

    tasks = list(session.execute(stmt).scalars())
    logger.info(f"{len(tasks)} tasks found")

    max_scraper_duration = 60
    for task in tasks:
        schedule_name = task.schedule.name if task.schedule else "unknown"
        scraper_duration = (
            get_timestamp_for_status(task.timestamp, "scraper_completed")
            - get_timestamp_for_status(task.timestamp, "scraper_started")
        ).total_seconds()
        if scraper_duration > max_scraper_duration:
            logger.info(
                f"Ignoring schedule {schedule_name}, duration was {scraper_duration}"
            )
            continue

        all_tasks = sorted(
            task.schedule.tasks if task.schedule else [],
            key=lambda t: t.updated_at,
            reverse=True,
        )

        nb_failed = len(list(filter(lambda t: t.status == "failed", all_tasks)))
        nb_success = len(list(filter(lambda t: t.status == "succeeded", all_tasks)))
        total = len(all_tasks)

        if nb_success == 0:
            logger.info(
                f"Ignoring schedule {schedule_name}, never succeeded out of "
                f"{total} attempts"
            )
            continue

        nb_failures_in_a_row = 0
        if nb_failed > 1:
            for _task in all_tasks:
                if _task.status != "failed":
                    break
                nb_failures_in_a_row += 1

        if nb_failures_in_a_row > 1:
            logger.info(
                f"Ignoring schedule {schedule_name}, too many failures in a row,"
                f" failed: {nb_failed}, failure_in_a_row: {nb_failures_in_a_row},"
                f" nb_success: {nb_success}, total: {total}"
            )
            continue

        logger.info(
            f"Requesting schedule {schedule_name} failed: {nb_failed}, "
            f"failure_in_a_row: {nb_failures_in_a_row}, nb_success: {nb_success},"
            f" total: {total}"
        )

        request_task(
            session=session, schedule_name=schedule_name, requested_by="benoit"
        )


if __name__ == "__main__":
    # change value below
    with Session.begin() as session:
        relaunch_failed_recipes(session=session, start_date="2023-10-19 17:40:00")
    logger.info("FINISH!")
