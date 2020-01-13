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
