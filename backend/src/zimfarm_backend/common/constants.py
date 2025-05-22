import datetime
import os

from zimfarm_backend.common.enum import SchedulePeriodicity

OPENSSL_BIN = os.getenv("OPENSSL_BIN", "/usr/bin/openssl")
MESSAGE_VALIDITY = 60  # number of seconds before a message expire

REFRESH_TOKEN_EXPIRY = 180  # days
TOKEN_EXPIRY = 24  # hours

ENABLED_SCHEDULER = not os.getenv("DISABLE_SCHEDULER", "")
DEFAULT_SCHEDULE_DURATION = datetime.timedelta(days=31).total_seconds()

PERIODICITIES = {
    SchedulePeriodicity.monthly: {"days": 31},
    SchedulePeriodicity.quarterly: {"days": 90},
    SchedulePeriodicity.biannualy: {"days": 180},
    SchedulePeriodicity.annually: {"days": 365},
}

ZIM_UPLOAD_URI = os.getenv(
    "ZIM_UPLOAD_URI", "sftp://uploader@warehouse.farm.openzim.org:1522/zim"
)
try:
    # ZIM files expiration, 0 to disable expiration
    # only working in Wasabi S3 for now, works only if retention compliance is activated
    # on the bucket and the bucket retention is smaller than value below
    ZIM_EXPIRATION = int(os.getenv("ZIM_EXPIRATION", "0"))
except Exception:
    ZIM_EXPIRATION = 0  # pyright: ignore[reportConstantRedefinition]
LOGS_UPLOAD_URI = os.getenv(
    "LOGS_UPLOAD_URI", "sftp://uploader@warehouse.farm.openzim.org:1522/logs"
)
try:
    # log files expiration, 0 to disable expiration
    # only working in Wasabi S3 for now, works only if retention compliance is activated
    # on the bucket and the bucket retention is smaller than value below
    LOGS_EXPIRATION = int(os.getenv("LOGS_EXPIRATION", "30"))
except Exception:
    LOGS_EXPIRATION = 30  # pyright: ignore[reportConstantRedefinition]
ARTIFACTS_UPLOAD_URI = os.getenv("ARTIFACTS_UPLOAD_URI", None)
try:
    # artifact files expiration, 0 to disable expiration
    # only working in Wasabi S3 for now, works only if retention compliance is activated
    # on the bucket and the bucket retention is smaller than value below
    ARTIFACTS_EXPIRATION = int(os.getenv("ARTIFACTS_EXPIRATION", "30"))
except Exception:
    ARTIFACTS_EXPIRATION = 30  # pyright: ignore[reportConstantRedefinition]

# empty ZIMCHECK_OPTION means no zimcheck
ZIMCHECK_OPTION = os.getenv("ZIMCHECK_OPTION", "")

# Publisher value to "force" in all scrapers if not set in the recipe
DEFAULT_PUBLISHER = os.getenv("DEFAULT_PUBLISHER")

# NOTIFICATIONS

# in-notification URLs
PUBLIC_URL = os.getenv("PUBLIC_URL", "https://farm.openzim.org")
ZIM_DOWNLOAD_URL = os.getenv(
    "ZIM_DOWNLOAD_URL", "https://mirror.download.kiwix.org/zim"
)

# mailgun
MAILGUN_FROM = os.getenv("MAILGUN_FROM", "zimfarm@localhost")
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY", "")
MAILGUN_API_URL = os.getenv("MAILGUN_API_URL", "")

# slack
SLACK_URL = os.getenv("SLACK_URL", "")
# no defauts for branding so it falls back to what's configured in slack
SLACK_USERNAME = os.getenv("SLACK_USERNAME")
SLACK_EMOJI = os.getenv("SLACK_EMOJI")
SLACK_ICON = os.getenv("SLACK_ICON")

# string to replace hidden secrets with
SECRET_REPLACEMENT = "--------"  # nosec

# ###
# workers whitelist management
# ###
# using the following, it is possible to automate
# the update of a whitelist of workers IPs on Wasabi (S3 provider)
# enable this feature (default is off)
USES_WORKERS_IPS_WHITELIST = bool(os.getenv("USES_WORKERS_IPS_WHITELIST"))
MAX_WORKER_IP_CHANGES_PER_DAY = 4
# wasabi URL with credentials to update policy
WASABI_URL = os.getenv("WASABI_URL", "")
# policy ARN such as arn:aws:iam::xxxxxxxxxxxx:policy/yyyyyyyy
WASABI_WHITELIST_POLICY_ARN = os.getenv("WASABI_WHITELIST_POLICY_ARN", "")
# ID of the statement to set on the policy for the whitelist
WASABI_WHITELIST_STATEMENT_ID = os.getenv(
    "WASABI_WHITELIST_STATEMENT_ID", "ZimfarmWorkersIPsWhiteList"
)
# list of IPs and networks to always allow (regardless of used by workers or not)
WHITELISTED_IPS = [
    ip.strip() for ip in os.getenv("WHITELISTED_IPS", "").split(",") if ip.strip()
]


# openZIM CMS can be called upon receival of each ZIM
INFORM_CMS = bool(os.getenv("INFORM_CMS"))
CMS_ENDPOINT = os.getenv("CMS_ENDPOINT", "https://api.cms.openzim.org/v1/books/add")
# URL to tell the CMS where to download ZIM from
CMS_ZIM_DOWNLOAD_URL = os.getenv(
    "CMS_ZIM_DOWNLOAD_URL", "https://download.kiwix.org/zim"
)

# [DEBUG] prevent scraper containers from running wit extended capabilities
DISALLOW_CAPABILITIES = bool(os.getenv("ZIMFARM_DISALLOW_CAPABILITIES"))

# Timeout for requests to other services
REQ_TIMEOUT_NOTIFICATIONS = int(os.getenv("REQ_TIMEOUT_NOTIFICATIONS", "5"))
REQ_TIMEOUT_CMS = int(os.getenv("REQ_TIMEOUT_CMS", "10"))
REQ_TIMEOUT_GHCR = int(os.getenv("REQ_TIMEOUT_GHCR", "10"))

# OFFLINERS
ZIMIT_USE_RELAXED_SCHEMA = bool(os.getenv("ZIMIT_USE_RELAXED_SCHEMA"))
NAUTILUS_USE_RELAXED_SCHEMA = bool(os.getenv("NAUTILUS_USE_RELAXED_SCHEMA"))
