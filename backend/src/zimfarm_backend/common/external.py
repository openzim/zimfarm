import ipaddress
import json
import logging
from typing import Any, cast

import sqlalchemy as sa
import sqlalchemy.orm as so
from kiwixstorage import (  # pyright: ignore[reportMissingTypeStubs]
    AuthenticationError,
    KiwixStorage,
)

import zimfarm_backend.db.models as dbm
from zimfarm_backend.common.constants import (
    WASABI_MAX_WHITELIST_VERSIONS,
    WASABI_REQUEST_TIMEOUT,
    WASABI_URL,
    WASABI_WHITELIST_POLICY_ARN,
    WASABI_WHITELIST_STATEMENT_ID,
    WHITELISTED_IPS,
)

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
