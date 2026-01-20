from typing import Any

from pydantic import BaseModel

from healthcheck.constants import ZIMFARM_API_URL
from healthcheck.status import Result
from healthcheck.status import status_logger as logger
from healthcheck.status.requests import query_api


class TaskUploadStatus(BaseModel):
    logs_uploaded: bool
    artifacts_uploaded: bool


def _check_artifacts_uploaded(task: dict[str, Any]) -> bool:
    """Check if artifacts are uploaded for task."""
    # artificats should be uploaded if artifacts_globs is not empty and
    # upload_uri for artifacts is set and container key has artifacts filename
    if not task.get("config", {}).get("artifacts_globs"):
        return True
    if not task.get("upload", {}).get("artifacts", {}).get("upload_uri"):
        return True

    return bool(task.get("container", {}).get("artifacts"))


async def check_log_and_artifacts_upload_status() -> Result[TaskUploadStatus]:
    """Check the log/artifacts upload status of the last completed task."""
    check_name = "zimfarm-logs-artifacts-upload-status"
    response = await query_api(
        f"{ZIMFARM_API_URL}/tasks",
        method="GET",
        params={"status": "succeeded", "limit": 1},
        check_name=check_name,
    )
    if not response.success:
        return Result(
            success=response.success,
            status_code=response.status_code,
            data=None,
        )

    items = response.json.get("items", [])
    if not items:
        logger.warning("No tasks have been completed", extra={"checkname": check_name})
        return Result(
            success=response.success,
            status_code=response.status_code,
            data=None,
        )
    # Fetch the task from the API
    task_response = await query_api(
        f"{ZIMFARM_API_URL}/tasks/{items[0]['id']}", method="GET", check_name=check_name
    )
    if not task_response.success:
        return Result(
            success=task_response.success,
            status_code=task_response.status_code,
            data=None,
        )
    upload_status = TaskUploadStatus(
        logs_uploaded=bool(task_response.json.get("container", {}).get("log")),
        artifacts_uploaded=_check_artifacts_uploaded(task_response.json),
    )
    return Result(
        success=upload_status.logs_uploaded and upload_status.artifacts_uploaded,
        status_code=response.status_code,
        data=upload_status,
    )
