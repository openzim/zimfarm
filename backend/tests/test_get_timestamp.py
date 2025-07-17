import datetime

import pytest

from zimfarm_backend.utils.task import DEFAULT_TIMESTAMP, get_timestamp_for_status


@pytest.mark.parametrize(
    "timestamp_list,status,expected",
    [
        # Test finding the most recent timestamp for a status
        pytest.param(
            [
                ("started", datetime.datetime(2023, 1, 1, 10, 0)),
                ("completed", datetime.datetime(2023, 1, 1, 12, 0)),
                ("started", datetime.datetime(2023, 1, 1, 11, 0)),  # More recent
            ],
            "started",
            datetime.datetime(2023, 1, 1, 11, 0),
            id="most_recent_timestamp_for_status",
        ),
        # Test single timestamp for a status
        pytest.param(
            [
                ("started", datetime.datetime(2023, 1, 1, 10, 0)),
                ("completed", datetime.datetime(2023, 1, 1, 12, 0)),
            ],
            "started",
            datetime.datetime(2023, 1, 1, 10, 0),
            id="single_timestamp_for_status",
        ),
        # Test status not found - should return default
        pytest.param(
            [
                ("started", datetime.datetime(2023, 1, 1, 10, 0)),
                ("completed", datetime.datetime(2023, 1, 1, 12, 0)),
            ],
            "not_found",
            DEFAULT_TIMESTAMP,
            id="status_not_found_returns_default",
        ),
        # Test empty list - should return default
        pytest.param(
            [],
            "any_status",
            DEFAULT_TIMESTAMP,
            id="empty_list_returns_default",
        ),
    ],
)
def test_get_timestamp_for_status(
    timestamp_list: list[tuple[str, datetime.datetime]],
    status: str,
    expected: datetime.datetime,
) -> None:
    """Test get_timestamp_for_status function with various scenarios."""
    result = get_timestamp_for_status(timestamp_list, status)
    assert result == expected


@pytest.mark.parametrize(
    "timestamp_list,status,custom_default,expected",
    [
        # Test with custom default when status not found
        pytest.param(
            [
                ("started", datetime.datetime(2023, 1, 1, 10, 0)),
            ],
            "not_found",
            datetime.datetime(2024, 1, 1),
            datetime.datetime(2024, 1, 1),
            id="custom_default_used_when_status_not_found",
        ),
        # Test with custom default but status exists - should ignore default
        pytest.param(
            [
                ("started", datetime.datetime(2023, 1, 1, 10, 0)),
            ],
            "started",
            datetime.datetime(2024, 1, 1),
            datetime.datetime(2023, 1, 1, 10, 0),
            id="custom_default_ignored_when_status_exists",
        ),
    ],
)
def test_get_timestamp_for_status_with_custom_default(
    timestamp_list: list[tuple[str, datetime.datetime]],
    status: str,
    custom_default: datetime.datetime,
    expected: datetime.datetime,
) -> None:
    """Test get_timestamp_for_status function with custom default parameter."""
    result = get_timestamp_for_status(timestamp_list, status, default=custom_default)
    assert result == expected
