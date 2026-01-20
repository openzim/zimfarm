from collections.abc import Generator
from http import HTTPStatus
from unittest.mock import MagicMock, patch

import pytest

from healthcheck.status.requests import Response
from healthcheck.status.tasks import (
    TaskUploadStatus,
    check_log_and_artifacts_upload_status,
)


@pytest.fixture
def mock_query_api() -> Generator[MagicMock]:
    """Fixture to mock the query_api function."""
    with patch("healthcheck.status.tasks.query_api") as mock:
        yield mock


async def test_check_log_and_artifacts_upload_status_success(
    mock_query_api: MagicMock,
) -> None:
    """Test successful check with logs and artifacts uploaded."""
    # Mock the first API call (list tasks)
    tasks_list_response = Response(
        status_code=HTTPStatus.OK,
        success=True,
        json={"items": [{"id": "task_123"}]},
    )

    # Mock the second API call (get specific task)
    task_detail_response = Response(
        status_code=HTTPStatus.OK,
        success=True,
        json={
            "container": {
                "log": "path/to/log.txt",
                "artifacts": "path/to/artifacts.tar.gz",
            },
            "config": {"artifacts_globs": ["*.txt", "*.log"]},
            "upload": {"artifacts": {"upload_uri": "s3://bucket/path"}},
        },
    )

    mock_query_api.side_effect = [tasks_list_response, task_detail_response]

    result = await check_log_and_artifacts_upload_status()

    assert result.success is True
    assert result.status_code == HTTPStatus.OK
    assert result.data is not None
    assert isinstance(result.data, TaskUploadStatus)
    assert result.data.logs_uploaded is True
    assert result.data.artifacts_uploaded is True


async def test_check_log_and_artifacts_upload_status_logs_only(
    mock_query_api: MagicMock,
) -> None:
    """Test when only logs are uploaded but not artifacts."""
    tasks_list_response = Response(
        status_code=HTTPStatus.OK,
        success=True,
        json={"items": [{"id": "task_456"}]},
    )

    task_detail_response = Response(
        status_code=HTTPStatus.OK,
        success=True,
        json={
            "container": {
                "log": "path/to/log.txt",
                # No artifacts field
            },
            "config": {"artifacts_globs": ["*.txt"]},
            "upload": {"artifacts": {"upload_uri": "s3://bucket/path"}},
        },
    )

    mock_query_api.side_effect = [tasks_list_response, task_detail_response]

    result = await check_log_and_artifacts_upload_status()

    assert result.success is False
    assert result.status_code == HTTPStatus.OK
    assert result.data is not None
    assert result.data.logs_uploaded is True
    assert result.data.artifacts_uploaded is False


async def test_check_log_and_artifacts_upload_status_no_artifacts_globs(
    mock_query_api: MagicMock,
) -> None:
    """Test when artifacts_globs is empty (no artifacts expected)."""
    tasks_list_response = Response(
        status_code=HTTPStatus.OK,
        success=True,
        json={"items": [{"id": "task_789"}]},
    )

    task_detail_response = Response(
        status_code=HTTPStatus.OK,
        success=True,
        json={
            "container": {
                "log": "path/to/log.txt",
                "artifacts": "path/to/artifacts.tar.gz",
            },
            "config": {"artifacts_globs": []},  # Empty list means no artifacts expected
            "upload": {"artifacts": {"upload_uri": "s3://bucket/path"}},
        },
    )

    mock_query_api.side_effect = [tasks_list_response, task_detail_response]

    result = await check_log_and_artifacts_upload_status()

    assert result.success is True
    assert result.data is not None
    assert result.data.logs_uploaded is True
    assert result.data.artifacts_uploaded is True


async def test_check_log_and_artifacts_upload_status_no_logs(
    mock_query_api: MagicMock,
) -> None:
    """Test when logs are not uploaded."""
    tasks_list_response = Response(
        status_code=HTTPStatus.OK,
        success=True,
        json={"items": [{"id": "task_202"}]},
    )

    task_detail_response = Response(
        status_code=HTTPStatus.OK,
        success=True,
        json={
            "container": {
                # No log field
                "artifacts": "path/to/artifacts.tar.gz",
            },
            "config": {"artifacts_globs": ["*.txt"]},
            "upload": {"artifacts": {"upload_uri": "s3://bucket/path"}},
        },
    )

    mock_query_api.side_effect = [tasks_list_response, task_detail_response]

    result = await check_log_and_artifacts_upload_status()

    assert result.success is False
    assert result.data is not None
    assert result.data.logs_uploaded is False
    assert result.data.artifacts_uploaded is True


async def test_check_log_and_artifacts_upload_status_first_api_call_fails(
    mock_query_api: MagicMock,
) -> None:
    """Test when the first API call to list tasks fails."""
    tasks_list_response = Response(
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        success=False,
        json={},
        error="Internal server error",
    )

    mock_query_api.return_value = tasks_list_response

    result = await check_log_and_artifacts_upload_status()

    assert result.success is False
    assert result.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert result.data is None

    assert mock_query_api.call_count == 1


async def test_check_log_and_artifacts_upload_status_second_api_call_fails(
    mock_query_api: MagicMock,
) -> None:
    """Test when the second API call to get task details fails."""
    tasks_list_response = Response(
        status_code=HTTPStatus.OK,
        success=True,
        json={"items": [{"id": "task_303"}]},
    )

    task_detail_response = Response(
        status_code=HTTPStatus.NOT_FOUND,
        success=False,
        json={},
        error="Task not found",
    )

    mock_query_api.side_effect = [tasks_list_response, task_detail_response]

    result = await check_log_and_artifacts_upload_status()

    assert result.success is False
    assert result.status_code == HTTPStatus.NOT_FOUND
    assert result.data is None

    assert mock_query_api.call_count == 2
