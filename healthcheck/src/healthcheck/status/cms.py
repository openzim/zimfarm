import datetime

from pydantic import BaseModel

from healthcheck import getnow
from healthcheck.constants import (
    CMS_API_URL,
    CMS_PENDING_THRESHOLD,
    ZIMFARM_API_URL,
)
from healthcheck.status import Result
from healthcheck.status import status_logger as logger
from healthcheck.status.requests import query_api


class CmsHealthCheck(BaseModel):
    status: str
    timestamp: str


class PendingFile(BaseModel):
    filename: str
    created_timestamp: str


class PendingNotificationsStatus(BaseModel):
    total_pending: int
    pending_too_long: int
    files_pending_too_long: list[str]


async def check_cms_availability() -> Result[CmsHealthCheck]:
    """Check if CMS API is available."""

    check_name = "cms-healthcheck"

    response = await query_api(
        f"{CMS_API_URL}/healthcheck", method="GET", check_name=check_name
    )
    if not response.success:
        data = None
    else:
        data = CmsHealthCheck.model_validate(response.json)
    return Result(
        success=response.success,
        status_code=response.status_code,
        data=data,
    )


async def check_cms_pending_notifications() -> Result[PendingNotificationsStatus]:
    """Check if there are files pending CMS notifications for too long."""

    check_name = "cms-pending-notifications"

    response = await query_api(
        f"{ZIMFARM_API_URL}/files/pending-cms-notifications",
        method="GET",
        check_name=check_name,
    )

    if not response.success:
        return Result(
            success=response.success,
            status_code=response.status_code,
            data=None,
        )

    items = response.json.get("items", [])
    total_pending = len(items)

    if total_pending == 0:
        return Result(
            success=True,
            status_code=response.status_code,
            data=PendingNotificationsStatus(
                total_pending=0,
                pending_too_long=0,
                files_pending_too_long=[],
            ),
        )

    now = getnow()
    files_pending_too_long: list[str] = []

    for item in items:
        created_timestamp = datetime.datetime.fromisoformat(
            item["created_timestamp"]
        ).replace(tzinfo=None)

        if (now - created_timestamp) > CMS_PENDING_THRESHOLD:
            files_pending_too_long.append(item["filename"])

    pending_too_long_count = len(files_pending_too_long)

    if pending_too_long_count > 0:
        logger.warning(
            f"{pending_too_long_count} file(s) have been pending CMS notification "
            f"for more than {CMS_PENDING_THRESHOLD} seconds: {files_pending_too_long}",
            extra={"checkname": check_name},
        )

    return Result(
        success=pending_too_long_count == 0,
        status_code=response.status_code,
        data=PendingNotificationsStatus(
            total_pending=total_pending,
            pending_too_long=pending_too_long_count,
            files_pending_too_long=files_pending_too_long,
        ),
    )
