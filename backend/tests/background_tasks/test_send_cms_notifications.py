from collections.abc import Callable
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
    # Create a file that needs notification
    create_or_update_task_file(
        dbsession,
        FileCreateUpdateSchema(
            task_id=task.id,
            name="test.zim",
            status="checked",
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

    # Create a file that failed notification
    create_or_update_task_file(
        dbsession,
        FileCreateUpdateSchema(
            task_id=task.id,
            name="failed_notification.zim",
            status="checked",
            cms_notified=False,  # Failed notification
            cms_on=getnow(),
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
    """Test that files never notified are attempted"""
    monkeypatch.setattr(send_cms_notifications_module, "INFORM_CMS", True)
    task = create_task()

    # Create a file that was never notified
    create_or_update_task_file(
        dbsession,
        FileCreateUpdateSchema(
            task_id=task.id,
            name="never_notified.zim",
            status="checked",
            cms_notified=None,  # Never attempted
        ),
    )
    dbsession.flush()

    with patch(
        "zimfarm_backend.background_tasks.send_cms_notifications.advertise_book_to_cms"
    ) as mock_advertise:
        notify_cms_for_checked_files(dbsession)
        mock_advertise.assert_called_once()


def test_send_cms_notifications_skip_non_checked_files(
    dbsession: OrmSession,
    create_task: Callable[..., Task],
    monkeypatch: pytest.MonkeyPatch,
):
    """Test that files not in 'checked' status are skipped"""
    monkeypatch.setattr(send_cms_notifications_module, "INFORM_CMS", True)
    task = create_task()

    # Create files in various non-checked statuses
    for status in ["created", "uploaded", "failed", "checking"]:
        create_or_update_task_file(
            dbsession,
            FileCreateUpdateSchema(
                task_id=task.id,
                name=f"{status}_file.zim",
                status=status,
                cms_notified=None,  # Never notified
            ),
        )
    dbsession.flush()

    with patch(
        "zimfarm_backend.background_tasks.send_cms_notifications.advertise_book_to_cms"
    ) as mock_advertise:
        notify_cms_for_checked_files(dbsession)
        mock_advertise.assert_not_called()
