import datetime
from unittest.mock import Mock

from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.background_tasks.task_config import TaskConfig
from zimfarm_backend.common import getnow


def test_should_run_returns_true_when_interval_exceeded():
    """Test that should_run returns True when interval has been exceeded"""
    mock_func = Mock()
    interval = datetime.timedelta(minutes=5)

    config = TaskConfig(func=mock_func, interval=interval)
    config._last_run = datetime.datetime(  # pyright: ignore[reportPrivateUsage]
        2024, 1, 1, 12, 0, 0
    )

    now = datetime.datetime(2024, 1, 1, 12, 6, 0)  # 6 minutes later

    assert config.should_run(now) is True


def test_should_run_returns_false_when_interval_not_met():
    """Test that should_run returns False when interval has not been met"""
    mock_func = Mock()
    interval = datetime.timedelta(minutes=5)

    config = TaskConfig(func=mock_func, interval=interval)
    config._last_run = datetime.datetime(  # pyright: ignore[reportPrivateUsage]
        2024, 1, 1, 12, 0, 0
    )

    now = datetime.datetime(2024, 1, 1, 12, 4, 0)  # Only 4 minutes later

    assert config.should_run(now) is False


def test_should_run_returns_true_for_never_run_task():
    """Test that should_run returns True for a task that has never been run"""
    mock_func = Mock()
    interval = datetime.timedelta(minutes=5)

    config = TaskConfig(func=mock_func, interval=interval)

    now = getnow()

    assert config.should_run(now) is True


def test_execute_calls_function_with_session(dbsession: OrmSession):
    """Test that execute calls the configured function with the session"""
    mock_func = Mock()
    interval = datetime.timedelta(minutes=5)

    config = TaskConfig(func=mock_func, interval=interval)

    config.execute(dbsession)

    mock_func.assert_called_once_with(dbsession)


def test_execute_updates_last_run_timestamp(dbsession: OrmSession):
    """Test that execute updates the _last_run timestamp"""
    mock_func = Mock()
    interval = datetime.timedelta(minutes=5)

    config = TaskConfig(func=mock_func, interval=interval)
    original_last_run = config._last_run  # pyright: ignore[reportPrivateUsage]

    config.execute(dbsession)
    assert config._last_run > original_last_run  # pyright: ignore[reportPrivateUsage]
