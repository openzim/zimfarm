from typing import cast

import sqlalchemy as sa
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.background_tasks import logger
from zimfarm_backend.common.constants import INFORM_CMS
from zimfarm_backend.common.external import advertise_book_to_cms
from zimfarm_backend.db.models import File, Task
from zimfarm_backend.db.tasks import get_task_by_id


def notify_cms_for_checked_files(session: OrmSession):
    """Send notifications to CMS about checked files."""

    if not INFORM_CMS:
        logger.info("::: CMS notifications are disabled (INFORM_CMS=false)")
        return

    logger.info(":: checking for files needing CMS notification")

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
        logger.info("::: no files need CMS notification")
        return

    logger.info(f"::: found {nb_files} file(s) needing CMS notification")

    nb_notified = 0

    try:
        for row in files_to_notify:
            file = cast(File, row.File)
            task_full = get_task_by_id(session, row.task_id)

            advertise_book_to_cms(session, task_full, file.name)
            nb_notified += 1

            logger.debug(f"Notified CMS for file {file.name} from task {row.task_id}")
    except Exception:
        logger.exception(
            f"Failed to send CMS notification, sent {nb_notified} notifications to CMS"
        )
    else:
        logger.info(f"::: Sent {nb_notified} notifications to CMS")
