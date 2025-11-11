import argparse
import logging
from time import sleep

from zimfarm_backend.__about__ import __version__
from zimfarm_backend.background_tasks import logger
from zimfarm_backend.background_tasks.cancel_tasks import (
    cancel_incomplete_tasks,
    cancel_stale_tasks,
    remove_old_tasks,
)
from zimfarm_backend.background_tasks.constants import (
    BACKGROUND_TASKS_SLEEP_DURATION,
    CANCEL_INCOMPLETE_TASKS_INTERVAL,
    CANCEL_STALE_TASKS_INTERVAL,
    CMS_NOTIFICATIONS_INTERVAL,
    HISTORY_CLEANUP_INTERVAL,
    REMOVE_OLD_TASKS_INTERVAL,
    REQUEST_TASKS_INTERVAL,
)
from zimfarm_backend.background_tasks.history_cleanup import history_cleanup
from zimfarm_backend.background_tasks.request_tasks import request_tasks
from zimfarm_backend.background_tasks.send_cms_notifications import (
    notify_cms_for_checked_files,
)
from zimfarm_backend.background_tasks.task_config import TaskConfig
from zimfarm_backend.common import getnow
from zimfarm_backend.common.constants import ALEMBIC_UPGRADE_HEAD_ON_START
from zimfarm_backend.db import Session
from zimfarm_backend.utils.database import (
    check_if_schema_is_up_to_date,
    create_initial_user,
    upgrade_db_schema,
)

# Configure background tasks with their execution intervals
tasks: list[TaskConfig] = [
    TaskConfig(
        func=remove_old_tasks,
        interval=REMOVE_OLD_TASKS_INTERVAL,
    ),
    TaskConfig(
        func=cancel_incomplete_tasks,
        interval=CANCEL_INCOMPLETE_TASKS_INTERVAL,
    ),
    TaskConfig(
        func=cancel_stale_tasks,
        interval=CANCEL_STALE_TASKS_INTERVAL,
    ),
    TaskConfig(
        func=history_cleanup,
        interval=HISTORY_CLEANUP_INTERVAL,
    ),
    TaskConfig(
        func=request_tasks,
        interval=REQUEST_TASKS_INTERVAL,
    ),
    TaskConfig(
        func=notify_cms_for_checked_files,
        interval=CMS_NOTIFICATIONS_INTERVAL,
    ),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--version",
        help="Show version and exit.",
        action="version",
        version="%(prog)s: " + __version__,
    )
    parser.add_argument(
        "--verbose", "-v", help="Show verbose output.", action="store_true"
    )

    args = parser.parse_args()
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    logger.info("Starting background tasks...")
    logger.info(f"Configured {len(tasks)} tasks")

    if ALEMBIC_UPGRADE_HEAD_ON_START:
        upgrade_db_schema()
    check_if_schema_is_up_to_date()
    create_initial_user()
    while True:
        now = getnow()
        for task_config in tasks:
            if task_config.should_run(now):
                with Session.begin() as session:
                    try:
                        logger.debug(f"Executing task: {task_config.task_name}")
                        task_config.execute(session)
                    except Exception:
                        logger.exception(
                            f"Unexpected error while executing task: "
                            f"{task_config.task_name}"
                        )
        logger.debug(
            f"Background tasks sleeping for {BACKGROUND_TASKS_SLEEP_DURATION}s..."
        )
        sleep(BACKGROUND_TASKS_SLEEP_DURATION)
