from unittest.mock import Mock, patch

from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.background_tasks.delete_orphaned_blobs import (
    delete_blob_from_storage,
    delete_orphaned_blobs,
)
from zimfarm_backend.db import count_from_stmt
from zimfarm_backend.db.models import Blob, Schedule


def test_delete_blob_from_storage_success():
    """Test successfully deleting a blob from storage"""
    blob_url = "https://storage.example.com/blob123.css"

    with patch(
        "zimfarm_backend.background_tasks.delete_orphaned_blobs.requests"
    ) as mock_requests:
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_requests.delete.return_value = mock_response

        result = delete_blob_from_storage(blob_url)

        assert result is True
        mock_requests.delete.assert_called_once()


def test_delete_blob_from_storage_failure():
    """Test handling failure when deleting blob from storage"""
    blob_url = "https://storage.example.com/blob123.css"

    with patch(
        "zimfarm_backend.background_tasks.delete_orphaned_blobs.requests"
    ) as mock_requests:
        mock_requests.delete.side_effect = Exception("Network error")

        result = delete_blob_from_storage(blob_url)

        assert result is False


def test_delete_orphaned_blobs_no_orphans(
    dbsession: OrmSession,
    schedule: Schedule,
):
    """Test delete_orphaned_blobs when there are no orphaned blobs"""
    schedule.blobs.append(
        Blob(
            kind="css",
            flag_name="custom-css",
            url="https://storage.example.com/style1.css",
            checksum="1",
        )
    )
    schedule.blobs.append(
        Blob(
            kind="js",
            flag_name="custom-js",
            url="https://storage.example.com/script1.js",
            checksum="2",
        )
    )
    dbsession.add(schedule)
    dbsession.flush()

    with patch(
        "zimfarm_backend.background_tasks.delete_orphaned_blobs.delete_blob_from_storage"
    ) as mock_delete_storage:
        delete_orphaned_blobs(dbsession)

        # No blobs should be deleted
        mock_delete_storage.assert_not_called()
        assert count_from_stmt(dbsession, select(Blob.id)) == 2


def test_delete_orphaned_blobs_deletes_orphans(
    dbsession: OrmSession,
    schedule: Schedule,
):
    """Test delete_orphaned_blobs successfully deletes orphaned blobs"""
    orphaned_blob1 = Blob(
        kind="css",
        flag_name="custom-css",
        url="https://storage.example.com/orphan1.css",
        checksum="1",
    )
    orphaned_blob2 = Blob(
        kind="js",
        flag_name="custom-js",
        url="https://storage.example.com/orphan2.js",
        checksum="2",
    )
    dbsession.add_all([orphaned_blob1, orphaned_blob2])
    dbsession.flush()

    # Create a non-orphaned blob
    schedule.blobs.append(
        Blob(
            kind="css",
            flag_name="active-css",
            url="https://storage.example.com/active.css",
            checksum="3",
        )
    )
    dbsession.add(schedule)
    dbsession.flush()

    with patch(
        "zimfarm_backend.background_tasks.delete_orphaned_blobs.delete_blob_from_storage"
    ) as mock_delete_storage:
        mock_delete_storage.return_value = True

        delete_orphaned_blobs(dbsession)

        # Should have called delete_blob_from_storage twice (for orphaned blobs)
        assert mock_delete_storage.call_count == 2

        # Only the non-orphaned blob should remain
        assert count_from_stmt(dbsession, select(Blob.id)) == 1
        remaining_blob = dbsession.execute(select(Blob)).scalar_one()
        assert remaining_blob.checksum == "3"


def test_delete_orphaned_blobs_handles_storage_deletion_failure(
    dbsession: OrmSession,
):
    """Test that blobs are not deleted from DB if storage deletion fails"""
    # Create orphaned blobs
    orphaned_blob1 = Blob(
        kind="css",
        flag_name="custom-css",
        url="https://storage.example.com/orphan1.css",
        checksum="1",
    )
    orphaned_blob2 = Blob(
        kind="js",
        flag_name="custom-js",
        url="https://storage.example.com/orphan2.js",
        checksum="2",
    )
    dbsession.add_all([orphaned_blob1, orphaned_blob2])
    dbsession.flush()

    with patch(
        "zimfarm_backend.background_tasks.delete_orphaned_blobs.delete_blob_from_storage"
    ) as mock_delete_storage:
        # Simulate storage deletion failure
        mock_delete_storage.return_value = False

        delete_orphaned_blobs(dbsession)

        # Both blobs should remain in DB since storage deletion failed
        assert count_from_stmt(dbsession, select(Blob.id)) == 2
