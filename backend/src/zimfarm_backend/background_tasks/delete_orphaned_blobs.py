from sqlalchemy import delete
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.background_tasks import logger
from zimfarm_backend.db.models import Blob


def delete_orphaned_blobs(session: OrmSession):
    """
    Delete orphaned blobs from the blob storage.

    A blob is considered orphaned when its recipe_id is NULL.
    This function:
    1. Finds all blobs with recipe_id = NULL
    2. Deletes the blobs from the database.
    """
    logger.info(":: checking for orphaned blobs (recipe_id is NULL)")

    nb_deleted_from_db = session.execute(
        delete(Blob).where(Blob.recipe_id.is_(None))
    ).rowcount

    logger.info(f"::: deleted {nb_deleted_from_db} orphaned blobs from database.")
