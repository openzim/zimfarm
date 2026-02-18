import datetime
from http import HTTPStatus
from typing import Any, cast

import requests
import sqlalchemy as sa
from requests.auth import HTTPBasicAuth
from sqlalchemy import func, or_
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.background_tasks import logger
from zimfarm_backend.background_tasks.constants import (
    CMS_MAXIMUM_RETRY_INTERVAL,
    CMS_OAUTH_AUDIENCE_ID,
    CMS_OAUTH_CLIENT_ID,
    CMS_OAUTH_CLIENT_SECRET,
    CMS_OAUTH_ISSUER,
    CMS_TOKEN_RENEWAL_WINDOW,
)
from zimfarm_backend.common import getnow
from zimfarm_backend.common.constants import (
    CMS_ENDPOINT,
    INFORM_CMS,
    REQ_TIMEOUT_CMS,
    REQUESTS_TIMEOUT,
)
from zimfarm_backend.common.schemas.models import FileCreateUpdateSchema
from zimfarm_backend.common.schemas.orms import (
    TaskFileSchema,
    TaskFullSchema,
)
from zimfarm_backend.common.upload import upload_url
from zimfarm_backend.db.models import File, Task
from zimfarm_backend.db.tasks import create_or_update_task_file, get_task_by_id


class CMSClientTokenProvider:
    """Client to generate access tokens to authenticate with CMS"""

    def __init__(self):
        self._access_token: str | None = None
        self._expires_at: datetime.datetime = datetime.datetime.fromtimestamp(
            0
        ).replace(tzinfo=None)

    def get_access_token(self) -> str:
        """Retrieve or generate access token depending on if token has expired."""
        now = getnow()
        if self._access_token is None or now >= (
            self._expires_at - CMS_TOKEN_RENEWAL_WINDOW
        ):
            response = requests.post(
                f"{CMS_OAUTH_ISSUER}/oauth2/token",
                data={
                    "grant_type": "client_credentials",
                    "audience": CMS_OAUTH_AUDIENCE_ID,
                },
                auth=HTTPBasicAuth(CMS_OAUTH_CLIENT_ID, CMS_OAUTH_CLIENT_SECRET),
                timeout=REQUESTS_TIMEOUT,
            )
            response.raise_for_status()

            payload = response.json()
            self._access_token = cast(str, payload["access_token"])
            self._expires_at = getnow() + datetime.timedelta(
                seconds=payload["expires_in"]
            )
        return self._access_token


cms_client_token_provider = CMSClientTokenProvider()


def advertise_book_to_cms(session: OrmSession, task: TaskFullSchema, file_name: str):
    """inform openZIM CMS (or compatible) of a created ZIM in the farm

    Safe to re-run as successful requests are skipped
    """

    file_data = task.files[file_name]

    if file_data.cms_notified:
        logger.warning(f"Book {file_data.name} already advertised to CMS")
        return
    try:
        access_token = cms_client_token_provider.get_access_token()
    except Exception:
        logger.exception("Unable to generate access token to authenticate with CMS")
        return

    file_data.cms_on = getnow()
    file_data.cms_notified = False
    try:
        resp = requests.post(
            CMS_ENDPOINT,
            json=get_openzimcms_payload(
                file_data,
                task.upload.check.upload_uri if task.upload.check else None,
            ),
            timeout=REQ_TIMEOUT_CMS,
            headers={"Authorization": f"Bearer {access_token}"},
        )
    except Exception:
        logger.exception(f"Unable to advertise book to CMS at {CMS_ENDPOINT}")
    else:
        status_code = HTTPStatus(resp.status_code)
        file_data.cms_notified = status_code.is_success
        if not status_code.is_success:
            logger.error(
                f"CMS returned an error {resp.status_code} for book"
                f"{file_data.info['id']}"
            )

    # record request result
    create_or_update_task_file(
        session,
        FileCreateUpdateSchema(
            task_id=task.id,
            name=file_name,
            status=file_data.status,
            cms_on=file_data.cms_on,
            cms_notified=file_data.cms_notified,
        ),
    )


def get_openzimcms_payload(
    file: TaskFileSchema, zimcheck_base_url: str | None
) -> dict[str, Any]:
    payload = {
        "id": file.info["id"],
        "counter": file.info.get("counter"),
        "article_count": file.info.get("article_count"),
        "media_count": file.info.get("media_count"),
        "size": file.info.get("size"),
        "metadata": file.info.get("metadata"),
        "zimcheck_url": (
            upload_url(zimcheck_base_url, file.check_filename)
            if zimcheck_base_url and file.check_filename
            else None
        ),
    }
    return payload


def notify_cms_for_checked_files(session: OrmSession):
    """Send notifications to CMS about checked files."""

    if not INFORM_CMS:
        logger.info("::: CMS notifications are disabled (INFORM_CMS=false)")
        return

    logger.info(":: checking for files needing CMS notification")

    files_to_notify = session.execute(
        sa.select(File, Task.id.label("task_id"))
        .join(Task, Task.id == File.task_id)
        .where(
            # We should send notifications for files that meet the following criteria:
            # - have not been successfully notified
            # - have  check_result or check_filename
            # - are not older than CMS_MAXIMUM_RETRY_INTERVAL since check_timestamp
            #   so we don't discard notifying CMS about a file because the zimcheck
            #   results were not uploaded due to another issue.
            or_(File.cms_notified.is_(None), File.cms_notified.is_(False)),
            or_(File.check_result.is_not(None), File.check_filename.is_not(None)),
            func.extract(
                "epoch",
                func.now()
                - func.coalesce(File.check_timestamp, File.created_timestamp),
            )
            < CMS_MAXIMUM_RETRY_INTERVAL,
        )
    ).all()

    nb_files = len(files_to_notify)
    if nb_files == 0:
        logger.info("::: no files need CMS notification")
        return

    logger.info(f"::: found {nb_files} file(s) needing CMS notification")

    nb_notified = 0

    try:
        for row in files_to_notify:
            file = cast(File, row.File)
            task_full = get_task_by_id(session, row.task_id)

            advertise_book_to_cms(session, task_full, file.name)
            nb_notified += 1

            logger.debug(f"Notified CMS for file {file.name} from task {row.task_id}")
    except Exception:
        logger.exception(
            f"Failed to send CMS notification, sent {nb_notified} notifications to CMS"
        )
    else:
        logger.info(f"::: Sent {nb_notified} notifications to CMS")
