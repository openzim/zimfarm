from collections.abc import Callable
from datetime import timedelta
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.background_tasks import (
    send_cms_notifications as send_cms_notifications_module,
)
from zimfarm_backend.background_tasks.send_cms_notifications import (
    notify_cms_for_checked_files,
)
from zimfarm_backend.common import getnow
from zimfarm_backend.common.schemas.models import FileCreateUpdateSchema
from zimfarm_backend.db.models import Task
from zimfarm_backend.db.tasks import create_or_update_task_file


def test_send_cms_notifications_disabled(
    dbsession: OrmSession,
    create_task: Callable[..., Task],
    monkeypatch: pytest.MonkeyPatch,
):
    """Test that send_cms_notifications task respects INFORM_CMS flag"""
    # Disable CMS notifications
    monkeypatch.setattr(send_cms_notifications_module, "INFORM_CMS", False)

    task = create_task()
    # Create a file that meets all criteria but INFORM_CMS is disabled
    create_or_update_task_file(
        dbsession,
        FileCreateUpdateSchema(
            task_id=task.id,
            name="test.zim",
            status="checked",
            check_result=1,
            check_filename="check_report.json",
            check_timestamp=getnow(),
            created_timestamp=getnow(),
            cms_notified=None,
        ),
    )
    dbsession.flush()

    with patch(
        "zimfarm_backend.background_tasks.send_cms_notifications.advertise_book_to_cms"
    ) as mock_advertise:
        notify_cms_for_checked_files(dbsession)
        mock_advertise.assert_not_called()


def test_send_cms_notifications_skip_already_notified(
    dbsession: OrmSession,
    create_task: Callable[..., Task],
    monkeypatch: pytest.MonkeyPatch,
):
    """Test that files already successfully notified are skipped"""
    monkeypatch.setattr(send_cms_notifications_module, "INFORM_CMS", True)
    task = create_task()

    # Create a file that was successfully notified
    create_or_update_task_file(
        dbsession,
        FileCreateUpdateSchema(
            task_id=task.id,
            name="already_notified.zim",
            status="checked",
            cms_notified=True,  # Already successfully notified
            check_result=1,
            check_filename="check_report.json",
            check_timestamp=getnow(),
            created_timestamp=getnow(),
            cms_on=getnow(),
        ),
    )
    dbsession.flush()

    with patch(
        "zimfarm_backend.background_tasks.send_cms_notifications.advertise_book_to_cms"
    ) as mock_advertise:
        notify_cms_for_checked_files(dbsession)
        mock_advertise.assert_not_called()


def test_send_cms_notifications_retry_failed(
    dbsession: OrmSession,
    create_task: Callable[..., Task],
    monkeypatch: pytest.MonkeyPatch,
):
    """Test that files with failed notifications are retried"""
    monkeypatch.setattr(send_cms_notifications_module, "INFORM_CMS", True)
    task = create_task()

    # Create a file that failed notification and meets all other criteria
    create_or_update_task_file(
        dbsession,
        FileCreateUpdateSchema(
            task_id=task.id,
            name="failed_notification.zim",
            status="checked",
            cms_notified=False,  # Failed notification
            cms_on=getnow(),
            check_result=1,
            check_filename="check_report.json",
            check_timestamp=getnow(),
            created_timestamp=getnow(),
        ),
    )
    dbsession.flush()

    with patch(
        "zimfarm_backend.background_tasks.send_cms_notifications.advertise_book_to_cms"
    ) as mock_advertise:
        notify_cms_for_checked_files(dbsession)
        mock_advertise.assert_called_once()


def test_send_cms_notifications_retry_never_notified(
    dbsession: OrmSession,
    create_task: Callable[..., Task],
    monkeypatch: pytest.MonkeyPatch,
):
    """Test that files never notified are attempted if they meet all criteria"""
    monkeypatch.setattr(send_cms_notifications_module, "INFORM_CMS", True)
    task = create_task()

    # Create a file that was never notified and meets all other criteria
    create_or_update_task_file(
        dbsession,
        FileCreateUpdateSchema(
            task_id=task.id,
            name="never_notified.zim",
            status="checked",
            cms_notified=None,  # Never attempted
            check_result=1,
            check_filename="check_report.json",
            check_timestamp=getnow(),
            created_timestamp=getnow(),
        ),
    )
    dbsession.flush()

    with patch(
        "zimfarm_backend.background_tasks.send_cms_notifications.advertise_book_to_cms"
    ) as mock_advertise:
        notify_cms_for_checked_files(dbsession)
        mock_advertise.assert_called_once()


def test_send_cms_notifications_with_check_result_only(
    dbsession: OrmSession,
    create_task: Callable[..., Task],
    monkeypatch: pytest.MonkeyPatch,
):
    """Test that files with only check_result (no check_filename) are notified"""
    monkeypatch.setattr(send_cms_notifications_module, "INFORM_CMS", True)
    monkeypatch.setattr(
        send_cms_notifications_module, "CMS_MAXIMUM_RETRY_INTERVAL", 24 * 60 * 60
    )
    task = create_task()

    # Create a file with check_result but no check_filename
    create_or_update_task_file(
        dbsession,
        FileCreateUpdateSchema(
            task_id=task.id,
            name="only_result.zim",
            status="checked",
            cms_notified=None,
            check_result=1,  # Has check_result
            check_filename=None,  # No check_filename
            check_timestamp=getnow() - timedelta(hours=1),  # Recent
            created_timestamp=getnow() - timedelta(hours=1),
        ),
    )
    dbsession.flush()

    with patch(
        "zimfarm_backend.background_tasks.send_cms_notifications.advertise_book_to_cms"
    ) as mock_advertise:
        notify_cms_for_checked_files(dbsession)
        mock_advertise.assert_called_once()


def test_send_cms_notifications_with_check_filename_only(
    dbsession: OrmSession,
    create_task: Callable[..., Task],
    monkeypatch: pytest.MonkeyPatch,
):
    """Test that files with only check_filename (no check_result) are notified"""
    monkeypatch.setattr(send_cms_notifications_module, "INFORM_CMS", True)
    monkeypatch.setattr(
        send_cms_notifications_module, "CMS_MAXIMUM_RETRY_INTERVAL", 24 * 60 * 60
    )
    task = create_task()

    # Create a file with check_filename but no check_result
    create_or_update_task_file(
        dbsession,
        FileCreateUpdateSchema(
            task_id=task.id,
            name="only_filename.zim",
            status="checked",
            cms_notified=None,
            check_result=None,  # No check_result
            check_timestamp=None,  # No check_timestamp
            check_filename="check_report.json",  # Has check_filename
            created_timestamp=getnow() - timedelta(hours=1),
        ),
    )
    dbsession.flush()

    with patch(
        "zimfarm_backend.background_tasks.send_cms_notifications.advertise_book_to_cms"
    ) as mock_advertise:
        notify_cms_for_checked_files(dbsession)
        mock_advertise.assert_called_once()


def test_send_cms_notifications_with_both_check_fields(
    dbsession: OrmSession,
    create_task: Callable[..., Task],
    monkeypatch: pytest.MonkeyPatch,
):
    """Test that files with both check_result and check_filename are notified"""
    monkeypatch.setattr(send_cms_notifications_module, "INFORM_CMS", True)
    monkeypatch.setattr(
        send_cms_notifications_module, "CMS_MAXIMUM_RETRY_INTERVAL", 24 * 60 * 60
    )
    task = create_task()

    # Create a file with both check fields and recent timestamp
    create_or_update_task_file(
        dbsession,
        FileCreateUpdateSchema(
            task_id=task.id,
            name="has_both_fields.zim",
            status="checked",
            cms_notified=None,
            check_result=1,
            check_filename="check_report.json",
            check_timestamp=getnow() - timedelta(hours=1),
            created_timestamp=getnow() - timedelta(hours=1),
        ),
    )
    dbsession.flush()

    with patch(
        "zimfarm_backend.background_tasks.send_cms_notifications.advertise_book_to_cms"
    ) as mock_advertise:
        notify_cms_for_checked_files(dbsession)
        mock_advertise.assert_called_once()


def test_send_cms_notifications_skip_without_check_fields(
    dbsession: OrmSession,
    create_task: Callable[..., Task],
    monkeypatch: pytest.MonkeyPatch,
):
    """Test that files without any check fields are skipped even if recent"""
    monkeypatch.setattr(send_cms_notifications_module, "INFORM_CMS", True)
    monkeypatch.setattr(
        send_cms_notifications_module, "CMS_MAXIMUM_RETRY_INTERVAL", 24 * 60 * 60
    )
    task = create_task()

    # Create a file without check fields but recent
    create_or_update_task_file(
        dbsession,
        FileCreateUpdateSchema(
            task_id=task.id,
            name="no_check_fields.zim",
            status="uploaded",
            cms_notified=None,
            check_result=None,  # No check_result
            check_filename=None,  # No check_filename
            check_timestamp=getnow() - timedelta(hours=1),  # Recent but no check fields
            created_timestamp=getnow() - timedelta(hours=1),
        ),
    )
    dbsession.flush()

    with patch(
        "zimfarm_backend.background_tasks.send_cms_notifications.advertise_book_to_cms"
    ) as mock_advertise:
        notify_cms_for_checked_files(dbsession)
        # Should NOT be notified - missing check fields
        mock_advertise.assert_not_called()


def test_send_cms_notifications_skip_old_timestamp(
    dbsession: OrmSession,
    create_task: Callable[..., Task],
    monkeypatch: pytest.MonkeyPatch,
):
    """Test that files older than wait interval are skipped even with check fields"""
    monkeypatch.setattr(send_cms_notifications_module, "INFORM_CMS", True)
    monkeypatch.setattr(
        send_cms_notifications_module, "CMS_MAXIMUM_RETRY_INTERVAL", 24 * 60 * 60
    )
    task = create_task()

    old_timestamp = getnow() - timedelta(days=30)
    # Create a file with check fields but too old
    create_or_update_task_file(
        dbsession,
        FileCreateUpdateSchema(
            task_id=task.id,
            name="old_file.zim",
            status="checked",
            cms_notified=None,
            check_result=1,  # Has check field
            check_filename="report.json",  # Has check field
            check_timestamp=old_timestamp,  # Too old
            created_timestamp=old_timestamp,
        ),
    )
    dbsession.flush()

    with patch(
        "zimfarm_backend.background_tasks.send_cms_notifications.advertise_book_to_cms"
    ) as mock_advertise:
        notify_cms_for_checked_files(dbsession)
        # Should NOT be notified - too old
        mock_advertise.assert_not_called()


def test_send_cms_notifications_coalesce_uses_created_timestamp(
    dbsession: OrmSession,
    create_task: Callable[..., Task],
    monkeypatch: pytest.MonkeyPatch,
):
    """Test that created_timestamp is used when check_timestamp is NULL"""
    monkeypatch.setattr(send_cms_notifications_module, "INFORM_CMS", True)
    monkeypatch.setattr(
        send_cms_notifications_module, "CMS_MAXIMUM_RETRY_INTERVAL", 24 * 60 * 60
    )
    task = create_task()

    recent_created = getnow() - timedelta(hours=1)
    # File with no check_timestamp but recent created_timestamp
    create_or_update_task_file(
        dbsession,
        FileCreateUpdateSchema(
            task_id=task.id,
            name="recent_created.zim",
            status="uploaded",
            cms_notified=None,
            check_result=1,  # Has check field
            check_filename=None,
            check_timestamp=None,  # NULL
            created_timestamp=recent_created,  # Should use this
        ),
    )
    dbsession.flush()

    with patch(
        "zimfarm_backend.background_tasks.send_cms_notifications.advertise_book_to_cms"
    ) as mock_advertise:
        notify_cms_for_checked_files(dbsession)
        # Should be notified - recent created_timestamp + has check field
        mock_advertise.assert_called_once()
