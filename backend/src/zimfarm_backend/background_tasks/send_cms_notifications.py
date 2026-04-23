import datetime
from http import HTTPStatus
from typing import Any, cast

import requests
from requests.auth import HTTPBasicAuth
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.background_tasks import logger
from zimfarm_backend.background_tasks.constants import (
    CMS_AUTH_MODE,
    CMS_MAXIMUM_RETRY_INTERVAL,
    CMS_OAUTH_AUDIENCE_ID,
    CMS_OAUTH_CLIENT_ID,
    CMS_OAUTH_CLIENT_SECRET,
    CMS_OAUTH_ISSUER,
    CMS_PASSWORD,
    CMS_TOKEN_RENEWAL_WINDOW,
    CMS_USERNAME,
)
from zimfarm_backend.common import getnow
from zimfarm_backend.common.constants import (
    CMS_BASE_URL,
    INFORM_CMS,
    REQ_TIMEOUT_CMS,
    REQUESTS_TIMEOUT,
)
from zimfarm_backend.common.schemas.models import FileCreateUpdateSchema
from zimfarm_backend.common.schemas.orms import (
    TaskFileSchema,
    TaskFullSchema,
)
from zimfarm_backend.common.upload import generate_http_upload_url
from zimfarm_backend.db.files import get_files_to_notify
from zimfarm_backend.db.tasks import (
    create_or_update_task_file,
    get_task_by_id,
)


class CMSClientTokenProvider:
    """Client to generate access tokens to authenticate with CMS"""

    def __init__(self):
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._expires_at: datetime.datetime = datetime.datetime.fromtimestamp(
            0
        ).replace(tzinfo=None)

    def _generate_oauth_access_token(self) -> None:
        """Generate oauth access token and update expires_at."""
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
        self._expires_at = getnow() + datetime.timedelta(seconds=payload["expires_in"])

    def _generate_local_access_token(self) -> None:
        if self._refresh_token:
            response = requests.post(
                f"{CMS_BASE_URL}/auth/refresh",
                json={
                    "refresh_token": self._refresh_token,
                },
                timeout=REQUESTS_TIMEOUT,
            )
        else:
            response = requests.post(
                f"{CMS_BASE_URL}/auth/authorize",
                json={
                    "username": CMS_USERNAME,
                    "password": CMS_PASSWORD,
                },
                timeout=REQUESTS_TIMEOUT,
            )

        response.raise_for_status()
        payload = response.json()
        self._access_token = cast(str, payload["access_token"])
        self._refresh_token = cast(str, payload["refresh_token"])
        self._expires_at = datetime.datetime.fromisoformat(
            payload["expires_time"]
        ).replace(tzinfo=None)

    def get_access_token(self) -> str:
        """Retrieve or generate access token depending on if token has expired."""
        now = getnow()
        if self._access_token is None or now >= (
            self._expires_at - CMS_TOKEN_RENEWAL_WINDOW
        ):
            if CMS_AUTH_MODE == "oauth":
                self._generate_oauth_access_token()
            elif CMS_AUTH_MODE == "local":
                self._generate_local_access_token()
            else:
                raise ValueError(
                    f"Unknown cms authentication mode: {CMS_AUTH_MODE}. "
                    "Allowed values are: 'local', 'oauth'"
                )
        if self._access_token is None:
            raise ValueError("Failed to generate access token.")
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
    url = f"{CMS_BASE_URL}/zimfarm-notifications"
    try:
        resp = requests.post(
            url,
            json=get_openzimcms_payload(
                file=file_data,
                warehouse_path=task.config.warehouse_path,
                zimcheck_base_url=(
                    task.upload.check.upload_uri if task.upload.check else None
                ),
            ),
            timeout=REQ_TIMEOUT_CMS,
            headers={"Authorization": f"Bearer {access_token}"},
        )
    except Exception:
        logger.exception(f"Unable to advertise book to CMS at {url}")
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
    *, file: TaskFileSchema, zimcheck_base_url: str | None, warehouse_path: str
) -> dict[str, Any]:
    # remove leading "/" in warehouse path since CMS expects relative paths
    folder_name = (
        warehouse_path[1:] if warehouse_path.startswith("/") else warehouse_path
    )
    payload = {
        "id": file.info["id"],
        "counter": file.info.get("counter"),
        "article_count": file.info.get("article_count"),
        "folder_name": folder_name,
        "filename": file.name,
        "media_count": file.info.get("media_count"),
        "size": file.info.get("size"),
        "metadata": file.info.get("metadata"),
        "zimcheck_url": (
            generate_http_upload_url(zimcheck_base_url, file.check_filename)
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

    results = get_files_to_notify(session, retry_interval=CMS_MAXIMUM_RETRY_INTERVAL)

    if results.nb_records == 0:
        logger.info("::: no files need CMS notification")
        return

    logger.info(f"::: found {len(results.files)} file(s) needing CMS notification")

    nb_notified = 0

    try:
        for file in results.files:
            task_full = get_task_by_id(session, file.task_id)
            advertise_book_to_cms(session, task_full, file.filename)
            nb_notified += 1

            logger.debug(
                f"Notified CMS for file {file.filename} from task {file.task_id}"
            )
    except Exception:
        logger.exception(
            f"Failed to send CMS notification, sent {nb_notified} notifications to CMS"
        )
    else:
        logger.info(f"::: Sent {nb_notified} notifications to CMS")
