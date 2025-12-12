import requests
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.background_tasks import logger
from zimfarm_backend.common.constants import (
    BLOB_STORAGE_PASSWORD,
    BLOB_STORAGE_USERNAME,
    REQUESTS_TIMEOUT,
)
from zimfarm_backend.db.blob import delete_blob
from zimfarm_backend.db.models import Blob


def delete_blob_from_storage(blob_url: str) -> bool:
    """
    Delete a blob from the blob storage.
    """
    try:
        response = requests.delete(
            blob_url,
            auth=(BLOB_STORAGE_USERNAME, BLOB_STORAGE_PASSWORD),
            timeout=REQUESTS_TIMEOUT,
        )
        response.raise_for_status()
        logger.debug(f"Successfully deleted blob from storage: {blob_url}")
        return True
    except Exception:
        logger.exception(f"Failed to delete blob from storage {blob_url}")
        return False


def delete_orphaned_blobs(session: OrmSession):
    """
    Delete orphaned blobs from the blob storage.

    A blob is considered orphaned when its schedule_id is NULL.
    This function:
    1. Finds all blobs with schedule_id = NULL
    2. Attempts to delete them from the blob storage via HTTP DELETE
    3. Removes successfully deleted blobs from the database
    """
    logger.info(":: checking for orphaned blobs (schedule_id is NULL)")

    # Find all orphaned blobs
    orphaned_blobs = session.execute(
        select(Blob).where(Blob.schedule_id.is_(None))
    ).scalars()

    nb_deleted_from_storage = 0
    nb_deleted_from_db = 0
    nb_failed = 0

    for blob in orphaned_blobs:
        # Attempt to delete from blob storage
        if delete_blob_from_storage(blob.url):
            # Only delete from database if storage deletion succeeded
            rows_deleted = delete_blob(session, blob_id=blob.id)
            nb_deleted_from_storage += 1
            nb_deleted_from_db += rows_deleted
        else:
            nb_failed += 1

    logger.info(
        f"::: deleted {nb_deleted_from_storage} orphaned blobs from storage, "
        f"{nb_deleted_from_db} from database, {nb_failed} failed"
    )
