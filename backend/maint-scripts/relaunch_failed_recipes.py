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
import sqlalchemy.orm as so

import db.models as dbm
from db import dbsession
from utils.scheduling import request_a_schedule


@dbsession
def relaunch_failed_recipes(session: so.Session, start_date: str):
    print("Loading tasks that have failed since start_date")

    start_datetime = datetime.datetime.fromisoformat(start_date)
    stmt = (
        sa.select(dbm.Task)
        .where(dbm.Task.updated_at > start_datetime)
        .where(
            dbm.Task.timestamp["reserved"]["$date"].astext.cast(sa.BigInteger)
            > start_datetime.timestamp()
        )
        .where(dbm.Task.status == "failed")
        .order_by(dbm.Task.updated_at.desc())
    )

    tasks = list(session.execute(stmt).scalars())
    print(f"{len(tasks)} tasks found")

    for task in tasks:
        scraper_duration = (
            task.timestamp["scraper_completed"] - task.timestamp["scraper_started"]
        ).total_seconds()
        if scraper_duration > 60:
            print(
                f"Ignoring schedule {task.schedule.name}, duration was "
                f"{scraper_duration}"
            )
            continue

        all_tasks = sorted(
            task.schedule.tasks, key=lambda t: t.updated_at, reverse=True
        )

        nb_failed = len(list(filter(lambda t: t.status == "failed", all_tasks)))
        nb_success = len(list(filter(lambda t: t.status == "succeeded", all_tasks)))
        total = len(all_tasks)

        if nb_success == 0:
            print(
                f"Ignoring schedule {task.schedule.name}, never succeeded out of "
                f"{total} attempts"
            )
            continue

        if nb_failed > 1:
            nb_failures_in_a_row = 0
            for task in all_tasks:
                if task.status != "failed":
                    break
                nb_failures_in_a_row += 1

        if nb_failures_in_a_row > 1:
            print(
                f"Ignoring schedule {task.schedule.name}, too many failures in a row,"
                f" failed: {nb_failed}, failure_in_a_row: {nb_failures_in_a_row},"
                f" nb_success: {nb_success}, total: {total}"
            )
            continue

        print(
            f"Requesting schedule {task.schedule.name} failed: {nb_failed}, "
            f"failure_in_a_row: {nb_failures_in_a_row}, nb_success: {nb_success},"
            f" total: {total}"
        )

        # Uncomment below to really request the schedule
        request_a_schedule(
            session=session, schedule_name=task.schedule.name, requested_by="benoit"
        )

    return


if __name__ == "__main__":
    # change value below
    relaunch_failed_recipes(start_date="2023-10-19 17:40:00")
    print("FINISH!")
