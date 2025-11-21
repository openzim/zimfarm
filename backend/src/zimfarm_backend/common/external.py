import ipaddress
import json
import logging
from http import HTTPStatus
from typing import Any, cast

import requests
import sqlalchemy as sa
import sqlalchemy.orm as so
from kiwixstorage import (  # pyright: ignore[reportMissingTypeStubs]
    AuthenticationError,
    KiwixStorage,
)

import zimfarm_backend.db.models as dbm
from zimfarm_backend.common import getnow
from zimfarm_backend.common.constants import (
    CMS_ENDPOINT,
    CMS_ZIM_DOWNLOAD_URL,
    REQ_TIMEOUT_CMS,
    WASABI_MAX_WHITELIST_VERSIONS,
    WASABI_REQUEST_TIMEOUT,
    WASABI_URL,
    WASABI_WHITELIST_POLICY_ARN,
    WASABI_WHITELIST_STATEMENT_ID,
    WHITELISTED_IPS,
)
from zimfarm_backend.common.schemas.models import FileCreateUpdateSchema
from zimfarm_backend.common.schemas.orms import (
    TaskFileSchema,
    TaskFullSchema,
)
from zimfarm_backend.common.upload import upload_url
from zimfarm_backend.db.tasks import create_or_update_task_file

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def update_workers_whitelist(session: so.Session):
    """update whitelist of workers on external services"""
    update_wasabi_whitelist(build_workers_whitelist(session=session))


def build_workers_whitelist(session: so.Session) -> list[str]:
    """list of worker IP adresses and networks (text) to use as whitelist"""
    wl_networks: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
    wl_ips: list[ipaddress.IPv4Address | ipaddress.IPv6Address] = []
    for item in WHITELISTED_IPS:
        if "/" in item:
            wl_networks.append(ipaddress.ip_network(item))
        else:
            wl_ips.append(ipaddress.ip_address(item))

    def is_covered(ip_addr: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
        for network in wl_networks:
            if ip_addr in network:
                return True
        return False

    for row in session.execute(
        sa.select(dbm.Worker.last_ip)
        .join(dbm.User)
        .filter(dbm.Worker.last_ip.is_not(None))
        .filter(dbm.User.deleted.is_(False))
        .filter(dbm.Worker.deleted.is_(False))
    ).scalars():
        if row is None:
            continue
        ip_addr = ipaddress.ip_address(row)
        if not is_covered(ip_addr):
            wl_ips.append(ip_addr)

    return [str(addr) for addr in set(wl_networks + wl_ips)]


def update_wasabi_whitelist(ip_addresses: list[str]):
    """update Wasabi policy to change IP adresses whitelist"""
    logger.info("Updating Wasabi whitelist")

    def get_statement() -> dict[str, Any]:
        return {
            "Sid": f"{WASABI_WHITELIST_STATEMENT_ID}",
            "Effect": "Deny",
            "Action": "s3:*",
            "Resource": "arn:aws:s3:::*",
            "Condition": {"NotIpAddress": {"aws:SourceIp": ip_addresses}},
        }

    if not WASABI_URL:
        logger.error("> Unable to update workers whitelist: missing WASABI_URL")
        return

    s3 = KiwixStorage(
        url=WASABI_URL,
        connect_timeout=WASABI_REQUEST_TIMEOUT,
        read_timeout=WASABI_REQUEST_TIMEOUT,
    )
    try:
        if not s3.check_credentials(  # pyright: ignore[reportUnknownMemberType]
            list_buckets=True, failsafe=False
        ):
            raise AuthenticationError("check_credentials failed")
    except Exception as exc:
        logger.error(
            f"> Unable to update workers whitelist: no auth for WASABI_URL: {exc}"
        )
        return

    iam = s3.get_service(  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
        "iam"  # pyright: ignore[reportArgumentType]
    )
    versions: list[dict[str, Any]] = cast(
        list[dict[str, Any]],
        iam.list_policy_versions(  # pyright: ignore[reportUnknownMemberType]
            PolicyArn=WASABI_WHITELIST_POLICY_ARN
        ).get("Versions", []),
    )
    logger.debug(f" > {len(versions)} versions for {WASABI_WHITELIST_POLICY_ARN}")

    version_id: str | None = None
    for version in versions:
        if version["IsDefaultVersion"]:
            version_id = version["VersionId"]

    logger.debug(f"> Default version is {version_id}")

    # delete all other versions
    if len(versions) == WASABI_MAX_WHITELIST_VERSIONS:
        logger.debug("> Deleting all other versions…")
        for version in versions:
            if version["VersionId"] == version_id:
                continue
            logger.debug(f"> Deleting version {version['VersionId']}")
            iam.delete_policy_version(  # pyright: ignore[reportUnknownMemberType]
                PolicyArn=WASABI_WHITELIST_POLICY_ARN, VersionId=version["VersionId"]
            )

    if not version_id:
        logger.error("> Existing policy doesn't exist. probably a mistake?")
        return

    pv = cast(
        dict[str, Any],
        iam.get_policy_version(  # pyright: ignore[reportUnknownMemberType]
            PolicyArn=WASABI_WHITELIST_POLICY_ARN, VersionId=version_id
        )
        .get("PolicyVersion", {})
        .get("Document", {}),
    )
    if not pv:
        logger.error("> We don't have a policy document.")
        return

    statement = get_statement()  # gen new statement

    try:
        stmt_index = [s["Sid"] for s in pv["Statement"]].index(
            WASABI_WHITELIST_STATEMENT_ID
        )
        pv["Statement"][stmt_index] = statement
    except ValueError:
        pv["Statement"].append(statement)

    new_policy = json.dumps(pv, indent=4)
    # logger.debug(f"New Policy:\n{new_policy}")

    logger.debug("> Overwriting policy…")
    iam.create_policy_version(  # pyright: ignore[reportUnknownMemberType]
        PolicyArn=WASABI_WHITELIST_POLICY_ARN,
        PolicyDocument=new_policy,
        SetAsDefault=True,
    )


def advertise_book_to_cms(session: so.Session, task: TaskFullSchema, file_name: str):
    """inform openZIM CMS (or compatible) of a created ZIM in the farm

    Safe to re-run as successful requests are skipped"""

    file_data = task.files[file_name]

    # skip if already advertised to CMS
    if file_data.cms_notified:
        logger.warning(f"Book {file_data.name} already advertised to CMS")
        return

    # prepare payload and submit request to CMS
    download_prefix = f"{CMS_ZIM_DOWNLOAD_URL}{task.config.warehouse_path}"
    file_data.cms_on = getnow()
    file_data.cms_notified = False
    try:
        resp = requests.post(
            CMS_ENDPOINT,
            json=get_openzimcms_payload(
                file_data,
                download_prefix,
                task.upload.check.upload_uri if task.upload.check else None,
            ),
            timeout=REQ_TIMEOUT_CMS,
        )
    except Exception as exc:
        logger.error(f"Unable to query CMS at {CMS_ENDPOINT}: {exc}")
        logger.exception(exc)
    else:
        status_code = HTTPStatus(resp.status_code)
        file_data.cms_notified = status_code.is_success
        if status_code.is_success:
            try:
                resp.json()
            except Exception as exc:
                logger.error(f"Unable to parse CMS response: {exc}")
                logger.exception(exc)
        else:
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
    file: TaskFileSchema, download_prefix: str, zimcheck_base_url: str | None
) -> dict[str, Any]:
    payload = {
        "id": file.info["id"],
        "period": file.info.get("metadata", {}).get("Date"),
        "counter": file.info.get("counter"),
        "article_count": file.info.get("article_count"),
        "media_count": file.info.get("media_count"),
        "size": file.info.get("size"),
        "metadata": file.info.get("metadata"),
        "url": f"{download_prefix}/{file.name}",
        "zimcheck_url": (
            upload_url(zimcheck_base_url, file.check_filename)
            if zimcheck_base_url and file.check_filename
            else None
        ),
    }
    return payload
