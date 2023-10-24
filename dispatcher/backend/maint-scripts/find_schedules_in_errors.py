#!/usr/bin/env python3

""" Find all schedules which are enabled and have at least the last two tasks which
    failed in a row
    
    ./find_schedules_in_errors"""

import sqlalchemy as sa
import sqlalchemy.orm as so

import db.models as dbm
from db import dbsession


@dbsession
def find_schedules_in_errors(session: so.Session):
    print(f"looking after schedules with bad status")

    stmt = (
        sa.select(dbm.Schedule).where(dbm.Schedule.enabled).order_by(dbm.Schedule.name)
    )

    schedules = list(session.execute(stmt).scalars())
    print(f"{len(schedules)} schedules found")

    for schedule in schedules:
        all_tasks = sorted(schedule.tasks, key=lambda t: t.updated_at, reverse=True)

        nb_failed = len(list(filter(lambda t: t.status == "failed", all_tasks)))
        nb_success = len(list(filter(lambda t: t.status == "succeeded", all_tasks)))
        total = len(all_tasks)

        if nb_success == 0:
            print(
                f"Never succeeded: schedule {schedule.name} (periodicity={schedule.periodicity}) never succeeded out of {total} attempts"
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
                    f"Many failures in a row: schedule {schedule.name} (periodicity={schedule.periodicity}) failed {nb_failures_in_a_row} times in a row, nb_success: {nb_success}, nb_failed: {nb_failed}, total: {total}"
                )
                continue

    return


if __name__ == "__main__":
    find_schedules_in_errors()
    print("FINISH!")
