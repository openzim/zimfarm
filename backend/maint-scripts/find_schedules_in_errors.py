#!/usr/bin/env python3

"""Find all schedules which are enabled and have at least the last two tasks which
failed in a row

./find_schedules_in_errors"""

import sqlalchemy as sa
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend import logger
from zimfarm_backend.db import Session
from zimfarm_backend.db.models import Schedule


def find_schedules_in_errors(session: OrmSession):
    logger.info("Looking after schedules with bad status")

    stmt = sa.select(Schedule).where(Schedule.enabled).order_by(Schedule.name)

    schedules = list(session.execute(stmt).scalars())
    logger.info(f"{len(schedules)} schedules found")

    for schedule in schedules:
        all_tasks = sorted(schedule.tasks, key=lambda t: t.updated_at, reverse=True)

        nb_failed = len(list(filter(lambda t: t.status == "failed", all_tasks)))
        nb_success = len(list(filter(lambda t: t.status == "succeeded", all_tasks)))
        total = len(all_tasks)

        if nb_success == 0:
            logger.info(
                f"Never succeeded: schedule {schedule.name} (periodicity="
                f"{schedule.periodicity}) never succeeded out of {total} attempts"
            )
            continue

        if nb_failed > 1:
            nb_failures_in_a_row = 0
            for task in all_tasks:
                if task.status != "failed":
                    break
                nb_failures_in_a_row += 1

            if nb_failures_in_a_row > 1:
                logger.info(
                    f"Many failures in a row: schedule {schedule.name} (periodicity="
                    f"{schedule.periodicity}) failed {nb_failures_in_a_row} times in"
                    f" a row, nb_success: {nb_success}, nb_failed: {nb_failed},"
                    f" total: {total}"
                )
                continue


if __name__ == "__main__":
    with Session.begin() as session:
        find_schedules_in_errors(session=session)
    logger.info("FINISH!")
