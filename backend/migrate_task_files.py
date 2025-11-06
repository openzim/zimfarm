from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend import logger
from zimfarm_backend.common.schemas.orms import TaskFileSchema
from zimfarm_backend.db import Session
from zimfarm_backend.db.models import File, Task


def migrate_task_files(session: OrmSession):
    for task_id in session.scalars(select(Task.id)):
        # Fetch the tasks incrementally as the entries are too big and have
        # huge data content
        task = session.scalars(select(Task).where(Task.id == task_id)).one()
        if not task.files:
            continue
        for filename, file_data in task.files.items():
            try:
                # Parse the file data using the schema to ensure it's valid
                file_schema = TaskFileSchema.model_validate(file_data)
            except Exception:
                logger.error(
                    f"Failed to parse file data for task {task_id} and file {filename}"
                )
                continue

            # Extract CMS data if present
            cms_status_code = None
            cms_succeeded = None
            cms_on = None
            cms_book_id = None
            cms_title_ident = None
            cms_notified = None

            if file_schema.cms:
                cms_status_code = file_schema.cms.status_code
                cms_succeeded = file_schema.cms.succeeded
                cms_on = file_schema.cms.on
                cms_book_id = file_schema.cms.book_id
                cms_title_ident = file_schema.cms.title_ident

            # Create File entry
            file_entry = File(
                name=filename,
                status=file_schema.status,
                size=file_schema.size,
                # CMS fields
                cms_status_code=cms_status_code,
                cms_succeeded=cms_succeeded,
                cms_on=cms_on,
                cms_book_id=cms_book_id,
                cms_title_ident=cms_title_ident,
                cms_notified=cms_notified,
                # Timestamp fields
                created_timestamp=file_schema.created_timestamp,
                uploaded_timestamp=file_schema.uploaded_timestamp,
                failed_timestamp=file_schema.failed_timestamp,
                check_timestamp=file_schema.check_timestamp,
                # Check fields
                check_result=file_schema.check_result,
                check_log=file_schema.check_log,
                check_details=file_schema.check_details,
                info=file_schema.info,
            )
            file_entry.task = task
            session.add(file_entry)
            logger.info(f"Created file entry for {filename} from task {task.id}")


if __name__ == "__main__":
    with Session.begin() as session:
        migrate_task_files(session)
