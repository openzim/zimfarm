import os
from pathlib import Path
from typing import Any

from humanfriendly import parse_size, parse_timespan

from zimfarm_backend.common.enums import SchedulePeriodicity


def parse_bool(value: Any) -> bool:
    """Parse value into boolean."""
    return str(value).lower() in ("true", "1", "yes", "y", "on")


def getenv(key: str, *, mandatory: bool = False, default: Any = None) -> Any:
    value = os.getenv(key) or default

    if mandatory and not value:
        raise OSError(f"Please set the {key} environment variable")

    return value


BASE_DIR = Path(__file__).parent.parent

DEBUG = parse_bool(getenv("DEBUG", default="false"))


REFRESH_TOKEN_EXPIRY_DURATION = parse_timespan(
    getenv("REFRESH_TOKEN_EXPIRY_DURATION", default="30d")
)

MESSAGE_VALIDITY_DURATION = parse_timespan(
    getenv("MESSAGE_VALIDITY_DURATION", default="1m")
)

ENABLED_SCHEDULER = not getenv("DISABLE_SCHEDULER", default="")
DEFAULT_SCHEDULE_DURATION = parse_timespan(
    getenv("DEFAULT_SCHEDULE_DURATION", default="31d")
)

PERIODICITIES = {
    SchedulePeriodicity.monthly: {"days": 31},
    SchedulePeriodicity.quarterly: {"days": 90},
    SchedulePeriodicity.biannualy: {"days": 180},
    SchedulePeriodicity.annually: {"days": 365},
}

ZIM_UPLOAD_URI = getenv(
    "ZIM_UPLOAD_URI", default="sftp://uploader@warehouse.farm.openzim.org:1522/zim"
)
# ZIM files expiration, 0 to disable expiration
# only working in Wasabi S3 for now, works only if retention compliance is activated
# on the bucket and the bucket retention is smaller than value below
ZIM_EXPIRATION = int(getenv("ZIM_EXPIRATION", default="0"))

LOGS_UPLOAD_URI = getenv(
    "LOGS_UPLOAD_URI", default="sftp://uploader@warehouse.farm.openzim.org:1522/logs"
)
# log files expiration, 0 to disable expiration
# only working in Wasabi S3 for now, works only if retention compliance is activated
# on the bucket and the bucket retention is smaller than value below
LOGS_EXPIRATION = int(getenv("LOGS_EXPIRATION", default="30"))
ARTIFACTS_UPLOAD_URI = getenv("ARTIFACTS_UPLOAD_URI", default=None)
# artifact files expiration, 0 to disable expiration
# only working in Wasabi S3 for now, works only if retention compliance is activated
# on the bucket and the bucket retention is smaller than value below
ARTIFACTS_EXPIRATION = int(getenv("ARTIFACTS_EXPIRATION", default="30"))

ZIMCHECK_RESULTS_UPLOAD_URI = getenv(
    "ZIMCHECK_RESULTS_UPLOAD_URI",
    default="sftp://uploader@warehouse.farm.openzim.org:1522/zimchecks",
)
# zimcheck files expiration, 0 to disable expiration
# only working in Wasabi S3 for now, works only if retention compliance is activated
# on the bucket and the bucket retention is smaller than value below
ZIMCHECK_RESULTS_EXPIRATION = int(getenv("ZIMCHECK_RESULTS_EXPIRATION", default="0"))

# empty ZIMCHECK_OPTION means no zimcheck
ZIMCHECK_OPTION = getenv("ZIMCHECK_OPTION", default="")

# Publisher value to "force" in all scrapers if not set in the recipe
DEFAULT_PUBLISHER = getenv("DEFAULT_PUBLISHER")

# NOTIFICATIONS

# in-notification URLs
PUBLIC_URL = getenv("PUBLIC_URL", default="https://farm.openzim.org")
ZIM_DOWNLOAD_URL = getenv(
    "ZIM_DOWNLOAD_URL", default="https://mirror.download.kiwix.org/zim"
)

# mailgun
MAILGUN_FROM = getenv("MAILGUN_FROM", default="zimfarm@localhost")
MAILGUN_API_KEY = getenv("MAILGUN_API_KEY", default="")
MAILGUN_API_URL = getenv("MAILGUN_API_URL", default="")

# slack
SLACK_URL = getenv("SLACK_URL", default="")
# no defauts for branding so it falls back to what's configured in slack
SLACK_USERNAME = getenv("SLACK_USERNAME")
SLACK_EMOJI = getenv("SLACK_EMOJI")
SLACK_ICON = getenv("SLACK_ICON")

# length of secret strings
SECRET_STRING_LENGTH = int(getenv("SECRET_STRING_LENGTH", default=24))

# ###
# workers whitelist management
# ###
# using the following, it is possible to automate
# the update of a whitelist of workers IPs on Wasabi (S3 provider)
# enable this feature (default is off)
USES_WORKERS_IPS_WHITELIST = parse_bool(
    getenv("USES_WORKERS_IPS_WHITELIST", default="false")
)
MAX_WORKER_IP_CHANGES_PER_DAY = int(
    getenv("MAX_WORKER_IP_CHANGES_PER_DAY", default="4")
)
# wasabi URL with credentials to update policy
WASABI_URL = getenv("WASABI_URL", default="")
# policy ARN such as arn:aws:iam::xxxxxxxxxxxx:policy/yyyyyyyy
WASABI_WHITELIST_POLICY_ARN = getenv("WASABI_WHITELIST_POLICY_ARN", default="")
# ID of the statement to set on the policy for the whitelist
WASABI_WHITELIST_STATEMENT_ID = getenv(
    "WASABI_WHITELIST_STATEMENT_ID", default="ZimfarmWorkersIPsWhiteList"
)
WASABI_REQUEST_TIMEOUT = parse_timespan(getenv("WASABI_REQUEST_TIMEOUT", default="10s"))
# list of IPs and networks to always allow (regardless of used by workers or not)
WHITELISTED_IPS = [
    ip.strip() for ip in getenv("WHITELISTED_IPS", default="").split(",") if ip.strip()
]
WASABI_MAX_WHITELIST_VERSIONS = int(
    getenv(
        "WASABI_MAX_WHITELIST_VERSIONS",
        default="5",
    )
)


# openZIM CMS can be called upon receival of each ZIM
INFORM_CMS = parse_bool(getenv("INFORM_CMS", default="false"))
CMS_ENDPOINT = getenv(
    "CMS_ENDPOINT", default="https://api.cms.openzim.org/v1/books/add"
)
# URL to tell the CMS where to download ZIM from
CMS_ZIM_DOWNLOAD_URL = getenv(
    "CMS_ZIM_DOWNLOAD_URL", default="https://download.kiwix.org/zim"
)

# [DEBUG] prevent scraper containers from running wit extended capabilities
DISALLOW_CAPABILITIES = parse_bool(
    getenv("ZIMFARM_DISALLOW_CAPABILITIES", default="false")
)

# Timeout for requests to other services
REQ_TIMEOUT_NOTIFICATIONS = int(getenv("REQ_TIMEOUT_NOTIFICATIONS", default="5"))
REQ_TIMEOUT_CMS = int(getenv("REQ_TIMEOUT_CMS", default="10"))
REQ_TIMEOUT_GHCR = int(getenv("REQ_TIMEOUT_GHCR", default="10"))

REQUESTS_TIMEOUT = parse_timespan(getenv("REQUESTS_TIMEOUT_DURATION", default="30s"))


POSTGRES_URI = getenv("POSTGRES_URI", mandatory=True)

WORKER_OFFLINE_DELAY_DURATION = parse_timespan(
    getenv("WORKER_OFFLINE_DELAY_DURATION", default="20m")
)

ALEMBIC_UPGRADE_HEAD_ON_START = parse_bool(
    getenv("ALEMBIC_UPGRADE_HEAD_ON_START", default="false")
)

BLOB_STORAGE_URL = getenv("BLOB_STORAGE_URL")
BLOB_STORAGE_USERNAME = getenv("BLOB_STORAGE_USERNAME")
BLOB_STORAGE_PASSWORD = getenv("BLOB_STORAGE_PASSWORD")
BLOB_MAX_SIZE = parse_size(getenv("BLOB_MAX_SIZE", default="1MB"), binary=True)
