from typing import cast

import sqlalchemy as sa
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.background_tasks import logger
from zimfarm_backend.common.constants import INFORM_CMS
from zimfarm_backend.common.external import advertise_book_to_cms
from zimfarm_backend.db.models import File, Task
from zimfarm_backend.db.tasks import get_task_by_id


def retry_cms_notifications(session: OrmSession):
    """Retry CMS notifications for files that failed or were never notified.

    This task finds all checked files that have not been successfully notified to CMS.
    """
    logger.info(":: checking for files needing CMS notification retry")

    # Skip if CMS notifications are disabled
    if not INFORM_CMS:
        logger.info("::: CMS notifications are disabled (INFORM_CMS=false)")
        return

    files_to_notify = session.execute(
        sa.select(File, Task.id.label("task_id"))
        .join(Task, Task.id == File.task_id)
        .where(
            File.status == "checked",
            sa.or_(
                File.cms_notified.is_(None),
                File.cms_notified.is_(False),
            ),
        )
    ).all()

    nb_files = len(files_to_notify)
    if nb_files == 0:
        logger.info("::: no files need CMS notification retry")
        return

    logger.info(f"::: found {nb_files} file(s) needing CMS notification")

    nb_notified = 0
    nb_failed = 0

    for row in files_to_notify:
        file = cast(File, row.File)
        try:
            task_full = get_task_by_id(session, row.task_id)

            advertise_book_to_cms(session, task_full, file.name)
            nb_notified += 1

            logger.debug(f"Notified CMS for file {file.name} from task {row.task_id}")
        except Exception:
            nb_failed += 1
            logger.exception(
                f"Failed to notify CMS for file {file.name} from task {row.task_id}"
            )

    logger.info(
        f"::: CMS notification retry completed: {nb_notified} notified, "
        f"{nb_failed} failed"
    )
