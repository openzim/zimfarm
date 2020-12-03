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
    "ZIM_UPLOAD_URI", "sftp://uploader@warehouse.farm.openzim.org:1522"
)
try:
    ZIM_EXPIRATION = int(os.getenv("ZIM_EXPIRATION", "0"))
except Exception:
    ZIM_EXPIRATION = 0
LOGS_UPLOAD_URI = os.getenv(
    "LOGS_UPLOAD_URI", "sftp://uploader@warehouse.farm.openzim.org:1522"
)
try:
    LOGS_EXPIRATION = int(os.getenv("LOGS_EXPIRATION", "30"))
except Exception:
    LOGS_EXPIRATION = 30
