import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common import getnow
from zimfarm_backend.common.utils import handle_file_event
from zimfarm_backend.db.models import File, Task


def test_handle_file_event_created_status(dbsession: OrmSession, task: Task):
    """Test handling file event with 'created' status"""
    timestamp = getnow()
    file_size = 1024000

    file_data = {
        "name": "test_file.zim",
        "status": "created",
        "size": file_size,
    }

    handle_file_event(dbsession, task.id, file_data, timestamp)

    # Verify the file was created with correct fields
    result = dbsession.execute(
        select(File).where(File.task_id == task.id, File.name == "test_file.zim")
    ).scalar_one()

    assert result.name == "test_file.zim"
    assert result.status == "created"
    assert result.size == file_size
    assert result.created_timestamp == timestamp
    assert result.uploaded_timestamp is None
    assert result.failed_timestamp is None
    assert result.check_timestamp is None


def test_handle_file_event_uploaded_status(dbsession: OrmSession, task: Task):
    """Test handling file event with 'uploaded' status"""
    created_timestamp = getnow()
    uploaded_timestamp = created_timestamp + datetime.timedelta(seconds=30)

    # First create the file
    file_data_created = {
        "name": "upload_test.zim",
        "status": "created",
        "size": 2048000,
    }
    handle_file_event(dbsession, task.id, file_data_created, created_timestamp)

    # Then update with uploaded status
    file_data_uploaded = {
        "name": "upload_test.zim",
        "status": "uploaded",
    }
    handle_file_event(dbsession, task.id, file_data_uploaded, uploaded_timestamp)

    # Verify the file was updated
    result = dbsession.execute(
        select(File).where(File.task_id == task.id, File.name == "upload_test.zim")
    ).scalar_one()

    assert result.status == "uploaded"
    assert result.uploaded_timestamp == uploaded_timestamp
    assert result.size == 2048000  # Original size should be preserved
    assert result.created_timestamp == created_timestamp


def test_handle_file_event_failed_status(dbsession: OrmSession, task: Task):
    """Test handling file event with 'failed' status"""
    created_timestamp = getnow()
    failed_timestamp = created_timestamp + datetime.timedelta(seconds=15)

    # First create the file
    file_data_created = {
        "name": "failed_test.zim",
        "status": "created",
        "size": 512000,
    }
    handle_file_event(dbsession, task.id, file_data_created, created_timestamp)

    # Then update with failed status
    file_data_failed = {
        "name": "failed_test.zim",
        "status": "failed",
    }
    handle_file_event(dbsession, task.id, file_data_failed, failed_timestamp)

    # Verify the file was updated
    result = dbsession.execute(
        select(File).where(File.task_id == task.id, File.name == "failed_test.zim")
    ).scalar_one()

    assert result.status == "failed"
    assert result.failed_timestamp == failed_timestamp
    assert result.uploaded_timestamp is None


def test_handle_file_event_checked_status(dbsession: OrmSession, task: Task):
    """Test handling file event with 'checked' status"""
    created_timestamp = getnow()
    checked_timestamp = created_timestamp + datetime.timedelta(seconds=60)

    # First create the file
    file_data_created = {
        "name": "checked_test.zim",
        "status": "created",
        "size": 3072000,
    }
    handle_file_event(dbsession, task.id, file_data_created, created_timestamp)

    # Then update with checked status
    check_info = {"id": "test_id", "version": "1.0"}
    file_data_checked = {
        "name": "checked_test.zim",
        "status": "checked",
        "check_result": 0,
        "info": check_info,
    }
    handle_file_event(dbsession, task.id, file_data_checked, checked_timestamp)

    # Verify the file was updated
    result = dbsession.execute(
        select(File).where(File.task_id == task.id, File.name == "checked_test.zim")
    ).scalar_one()

    assert result.status == "checked"
    assert result.check_timestamp == checked_timestamp
    assert result.check_result == 0
    assert result.info == check_info


def test_handle_file_event_checked_status_with_error(dbsession: OrmSession, task: Task):
    """Test handling file event with 'checked' status when check fails"""
    timestamp = getnow()

    file_data = {
        "name": "check_error.zim",
        "status": "checked",
        "check_result": 1,
        "info": {"error": "ZIM file is corrupted"},
    }

    handle_file_event(dbsession, task.id, file_data, timestamp)
    dbsession.flush()

    # Verify the file was created with error info
    result = dbsession.execute(
        select(File).where(File.task_id == task.id, File.name == "check_error.zim")
    ).scalar_one()

    assert result.status == "checked"
    assert result.check_result == 1
    assert result.check_timestamp == timestamp
    assert result.info == {"error": "ZIM file is corrupted"}


def test_handle_file_event_check_results_uploaded_status(
    dbsession: OrmSession, task: Task
):
    """Test handling file event with 'check_results_uploaded' status"""
    created_timestamp = getnow()
    check_upload_timestamp = created_timestamp + datetime.timedelta(seconds=90)

    # First create the file
    file_data_created = {
        "name": "check_upload_test.zim",
        "status": "created",
        "size": 4096000,
    }
    handle_file_event(dbsession, task.id, file_data_created, created_timestamp)
    dbsession.flush()

    # Then update with check_results_uploaded status
    check_filename = "check_upload_test_zimcheck.json"
    file_data_uploaded = {
        "name": "check_upload_test.zim",
        "status": "check_results_uploaded",
        "check_filename": check_filename,
    }
    handle_file_event(dbsession, task.id, file_data_uploaded, check_upload_timestamp)
    dbsession.flush()

    # Verify the file was updated
    result = dbsession.execute(
        select(File).where(
            File.task_id == task.id, File.name == "check_upload_test.zim"
        )
    ).scalar_one()

    assert result.status == "check_results_uploaded"
    assert result.check_filename == check_filename
    assert result.check_upload_timestamp == check_upload_timestamp
