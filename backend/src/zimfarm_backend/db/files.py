import datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.db.models import File, Task


class CmsPendingFile(BaseModel):
    filename: str
    task_id: UUID
    created_timestamp: datetime.datetime | None


class CmsPendingFileListResult(BaseModel):
    nb_records: int
    files: list[CmsPendingFile]


def get_files_to_notify(
    session: OrmSession,
    limit: int = 20,
    *,
    retry_interval: float | None = None,
) -> CmsPendingFileListResult:
    """Get the list of files that need CMS notifications."""
    stmt = (
        select(
            func.count(File.id).over().label("nb_records"),
            File.name.label("filename"),
            Task.id.label("task_id"),
            File.created_timestamp.label("created_timestamp"),
        )
        .join(Task, Task.id == File.task_id)
        .where(
            # We should send notifications for files that meet the following criteria:
            # - have not been successfully notified
            # - have  check_result or check_filename
            # - are not older than retry_interval (if set) since check_timestamp
            #   so we don't discard notifying CMS about a file because the zimcheck
            #   results were not uploaded due to another issue.
            or_(File.cms_notified.is_(None), File.cms_notified.is_(False)),
            or_(File.check_result.is_not(None), File.check_filename.is_not(None)),
            (
                func.extract(
                    "epoch",
                    func.now()
                    - func.coalesce(File.check_timestamp, File.created_timestamp),
                )
                < (0.0 if retry_interval is None else retry_interval)
            )
            # if no retry_interval is set, this LHS of the OR evaluates to True
            | (retry_interval is None),
        )
        .order_by(File.created_timestamp)
        .limit(limit)
    )

    results = CmsPendingFileListResult(nb_records=0, files=[])
    for nb_records, filename, task_id, created_timestamp in session.execute(stmt).all():
        # Because the SQL window function returns the total_records
        # for every row, assign that value to the nb_records
        results.nb_records = nb_records
        results.files.append(
            CmsPendingFile(
                filename=filename,
                task_id=task_id,
                created_timestamp=created_timestamp,
            )
        )
    return results
