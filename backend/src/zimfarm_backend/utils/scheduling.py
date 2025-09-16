#!/usr/bin/env python3
# vim: ai ts=4 sts=4 et sw=4 nu

import datetime
import logging

import sqlalchemy as sa
from pydantic import ValidationError
from sqlalchemy.orm import Session as OrmSession

import zimfarm_backend.db.models as dbm
from zimfarm_backend.common import getnow
from zimfarm_backend.common.constants import (
    PERIODICITIES,
)
from zimfarm_backend.common.enums import SchedulePeriodicity, TaskStatus
from zimfarm_backend.db.requested_task import request_task
from zimfarm_backend.utils.timestamp import get_timestamp_for_status

logger = logging.getLogger(__name__)


def request_tasks_using_schedule(session: OrmSession):
    """create requested_tasks based on schedule's periodicity field

    Expected to be ran periodically to compute what needs to be scheduled
    """

    requester = "period-scheduler"
    priority = 0
    worker = None

    for period, period_data in {
        p: PERIODICITIES.get(p) for p in SchedulePeriodicity.all()
    }.items():
        if not period_data:
            continue  # manually has no data

        period_start = getnow() - datetime.timedelta(days=period_data["days"])
        logger.debug(f"requesting for `{period}` schedules (before {period_start})")

        # find non-requested schedules which last run started before our period start
        for schedule in session.execute(
            sa.select(dbm.Schedule).where(
                dbm.Schedule.enabled,
                dbm.Schedule.periodicity == period,
                ~sa.exists().where(dbm.RequestedTask.schedule_id == dbm.Schedule.id),
            )
        ).scalars():
            if schedule.most_recent_task_id is not None:
                last_run = schedule.most_recent_task
                # don't bother if it started after this rolling period's start
                if (
                    last_run
                    and get_timestamp_for_status(
                        last_run.timestamp, "started", datetime.datetime(2019, 1, 1)
                    )
                    > period_start
                ):
                    continue
                # don't request a task if the most_recent_task is still running
                if last_run and last_run.status not in TaskStatus.complete():
                    logger.debug(
                        f"{schedule.name} not requested because most_recent_task "
                        f"{last_run.id} did not complete"
                    )
                    continue

                # Create a nested transaction for each task request
                with session.begin_nested():
                    try:
                        result = request_task(
                            session=session,
                            schedule_name=schedule.name,
                            requested_by=requester,
                            worker_name=worker,
                            priority=priority,
                        )
                        if result.requested_task:
                            logger.debug(f"Successfully requested {schedule.name}")

                        if result.error:
                            logger.warning(
                                "Could not request task due to the following reason: "
                                f"{result.error}"
                            )
                    except ValidationError:
                        logger.exception(
                            f"Validation error requesting {schedule.name}",
                        )
                    except Exception:
                        logger.exception(
                            f"Unexpected error requesting {schedule.name}",
                        )
