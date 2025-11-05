from sqlalchemy import func, select
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.background_tasks import logger
from zimfarm_backend.background_tasks.constants import HISTORY_TASK_PER_SCHEDULE
from zimfarm_backend.db.models import Schedule, Task


def history_cleanup(session: OrmSession):
    """removes tasks for which the schedule has been run multiple times.

    Uses HISTORY_TASK_PER_SCHEDULE
    """

    logger.info(f":: removing tasks history (>{HISTORY_TASK_PER_SCHEDULE})")

    schedule_ids_stmt = (
        select(Task.schedule_id)
        .group_by(Task.schedule_id)
        .having(func.count(Task.id) > HISTORY_TASK_PER_SCHEDULE)
    )

    schedules_with_too_much_tasks = session.execute(
        select(Schedule).where(Schedule.id.in_(schedule_ids_stmt))
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
