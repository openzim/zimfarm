import datetime
import ipaddress
import json
import logging
import typing
from typing import Any, cast
from uuid import UUID

import requests
import sqlalchemy as sa
import sqlalchemy.orm as so
from kiwixstorage import (  # pyright: ignore[reportMissingTypeStubs]
    AuthenticationError,
    KiwixStorage,
)

import zimfarm_backend.db.models as dbm
from zimfarm_backend.common.constants import (
    CMS_ENDPOINT,
    CMS_ZIM_DOWNLOAD_URL,
    REQ_TIMEOUT_CMS,
    WASABI_URL,
    WASABI_WHITELIST_POLICY_ARN,
    WASABI_WHITELIST_STATEMENT_ID,
    WHITELISTED_IPS,
)
from zimfarm_backend.db import dbsession
from zimfarm_backend.errors.http import TaskNotFound

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def update_workers_whitelist(session: so.Session):
    """update whitelist of workers on external services"""
    ExternalIpUpdater.update(build_workers_whitelist(session=session))


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

    s3 = KiwixStorage(url=WASABI_URL)
    try:
        if not s3.check_credentials(list_buckets=True, failsafe=False):  # pyright: ignore[reportUnknownMemberType]
            raise AuthenticationError("check_credentials failed")
    except Exception as exc:
        logger.error(
            f"> Unable to update workers whitelist: no auth for WASABI_URL: {exc}"
        )
        return

    iam = s3.get_service("iam")  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
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
    if len(versions) == 5:  # noqa: PLR2004
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


class ExternalIpUpdater:
    """Class responsible to push IP updates to external system(s)

    `update` is called with the new list of all workers IPs everytime
    a change is detected.
    By default, this class update our IPs whitelist in Wasabi"""

    @staticmethod
    def update(ip_addresses: list[str]) -> None:
        update_wasabi_whitelist(ip_addresses)


@dbsession
def advertise_books_to_cms(task_id: UUID, session: so.Session):
    """inform openZIM CMS of all created ZIMs in the farm for this task

    Safe to re-run as successful requests are skipped"""
    task = dbm.Task.get(session, task_id, TaskNotFound)
    for file_name in task.files.keys():
        advertise_book_to_cms(task, file_name)


def advertise_book_to_cms(task: dbm.Task, file_name: str):
    """inform openZIM CMS (or compatible) of a created ZIM in the farm

    Safe to re-run as successful requests are skipped"""

    file_data = task.files[file_name]

    # skip if already advertised to CMS
    if file_data.get("cms"):
        # cms query already succeeded
        if file_data["cms"].get("succeeded"):
            return

    # prepare payload and submit request to CMS
    download_prefix = f"{CMS_ZIM_DOWNLOAD_URL}{task.config['warehouse_path']}"
    file_data["cms"] = {
        "status_code": -1,
        "succeeded": False,
        "on": datetime.datetime.now(datetime.UTC),
        "book_id": None,
        "title_ident": None,
    }
    try:
        resp = requests.post(
            CMS_ENDPOINT,
            json=get_openzimcms_payload(file_data, download_prefix),
            timeout=REQ_TIMEOUT_CMS,
        )
    except Exception as exc:
        logger.error(f"Unable to query CMS at {CMS_ENDPOINT}: {exc}")
        logger.exception(exc)
    else:
        file_data["cms"]["status_code"] = resp.status_code
        file_data["cms"]["succeeded"] = resp.status_code == 201  # noqa: PLR2004
        if resp.status_code < 400:  # noqa: PLR2004
            try:
                data = resp.json()
                file_data["cms"]["book_id"] = data.get("uuid")
                file_data["cms"]["title_ident"] = data.get("title")
            except Exception as exc:
                logger.error(f"Unable to parse CMS response: {exc}")
                logger.exception(exc)
        else:
            logger.error(
                f"CMS returned an error {resp.status_code} for book"
                f"{file_data['info']['id']}"
            )

    # record request result
    task.files[file_name] = file_data


def get_openzimcms_payload(
    file: dict[str, typing.Any], download_prefix: str
) -> dict[str, typing.Any]:
    payload = {
        "id": file["info"]["id"],
        "period": file["info"].get("metadata", {}).get("Date"),
        "counter": file["info"].get("counter"),
        "article_count": file["info"].get("article_count"),
        "media_count": file["info"].get("media_count"),
        "size": file["info"].get("size"),
        "metadata": file["info"].get("metadata"),
        "url": f"{download_prefix}/{file['name']}",
        "zimcheck": file.get("check_details", {}),
    }
    return payload
