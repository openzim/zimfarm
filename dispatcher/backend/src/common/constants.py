import os
import datetime

from common.enum import SchedulePeriodicity

OPENSSL_BIN = os.getenv("OPENSSL_BIN", "/usr/bin/openssl")
MESSAGE_VALIDITY = 60  # number of seconds before a message expire

REFRESH_TOKEN_EXPIRY = 180  # days
TOKEN_EXPIRY = 24  # hours

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
    ZIM_EXPIRATION = int(os.getenv("ZIM_EXPIRATION", "0"))
except Exception:
    ZIM_EXPIRATION = 0
LOGS_UPLOAD_URI = os.getenv(
    "LOGS_UPLOAD_URI", "sftp://uploader@warehouse.farm.openzim.org:1522/logs"
)
try:
    LOGS_EXPIRATION = int(os.getenv("LOGS_EXPIRATION", "30"))
except Exception:
    LOGS_EXPIRATION = 30

# empty ZIMCHECK_OPTION means no zimcheck
ZIMCHECK_OPTION = os.getenv("ZIMCHECK_OPTION", "")

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
SECRET_REPLACEMENT = "********"  # noqa
